"""
tools/slice_and_inspect.py - Locates and slices all animations from the 4 sprite sheets.
"""
import os
import cv2
import numpy as np
from PIL import Image

def analyze_sheet_contours(name, is_dark_bg=False):
    path = f"Animation/BubbleBobble_{name}_Character_SpriteSheet.png"
    img = Image.open(path).convert("RGBA")
    arr = np.array(img)
    h, w, _ = arr.shape
    rgb = arr[:, :, :3]
    
    if is_dark_bg:
        bg_thresh = np.all(rgb <= 24, axis=-1).astype(np.uint8) * 255
    else:
        bg_thresh = np.all(rgb >= 210, axis=-1).astype(np.uint8) * 255
        
    # Flood-fill background from corners
    filled_bg = bg_thresh.copy()
    mask = np.zeros((h + 2, w + 2), np.uint8)
    for sx, sy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1)]:
        if filled_bg[sy, sx] == 255:
            cv2.floodFill(filled_bg, mask, (sx, sy), 128)
            
    sprite_mask = (filled_bg != 128).astype(np.uint8) * 255
    
    # Ignore top text (y < 45) and bottom text (y > 930)
    sprite_mask[:45, :] = 0
    sprite_mask[930:, :] = 0
    
    # Find all connected components / bounding boxes
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(sprite_mask)
    
    components = []
    for i in range(1, num_labels):
        x, y, cw, ch, area = stats[i]
        # Filter out tiny text specks (keep characters / bubbles / particles)
        if area > 100 and ch > 20 and cw > 20:
            components.append((y, x, cw, ch, area))
            
    # Sort primarily by y (row) then x (col)
    components.sort(key=lambda c: (c[0] // 160, c[1]))
    print(f"=== {name} Sheet: Found {len(components)} sprite components ===")
    for idx, (y, x, cw, ch, area) in enumerate(components):
        print(f"  #{idx:02d}: x={x:4d}, y={y:4d}, w={cw:3d}, h={ch:3d}, area={area:5d}")
        
    return components

if __name__ == "__main__":
    analyze_sheet_contours("Green", is_dark_bg=False)
