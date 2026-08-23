"""
tools/inspect_layout.py - Find bounding boxes of all character sprites in the sprite sheets.
"""
import os
import cv2
import numpy as np
from PIL import Image

def analyze_sheet_layout(name):
    path = f"Animation/BubbleBobble_{name}_Character_SpriteSheet.png"
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    h, w, _ = arr.shape
    
    # 5 main vertical bands/rows:
    # Row 0: Idle, Walk Right, Walk Left (y ~ 50 to 190)
    # Row 1: Shoot Bubble Right, Shoot Bubble Left (y ~ 210 to 360)
    # Row 2: Jump, Jump Right, Jump Left (y ~ 380 to 540)
    # Row 3: Falling, Jump on Bubble, Inside Bubble (y ~ 550 to 720)
    # Row 4: Popping Bubble Escape, Being Killed, Popping Another Bubble (y ~ 730 to 920)
    
    rows = [
        ("Row 1 (Idle & Walk)", 50, 190),
        ("Row 2 (Shoot)", 210, 360),
        ("Row 3 (Jump)", 380, 540),
        ("Row 4 (Fall & Bubble Ride/Trap)", 550, 720),
        ("Row 5 (Pop & Killed)", 730, 920),
    ]
    
    print(f"=== {name} Sheet Analysis ===")
    for rname, ymin, ymax in rows:
        row_crop = arr[ymin:ymax, :, :]
        print(f"  {rname}: y=[{ymin}:{ymax}]")

if __name__ == "__main__":
    analyze_sheet_layout("Green")
