"""
tools/extract_all_sprites.py - Cleanly removes background and extracts transparent sprites for each player character.
"""
import os
import cv2
import numpy as np
from PIL import Image

def process_sprite_sheet(char_name, is_dark_bg=False):
    input_path = f"Animation/BubbleBobble_{char_name}_Character_SpriteSheet.png"
    img = Image.open(input_path).convert("RGBA")
    arr = np.array(img)
    h, w, _ = arr.shape
    
    # Create output directory
    out_dir = f"assets/sprites/{char_name.lower()}"
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Flood fill background from border to isolate characters
    # Convert to grayscale for thresholding / flood fill
    rgb = arr[:, :, :3]
    
    if is_dark_bg:
        # Blue sheet: dark background (< 20)
        bg_mask = np.all(rgb <= 22, axis=-1).astype(np.uint8) * 255
    else:
        # Green/Yellow/Red: light checkerboard (> 210)
        bg_mask = np.all(rgb >= 210, axis=-1).astype(np.uint8) * 255
    
    # Flood-fill from borders (0, 0), (w-1, 0), (0, h-1), (w-1, h-1)
    mask_for_flood = np.zeros((h + 2, w + 2), np.uint8)
    filled_bg = bg_mask.copy()
    
    for seed_x, seed_y in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1)]:
        if filled_bg[seed_y, seed_x] == 255:
            cv2.floodFill(filled_bg, mask_for_flood, (seed_x, seed_y), 128)
            
    # Characters are where filled_bg != 128
    is_sprite = (filled_bg != 128)
    
    # Refine sprite mask: morphological close to seal any outline pinholes
    kernel = np.ones((3, 3), np.uint8)
    is_sprite_clean = cv2.morphologyEx(is_sprite.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
    
    # Also exclude text labels (top 45px and bottom 100px text)
    is_sprite_clean[:45, :] = 0
    is_sprite_clean[930:, :] = 0
    
    # Apply alpha mask
    alpha_img = arr.copy()
    alpha_img[:, :, 3] = is_sprite_clean * 255
    
    # Save full transparent sheet
    transparent_full = Image.fromarray(alpha_img)
    transparent_full.save(f"{out_dir}/sheet_transparent.png")
    print(f"[{char_name}] Saved transparent sheet: {out_dir}/sheet_transparent.png")
    
    return alpha_img

if __name__ == "__main__":
    os.makedirs("assets/sprites", exist_ok=True)
    process_sprite_sheet("Green", is_dark_bg=False)
    process_sprite_sheet("Blue", is_dark_bg=True)
    process_sprite_sheet("Yellow", is_dark_bg=False)
    process_sprite_sheet("Red", is_dark_bg=False)
