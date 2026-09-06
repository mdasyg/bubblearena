"""
engine/sprites.py - Procedural 8-bit Pixel Art Generator & Asset Manager for Bubble Arena.
Generates authentic retro arcade sprites for characters, animations, bubbles, tiles, and items.
"""
import os
import sys
import pygame
import math
from constants import (
    COLOR_BLACK, COLOR_WHITE, COLOR_DARK_BLUE, COLOR_NAVY, COLOR_PURPLE,
    COLOR_RED, COLOR_ORANGE, COLOR_YELLOW, COLOR_GREEN, COLOR_CYAN,
    COLOR_BLUE, COLOR_PINK, COLOR_GRAY, COLOR_DARK_GRAY, COLOR_LIME, COLOR_GOLD,
    PLAYER_COLORS, TILE_SIZE
)

class SpriteManager:
    """Generates and caches all 8-bit sprites and animation frames."""
    def __init__(self):
        self.players = {}       # {player_id: {state: [frames]}}
        self.bubbles = []       # [normal_frames]
        self.giant_bubbles = [] # [giant_frames]
        self.bubble_pop = []    # [pop_frames]
        self.tiles = {}         # {theme_id: {"solid": surf, "oneway": surf}}
        self.powerups = {}      # {type: surf}
        self.flag_frames = []   # [flag_surfs]
        self.particles = {}     # {type: [frames]}

        self._generate_all()

    def _generate_all(self):
        self._generate_player_sprites()
        self._generate_bubble_sprites()
        self._generate_tile_sprites()
        self._generate_powerup_sprites()
        self._generate_flag_sprites()
        self._generate_particle_sprites()

    def _create_surface(self, width, height):
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        return surf

    def _generate_player_sprites(self):
        """Loads sprite animations from extracted sprite sheets or builds procedural fallback."""
        import os
        import sys

        base_res_dir = getattr(sys, '_MEIPASS', os.path.abspath("."))

        # Attempt to load custom sprite sheet animations
        for p_idx in range(4):
            p_dir = os.path.join(base_res_dir, "assets", "sprites", f"player_{p_idx}")
            if not os.path.exists(p_dir):
                p_dir = os.path.join(os.path.abspath("."), "assets", "sprites", f"player_{p_idx}")

            if os.path.exists(p_dir):
                p_dict = {}
                states = ["idle", "walk", "jump", "fall", "shoot", "bubble_ride", "trapped", "escape", "pop_death", "victory"]
                for state in states:
                    s_dir = os.path.join(p_dir, state)
                    frames = []
                    if os.path.exists(s_dir):
                        files = sorted([f for f in os.listdir(s_dir) if f.endswith(".png")],
                                       key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else x)
                        for f in files:
                            try:
                                img = pygame.image.load(os.path.join(s_dir, f)).convert_alpha()
                                frames.append(img)
                            except Exception:
                                pass
                    p_dict[state] = frames
                
                # Check if we loaded valid frames
                if len(p_dict.get("idle", [])) > 0 and len(p_dict.get("walk", [])) > 0:
                    self.players[p_idx] = p_dict
                    continue

            # Procedural fallback for this player
            color_cfg = PLAYER_COLORS[p_idx]
            main_col = color_cfg["main"]
            accent_col = color_cfg["accent"]
            belly_col = color_cfg["belly"]
            eye_col = COLOR_WHITE
            pupil_col = COLOR_BLACK

            p_dict = {
                "idle": [],
                "walk": [],
                "jump": [],
                "fall": [],
                "shoot": [],
                "bubble_ride": [],
                "trapped": [],
                "escape": [],
                "pop_death": [],
                "victory": []
            }

            # --- Idle (2 frames) ---
            for f in range(2):
                surf = self._create_surface(20, 20)
                b_off = 1 if f == 1 else 0
                # Body / Head
                pygame.draw.rect(surf, main_col, (4, 4 + b_off, 12, 12), border_radius=4)
                # Belly
                pygame.draw.rect(surf, belly_col, (10, 8 + b_off, 5, 7), border_radius=2)
                # Snout
                pygame.draw.rect(surf, accent_col, (13, 7 + b_off, 4, 4))
                # Back Spikes
                pygame.draw.polygon(surf, COLOR_ORANGE, [(4, 5 + b_off), (1, 7 + b_off), (4, 9 + b_off)])
                pygame.draw.polygon(surf, COLOR_ORANGE, [(4, 10 + b_off), (1, 12 + b_off), (4, 14 + b_off)])
                # Big Retro Eye
                pygame.draw.rect(surf, eye_col, (10, 5 + b_off, 4, 4))
                pygame.draw.rect(surf, pupil_col, (12, 6 + b_off, 2, 2))
                # Feet
                pygame.draw.rect(surf, accent_col, (5, 16, 4, 3), border_radius=1)
                pygame.draw.rect(surf, accent_col, (11, 16, 4, 3), border_radius=1)
                # Cute cheek blush
                pygame.draw.rect(surf, COLOR_PINK, (11, 10 + b_off, 2, 2))
                p_dict["idle"].append(surf)

            # --- Walk (4 frames) ---
            for f in range(4):
                surf = self._create_surface(20, 20)
                bob = 1 if f in (1, 3) else 0
                pygame.draw.rect(surf, main_col, (4, 4 - bob, 12, 12), border_radius=4)
                pygame.draw.rect(surf, belly_col, (10, 8 - bob, 5, 7), border_radius=2)
                pygame.draw.rect(surf, accent_col, (13, 7 - bob, 4, 4))
                pygame.draw.polygon(surf, COLOR_ORANGE, [(4, 5 - bob), (1, 7 - bob), (4, 9 - bob)])
                pygame.draw.polygon(surf, COLOR_ORANGE, [(4, 10 - bob), (1, 12 - bob), (4, 14 - bob)])
                pygame.draw.rect(surf, eye_col, (10, 5 - bob, 4, 4))
                pygame.draw.rect(surf, pupil_col, (12, 6 - bob, 2, 2))
                # Animated feet
                if f == 0:
                    pygame.draw.rect(surf, accent_col, (3, 16, 4, 3))
                    pygame.draw.rect(surf, accent_col, (12, 15, 4, 3))
                elif f == 1:
                    pygame.draw.rect(surf, accent_col, (5, 16, 4, 3))
                    pygame.draw.rect(surf, accent_col, (11, 16, 4, 3))
                elif f == 2:
                    pygame.draw.rect(surf, accent_col, (7, 15, 4, 3))
                    pygame.draw.rect(surf, accent_col, (14, 16, 4, 3))
                else:
                    pygame.draw.rect(surf, accent_col, (5, 16, 4, 3))
                    pygame.draw.rect(surf, accent_col, (11, 16, 4, 3))
                p_dict["walk"].append(surf)

            # --- Jump (1 frame) ---
            surf = self._create_surface(20, 20)
            pygame.draw.rect(surf, main_col, (4, 3, 12, 12), border_radius=4)
            pygame.draw.rect(surf, belly_col, (10, 7, 5, 6), border_radius=2)
            pygame.draw.rect(surf, accent_col, (13, 6, 4, 4))
            pygame.draw.polygon(surf, COLOR_GOLD, [(4, 4), (0, 6), (4, 8)])
            pygame.draw.polygon(surf, COLOR_GOLD, [(4, 9), (0, 11), (4, 13)])
            pygame.draw.rect(surf, eye_col, (10, 4, 4, 4))
            pygame.draw.rect(surf, pupil_col, (12, 4, 2, 2)) # looking up
            # Tucked legs
            pygame.draw.rect(surf, accent_col, (4, 14, 4, 4), border_radius=2)
            pygame.draw.rect(surf, accent_col, (12, 14, 4, 4), border_radius=2)
            p_dict["jump"].append(surf)

            # --- Fall (1 frame) ---
            surf = self._create_surface(20, 20)
            pygame.draw.rect(surf, main_col, (4, 5, 12, 12), border_radius=4)
            pygame.draw.rect(surf, belly_col, (10, 9, 5, 6), border_radius=2)
            pygame.draw.rect(surf, accent_col, (13, 8, 4, 4))
            pygame.draw.rect(surf, eye_col, (10, 6, 4, 4))
            pygame.draw.rect(surf, pupil_col, (12, 8, 2, 2)) # looking down
            # Extended legs
            pygame.draw.rect(surf, accent_col, (4, 17, 3, 3))
            pygame.draw.rect(surf, accent_col, (13, 17, 3, 3))
            p_dict["fall"].append(surf)

            # --- Shoot (2 frames) ---
            for f in range(2):
                surf = self._create_surface(22, 20)
                pygame.draw.rect(surf, main_col, (3, 4, 12, 12), border_radius=4)
                pygame.draw.rect(surf, belly_col, (8, 8, 5, 7), border_radius=2)
                # Puffed-out mouth
                mouth_w = 6 if f == 0 else 7
                pygame.draw.rect(surf, accent_col, (13, 7, mouth_w, 6), border_radius=2)
                pygame.draw.rect(surf, COLOR_DARK_BLUE, (15, 9, 3, 3)) # open mouth cavity
                pygame.draw.rect(surf, eye_col, (9, 4, 4, 4))
                pygame.draw.rect(surf, pupil_col, (11, 5, 2, 2))
                pygame.draw.rect(surf, accent_col, (4, 16, 4, 3))
                pygame.draw.rect(surf, accent_col, (10, 16, 4, 3))
                p_dict["shoot"].append(surf)

            # --- Trapped inside bubble (4 wobble frames) ---
            for f in range(4):
                surf = self._create_surface(26, 26)
                # Outer translucent bubble
                bubble_surf = pygame.Surface((26, 26), pygame.SRCALPHA)
                pygame.draw.circle(bubble_surf, (80, 200, 255, 120), (13, 13), 12)
                pygame.draw.circle(bubble_surf, (220, 250, 255, 220), (13, 13), 12, width=2)
                # Highlight glint
                pygame.draw.circle(bubble_surf, (255, 255, 255, 240), (8, 8), 3)

                # Trapped squished dragon inside
                wobble_x = int(math.sin(f * math.pi / 2) * 2)
                wobble_y = int(math.cos(f * math.pi / 2) * 2)
                d_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.rect(d_surf, main_col, (2, 2, 12, 12), border_radius=4)
                # Dizzy spiraling eyes
                if f % 2 == 0:
                    pygame.draw.line(d_surf, COLOR_WHITE, (6, 5), (10, 9), 2)
                    pygame.draw.line(d_surf, COLOR_WHITE, (6, 9), (10, 5), 2)
                else:
                    pygame.draw.circle(d_surf, COLOR_YELLOW, (8, 7), 3)
                    pygame.draw.circle(d_surf, COLOR_RED, (8, 7), 1)

                bubble_surf.blit(d_surf, (5 + wobble_x, 5 + wobble_y))
                surf.blit(bubble_surf, (0, 0))
                p_dict["trapped"].append(surf)

            # --- Pop / Death (4 frames) ---
            for f in range(4):
                surf = self._create_surface(28, 28)
                radius = 4 + f * 5
                # Expanding burst rings and stars
                pygame.draw.circle(surf, COLOR_WHITE, (14, 14), radius, width=2)
                star_angles = [0, 45, 90, 135, 180, 225, 270, 315]
                for ang in star_angles:
                    rad = math.radians(ang)
                    sx = int(14 + math.cos(rad) * (radius + 2))
                    sy = int(14 + math.sin(rad) * (radius + 2))
                    if 0 <= sx < 28 and 0 <= sy < 28:
                        pygame.draw.circle(surf, COLOR_GOLD, (sx, sy), 2)
                p_dict["pop_death"].append(surf)

            # --- Victory (2 frames) ---
            for f in range(2):
                surf = self._create_surface(20, 22)
                v_bob = 2 if f == 1 else 0
                pygame.draw.rect(surf, main_col, (4, 4 - v_bob, 12, 12), border_radius=4)
                pygame.draw.rect(surf, belly_col, (7, 8 - v_bob, 6, 7), border_radius=2)
                # Raised arms
                pygame.draw.rect(surf, accent_col, (1, 2 - v_bob, 3, 5), border_radius=1)
                pygame.draw.rect(surf, accent_col, (16, 2 - v_bob, 3, 5), border_radius=1)
                # Cheerful wink eyes
                pygame.draw.arc(surf, COLOR_WHITE, (6, 5 - v_bob, 4, 4), 0, math.pi, 2)
                pygame.draw.arc(surf, COLOR_WHITE, (12, 5 - v_bob, 4, 4), 0, math.pi, 2)
                pygame.draw.rect(surf, accent_col, (5, 16, 4, 3))
                pygame.draw.rect(surf, accent_col, (11, 16, 4, 3))
                p_dict["victory"].append(surf)

            self.players[p_idx] = p_dict

    def _generate_bubble_sprites(self):
        """Generates 4 animation frames for standard floating bubbles and giant bubbles."""
        # Standard Bubbles (24x24)
        for f in range(4):
            surf = self._create_surface(24, 24)
            # Subtle pulsation radius
            r = 10 + (1 if f in (1, 3) else 0)
            center = (12, 12)
            # Semi-transparent aqua/cyan body
            pygame.draw.circle(surf, (70, 210, 255, 100), center, r)
            # Crisp outer rim
            rim_color = (200, 245, 255, 220) if f % 2 == 0 else (140, 225, 255, 200)
            pygame.draw.circle(surf, rim_color, center, r, width=2)
            # Internal bubble reflection
            pygame.draw.circle(surf, (255, 255, 255, 240), (center[0] - 4, center[1] - 4), 3)
            pygame.draw.circle(surf, (255, 255, 255, 180), (center[0] + 4, center[1] + 4), 1)
            self.bubbles.append(surf)

        # Giant Bubbles (36x36)
        # Giant Bubbles - 2x Size (48x48, radius 22)
        for f in range(4):
            surf = self._create_surface(48, 48)
            r = 21 + (1 if f in (1, 3) else 0)
            center = (24, 24)
            # Translucent purple-magenta glow
            pygame.draw.circle(surf, (210, 80, 255, 110), center, r)
            pygame.draw.circle(surf, (250, 210, 255, 240), center, r, width=2)
            # Big highlight glints
            pygame.draw.circle(surf, (255, 255, 255, 255), (center[0] - 8, center[1] - 8), 5)
            pygame.draw.circle(surf, (255, 255, 255, 200), (center[0] + 8, center[1] + 8), 2)
            pygame.draw.circle(surf, (255, 255, 255, 180), (center[0] - 4, center[1] - 12), 2)
            self.giant_bubbles.append(surf)

        # Bubble Popping sequence (4 frames)
        for f in range(4):
            surf = self._create_surface(24, 24)
            r = 6 + f * 4
            num_droplets = 6
            for d in range(num_droplets):
                ang = (d * (360 / num_droplets)) + (f * 15)
                rad = math.radians(ang)
                dx = int(12 + math.cos(rad) * r)
                dy = int(12 + math.sin(rad) * r)
                if 0 <= dx < 24 and 0 <= dy < 24:
                    drop_r = max(1, 3 - f)
                    pygame.draw.circle(surf, (160, 235, 255, 220), (dx, dy), drop_r)
            self.bubble_pop.append(surf)

    def _generate_tile_sprites(self):
        """Generates tiles for 14 distinct level themes with solid and one-way platform variants."""
        themes = [
            # 1. Meadow
            {"name": "meadow", "base": (68, 140, 48), "sec": (108, 180, 68), "hi": (164, 236, 76), "dark": (36, 80, 24)},
            # 2. Blue Castle
            {"name": "castle", "base": (48, 80, 144), "sec": (68, 112, 184), "hi": (120, 172, 240), "dark": (24, 40, 80)},
            # 3. Neon Cyber
            {"name": "neon", "base": (28, 24, 48), "sec": (160, 40, 180), "hi": (68, 220, 240), "dark": (14, 12, 28)},
            # 4. Dungeon Vault
            {"name": "dungeon", "base": (84, 80, 96), "sec": (120, 116, 136), "hi": (160, 156, 176), "dark": (44, 40, 52)},
            # 5. Sky Spire
            {"name": "sky", "base": (210, 224, 244), "sec": (160, 184, 220), "hi": (255, 255, 255), "dark": (110, 136, 180)},
            # 6. Crystal Cavern
            {"name": "crystal", "base": (120, 44, 140), "sec": (168, 76, 188), "hi": (224, 140, 248), "dark": (64, 20, 80)},
            # 7. Double Helix
            {"name": "helix", "base": (36, 120, 128), "sec": (56, 168, 176), "hi": (112, 232, 240), "dark": (18, 64, 70)},
            # 8. Lava Forge
            {"name": "lava", "base": (64, 32, 32), "sec": (180, 60, 36), "hi": (244, 140, 40), "dark": (36, 16, 16)},
            # 9. Candy Land
            {"name": "candy", "base": (220, 80, 130), "sec": (248, 140, 180), "hi": (255, 220, 235), "dark": (140, 40, 80)},
            # 10. Golden Temple
            {"name": "gold", "base": (180, 130, 24), "sec": (224, 170, 40), "hi": (255, 235, 120), "dark": (100, 70, 12)},
            # 11. Coral Reef
            {"name": "coral", "base": (24, 128, 140), "sec": (48, 180, 196), "hi": (248, 140, 170), "dark": (12, 64, 72)},
            # 12. Haunted Manor
            {"name": "manor", "base": (40, 32, 60), "sec": (76, 60, 110), "hi": (180, 150, 240), "dark": (20, 16, 32)},
            # 13. Starry Cosmos
            {"name": "cosmos", "base": (20, 24, 52), "sec": (140, 50, 160), "hi": (100, 240, 255), "dark": (10, 12, 28)},
            # 14. Mushroom Grove
            {"name": "mushroom", "base": (80, 96, 48), "sec": (220, 90, 40), "hi": (255, 240, 200), "dark": (40, 50, 24)},
        ]

        for idx, t in enumerate(themes):
            # 1. Solid Block (16x16)
            solid_surf = self._create_surface(TILE_SIZE, TILE_SIZE)
            solid_surf.fill(t["base"])
            # Brick pattern lines
            pygame.draw.line(solid_surf, t["hi"], (0, 0), (15, 0), 1)
            pygame.draw.line(solid_surf, t["hi"], (0, 0), (0, 15), 1)
            pygame.draw.line(solid_surf, t["dark"], (0, 15), (15, 15), 1)
            pygame.draw.line(solid_surf, t["dark"], (15, 0), (15, 15), 1)
            # Inner texture brick split
            pygame.draw.line(solid_surf, t["dark"], (0, 8), (15, 8), 1)
            pygame.draw.line(solid_surf, t["sec"], (8, 0), (8, 7), 1)
            pygame.draw.line(solid_surf, t["sec"], (4, 8), (4, 15), 1)
            pygame.draw.line(solid_surf, t["sec"], (12, 8), (12, 15), 1)

            # 2. One-Way Pass-Through Platform (16x16 - solid top shelf with pass-through open bottom)
            oneway_surf = self._create_surface(TILE_SIZE, TILE_SIZE)
            # Top solid lip
            pygame.draw.rect(oneway_surf, t["hi"], (0, 0, 16, 3))
            pygame.draw.rect(oneway_surf, t["sec"], (0, 3, 16, 3))
            # Decorative brackets / dashed supports
            pygame.draw.rect(oneway_surf, t["dark"], (2, 6, 3, 5))
            pygame.draw.rect(oneway_surf, t["dark"], (11, 6, 3, 5))

            self.tiles[idx] = {
                "solid": solid_surf,
                "oneway": oneway_surf,
                "name": t["name"]
            }

    def _generate_powerup_sprites(self):
        """Generates power-ups and all 8 collectible bonus fruit/gem items."""
        # 1. Fast Shoes (Red Sneakers)
        surf = self._create_surface(16, 16)
        pygame.draw.rect(surf, COLOR_RED, (2, 6, 10, 5), border_radius=2)
        pygame.draw.polygon(surf, COLOR_RED, [(8, 6), (14, 11), (2, 11)])
        pygame.draw.rect(surf, COLOR_WHITE, (2, 11, 12, 3), border_radius=1)
        pygame.draw.line(surf, COLOR_YELLOW, (5, 8), (9, 8), 1)
        self.powerups["shoes"] = surf

        # 2. Blue Candy (Long Range)
        surf = self._create_surface(16, 16)
        pygame.draw.polygon(surf, COLOR_CYAN, [(1, 4), (5, 8), (1, 12)])
        pygame.draw.polygon(surf, COLOR_CYAN, [(15, 4), (11, 8), (15, 12)])
        pygame.draw.circle(surf, COLOR_BLUE, (8, 8), 5)
        pygame.draw.circle(surf, COLOR_WHITE, (6, 6), 2)
        self.powerups["candy_blue"] = surf

        # 3. Yellow Candy (Rapid Fire)
        surf = self._create_surface(16, 16)
        pygame.draw.polygon(surf, COLOR_GOLD, [(1, 4), (5, 8), (1, 12)])
        pygame.draw.polygon(surf, COLOR_GOLD, [(15, 4), (11, 8), (15, 12)])
        pygame.draw.circle(surf, COLOR_YELLOW, (8, 8), 5)
        pygame.draw.circle(surf, COLOR_ORANGE, (8, 8), 2)
        self.powerups["candy_yellow"] = surf

        # 4. Purple Candy (Mega 2x Giant Bubble - 30s)
        surf = self._create_surface(16, 16)
        pygame.draw.polygon(surf, COLOR_PINK, [(1, 3), (5, 8), (1, 13)])
        pygame.draw.polygon(surf, COLOR_PINK, [(15, 3), (11, 8), (15, 13)])
        pygame.draw.circle(surf, COLOR_PURPLE, (8, 8), 6)
        pygame.draw.circle(surf, (255, 180, 255), (8, 8), 4)
        pygame.draw.circle(surf, COLOR_WHITE, (6, 6), 2)
        self.powerups["candy_purple"] = surf

        # 5. Star Shield (Invincibility)
        surf = self._create_surface(16, 16)
        pygame.draw.polygon(surf, COLOR_GOLD, [
            (8, 1), (10, 6), (15, 6), (11, 9), (13, 14),
            (8, 11), (3, 14), (5, 9), (1, 6), (6, 6)
        ])
        pygame.draw.circle(surf, COLOR_WHITE, (8, 7), 2)
        self.powerups["shield"] = surf

        # 6. Diamond (Sparkling Gem +2500 pts)
        surf = self._create_surface(16, 16)
        # Brilliant cut diamond polygon
        pygame.draw.polygon(surf, (180, 240, 255), [(4, 4), (12, 4), (15, 7), (8, 14), (1, 7)])
        pygame.draw.polygon(surf, (240, 250, 255), [(4, 4), (12, 4), (10, 7), (6, 7)])
        pygame.draw.line(surf, COLOR_WHITE, (8, 4), (8, 14), 1)
        pygame.draw.line(surf, COLOR_WHITE, (1, 7), (15, 7), 1)
        pygame.draw.circle(surf, COLOR_WHITE, (5, 6), 1)
        self.powerups["diamond"] = surf

        # 7. Ruby Gem (+1500 pts)
        surf = self._create_surface(16, 16)
        pygame.draw.polygon(surf, (220, 20, 60), [(4, 3), (12, 3), (15, 8), (8, 14), (1, 8)])
        pygame.draw.polygon(surf, (255, 100, 130), [(5, 4), (11, 4), (9, 7), (7, 7)])
        pygame.draw.circle(surf, COLOR_WHITE, (6, 5), 1)
        self.powerups["ruby"] = surf

        # 8. Red Apple (+500 pts)
        surf = self._create_surface(16, 16)
        pygame.draw.circle(surf, COLOR_RED, (8, 9), 5)
        pygame.draw.rect(surf, COLOR_GREEN, (8, 3, 3, 3), border_radius=1) # leaf
        pygame.draw.line(surf, (90, 50, 30), (8, 4), (8, 6), 1) # stem
        pygame.draw.circle(surf, (255, 180, 180), (6, 8), 1) # highlight
        self.powerups["apple"] = surf

        # 9. Carrot (+400 pts)
        surf = self._create_surface(16, 16)
        # Orange carrot root
        pygame.draw.polygon(surf, COLOR_ORANGE, [(5, 6), (11, 6), (9, 14), (7, 14)])
        pygame.draw.line(surf, COLOR_YELLOW, (6, 8), (10, 8), 1)
        pygame.draw.line(surf, COLOR_YELLOW, (6, 11), (9, 11), 1)
        # Green leafy carrot top
        pygame.draw.line(surf, COLOR_GREEN, (8, 6), (5, 2), 2)
        pygame.draw.line(surf, COLOR_LIME, (8, 6), (8, 1), 2)
        pygame.draw.line(surf, COLOR_GREEN, (8, 6), (11, 2), 2)
        self.powerups["carrot"] = surf

        # 10. Watermelon (+800 pts)
        surf = self._create_surface(16, 16)
        # Green rind arc
        pygame.draw.arc(surf, (40, 160, 60), (2, 2, 12, 12), math.pi, 2 * math.pi, 3)
        # Pink flesh
        pygame.draw.polygon(surf, (245, 60, 90), [(2, 8), (14, 8), (8, 14)])
        # Seeds
        pygame.draw.rect(surf, COLOR_BLACK, (6, 9, 1, 1))
        pygame.draw.rect(surf, COLOR_BLACK, (10, 9, 1, 1))
        pygame.draw.rect(surf, COLOR_BLACK, (8, 11, 1, 1))
        self.powerups["watermelon"] = surf

        # 11. Grapes (+600 pts)
        surf = self._create_surface(16, 16)
        pygame.draw.line(surf, (90, 50, 30), (8, 2), (8, 5), 2) # stem
        pygame.draw.rect(surf, COLOR_GREEN, (9, 2, 3, 2)) # leaf
        # Grape cluster
        grape_pos = [(6, 6), (10, 6), (4, 9), (8, 9), (12, 9), (6, 12), (10, 12), (8, 14)]
        for gx, gy in grape_pos:
            pygame.draw.circle(surf, (140, 40, 180), (gx, gy), 2)
            pygame.draw.circle(surf, (200, 120, 240), (gx - 1, gy - 1), 1)
        self.powerups["grapes"] = surf

        # 12. Golden Bell (+2000 pts)
        surf = self._create_surface(16, 16)
        pygame.draw.circle(surf, COLOR_GOLD, (8, 5), 3)
        pygame.draw.polygon(surf, COLOR_GOLD, [(4, 7), (12, 7), (14, 12), (2, 12)])
        pygame.draw.rect(surf, COLOR_YELLOW, (3, 12, 10, 2), border_radius=1)
        pygame.draw.circle(surf, COLOR_ORANGE, (8, 13), 2) # clapper
        pygame.draw.circle(surf, COLOR_WHITE, (6, 7), 1)
        self.powerups["golden_bell"] = surf

        # 13. Banana (+700 pts)
        surf = self._create_surface(16, 16)
        pygame.draw.arc(surf, COLOR_YELLOW, (2, 3, 12, 10), 0.2, math.pi * 0.9, 3)
        pygame.draw.rect(surf, (100, 70, 20), (3, 4, 2, 2)) # stem
        pygame.draw.rect(surf, (100, 70, 20), (12, 10, 2, 2)) # tip
        self.powerups["banana"] = surf

        # 14. Fruit Fallback (+800 pts)
        self.powerups["fruit"] = self.powerups["apple"]

    def _generate_flag_sprites(self):
        """Generates waving animated CTF flag sprites."""
        for f in range(4):
            surf = self._create_surface(18, 22)
            # Golden Pole
            pygame.draw.rect(surf, COLOR_GOLD, (2, 2, 2, 18))
            pygame.draw.circle(surf, COLOR_YELLOW, (3, 2), 2)
            # Waving Flag cloth
            wave_off = int(math.sin(f * math.pi / 2) * 2)
            points = [
                (4, 3),
                (14 + wave_off, 6),
                (4, 11)
            ]
            pygame.draw.polygon(surf, COLOR_RED, points)
            pygame.draw.circle(surf, COLOR_WHITE, (8 + wave_off // 2, 6), 2)
            self.flag_frames.append(surf)

    def _generate_particle_sprites(self):
        """Generates spark, star, and dust particle sprites."""
        # Spark star
        star_surf = self._create_surface(8, 8)
        pygame.draw.line(star_surf, COLOR_GOLD, (0, 4), (7, 4), 1)
        pygame.draw.line(star_surf, COLOR_GOLD, (4, 0), (4, 7), 1)
        pygame.draw.circle(star_surf, COLOR_WHITE, (4, 4), 1)
        self.particles["star"] = star_surf

        # Dust puff
        dust_surf = self._create_surface(6, 6)
        pygame.draw.circle(dust_surf, COLOR_GRAY, (3, 3), 2)
        self.particles["dust"] = dust_surf
