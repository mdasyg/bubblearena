"""
tools/build_player_animations.py - Extracts, cleans, and packages the 4 player sprite sheets.
"""
import os
import cv2
import numpy as np
from PIL import Image

CHAR_MAP = {
    0: ("Green", False),
    1: ("Blue", True),
    2: ("Yellow", False),
    3: ("Red", False),
}

def remove_background(img_pil, is_dark_bg=False):
    arr = np.array(img_pil.convert("RGBA"))
    h, w, _ = arr.shape
    rgb = arr[:, :, :3]
    
    if is_dark_bg:
        # Dark background in Blue sheet
        bg_thresh = np.all(rgb <= 24, axis=-1).astype(np.uint8) * 255
    else:
        # Light checkerboard in Green, Yellow, Red
        bg_thresh = np.all(rgb >= 205, axis=-1).astype(np.uint8) * 255
        
    # Flood-fill background from corners and edges
    filled_bg = bg_thresh.copy()
    mask = np.zeros((h + 2, w + 2), np.uint8)
    for sx, sy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
                   (w // 4, 0), (w // 2, 0), (3 * w // 4, 0),
                   (w // 4, h - 1), (w // 2, h - 1), (3 * w // 4, h - 1)]:
        if filled_bg[sy, sx] == 255:
            cv2.floodFill(filled_bg, mask, (sx, sy), 128)
            
    is_sprite = (filled_bg != 128)
    
    # Close any small pinholes in outer black outlines
    kernel = np.ones((3, 3), np.uint8)
    is_sprite_clean = cv2.morphologyEx(is_sprite.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
    
    # Clear text labels
    is_sprite_clean[:45, :] = 0
    is_sprite_clean[930:, :] = 0
    
    alpha = is_sprite_clean * 255
    result = arr.copy()
    result[:, :, 3] = alpha
    return result

def extract_character_poses(p_id, name, is_dark_bg):
    sheet_path = f"Animation/BubbleBobble_{name}_Character_SpriteSheet.png"
    img_pil = Image.open(sheet_path)
    clean_arr = remove_background(img_pil, is_dark_bg)
    
    # Find bounding boxes
    mask = clean_arr[:, :, 3]
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
    
    components = []
    for i in range(1, num_labels):
        x, y, cw, ch, area = stats[i]
        if area > 400 and ch >= 40 and cw >= 40:
            components.append((y, x, cw, ch, area))
            
    # Sort into rows by y position
    # Row 1: y in [50, 200]
    # Row 2: y in [210, 360]
    # Row 3: y in [380, 540]
    # Row 4: y in [550, 750]
    # Row 5: y in [760, 930]
    
    rows = {1: [], 2: [], 3: [], 4: [], 5: []}
    for comp in components:
        y, x, cw, ch, area = comp
        if 45 <= y < 200:
            rows[1].append(comp)
        elif 200 <= y < 370:
            rows[2].append(comp)
        elif 370 <= y < 550:
            rows[3].append(comp)
        elif 550 <= y < 760:
            rows[4].append(comp)
        elif 760 <= y < 930:
            rows[5].append(comp)
            
    for r in rows:
        rows[r].sort(key=lambda c: c[1])  # sort left to right by x
        
    print(f"[{name}] Rows component counts: Row 1={len(rows[1])}, Row 2={len(rows[2])}, Row 3={len(rows[3])}, Row 4={len(rows[4])}, Row 5={len(rows[5])}")
    
    # Slice and normalize frames to 24x24 pixel art
    out_base = f"assets/sprites/player_{p_id}"
    os.makedirs(out_base, exist_ok=True)
    
    anim_dict = {}
    
    # 1. IDLE (first 5 components in Row 1)
    anim_dict["idle"] = [c for c in rows[1][:5]]
    
    # 2. WALK (components 5..9 in Row 1)
    anim_dict["walk"] = [c for c in rows[1][5:10]] if len(rows[1]) >= 10 else [c for c in rows[1][5:]]
    
    # 3. SHOOT (first 5 components in Row 2)
    anim_dict["shoot"] = [c for c in rows[2][:5]]
    
    # 4. JUMP (first 5 components in Row 3)
    anim_dict["jump"] = [c for c in rows[3][:5]]
    
    # 5. FALL (first 4 components in Row 4)
    anim_dict["fall"] = [c for c in rows[4][:4]]
    
    # 6. BUBBLE RIDE (next 4 components in Row 4)
    anim_dict["bubble_ride"] = [c for c in rows[4][4:8]] if len(rows[4]) >= 8 else [c for c in rows[4][4:]]
    
    # 7. TRAPPED (last large component in Row 4)
    anim_dict["trapped"] = [rows[4][-1]] if rows[4] else []
    
    # 8. ESCAPE / RESCUE (first 3 components in Row 5)
    anim_dict["escape"] = [c for c in rows[5][:3]] if len(rows[5]) >= 3 else []
    
    # 9. BEING KILLED (components in middle of Row 5)
    # Typically 4 death frames (shock, dizzy, squished, skeleton)
    anim_dict["pop_death"] = [c for c in rows[5][3:7]] if len(rows[5]) >= 7 else [c for c in rows[5][3:]]
    
    # 10. VICTORY (last components in Row 5)
    anim_dict["victory"] = [c for c in rows[5][7:]] if len(rows[5]) >= 8 else [c for c in rows[5][-4:]]
    
    TARGET_SIZE = 24  # Standard in-game high-definition pixel size
    
    saved_anims = {}
    for state_name, comp_list in anim_dict.items():
        state_dir = f"{out_base}/{state_name}"
        os.makedirs(state_dir, exist_ok=True)
        saved_anims[state_name] = []
        
        for idx, (y, x, cw, ch, area) in enumerate(comp_list):
            crop = clean_arr[y:y+ch, x:x+cw]
            crop_pil = Image.fromarray(crop, mode="RGBA")
            
            # Scale while preserving aspect ratio, centered in TARGET_SIZE x TARGET_SIZE
            scale = min((TARGET_SIZE - 2) / cw, (TARGET_SIZE - 2) / ch)
            nw = max(1, int(cw * scale))
            nh = max(1, int(ch * scale))
            resized = crop_pil.resize((nw, nh), Image.Resampling.LANCZOS)
            
            canvas = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
            # Align to bottom-center of canvas
            ox = (TARGET_SIZE - nw) // 2
            oy = (TARGET_SIZE - nh)
            canvas.paste(resized, (ox, oy), resized)
            
            file_path = f"{state_dir}/{idx}.png"
            canvas.save(file_path)
            saved_anims[state_name].append(file_path)
            
        print(f"  Extracted {state_name}: {len(saved_anims[state_name])} frames -> {state_dir}")
        
    return saved_anims

if __name__ == "__main__":
    for p_id, (name, dark) in CHAR_MAP.items():
        print(f"\n==========================================")
        print(f"  Extracting Player {p_id} ({name}) Sprites")
        print(f"==========================================")
        extract_character_poses(p_id, name, dark)
