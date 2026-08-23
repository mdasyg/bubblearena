"""
tools/extract_sprites.py - Inspects the 4 sprite sheets and extracts clean, isolated RGBA frames.
"""
import os
import pygame
import numpy as np
from PIL import Image

def analyze_sheet(name):
    path = f"Animation/BubbleBobble_{name}_Character_SpriteSheet.png"
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    print(f"\n--- Analyzing {name} ({w}x{h}) ---")
    return img

if __name__ == "__main__":
    for name in ["Green", "Blue", "Yellow", "Red"]:
        analyze_sheet(name)
