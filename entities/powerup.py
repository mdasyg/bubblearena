"""
entities/powerup.py - Dropped power-ups and collectible bonus items (Candies, Shoes, Gems, Fruits).
"""
import pygame
import math
import random
from constants import (
    POWERUP_SHOES, POWERUP_BLUE_CANDY, POWERUP_YELLOW_CANDY,
    POWERUP_PURPLE_CANDY, POWERUP_SHIELD, POWERUP_DIAMOND,
    POWERUP_RUBY, POWERUP_APPLE, POWERUP_CARROT, POWERUP_WATERMELON,
    POWERUP_GRAPES, POWERUP_GOLDEN_BELL, POWERUP_BANANA, POWERUP_FRUIT,
    GIANT_CANDY_DURATION, GRAVITY, MAX_FALL_SPEED, TILE_SIZE,
    VIRTUAL_WIDTH, VIRTUAL_HEIGHT
)

POWERUP_TYPES = [
    # Utilities & Candies
    POWERUP_SHOES,
    POWERUP_BLUE_CANDY,
    POWERUP_YELLOW_CANDY,
    POWERUP_PURPLE_CANDY,
    POWERUP_SHIELD,
    # Collectible Bonus Items
    POWERUP_DIAMOND,
    POWERUP_RUBY,
    POWERUP_GOLDEN_BELL,
    POWERUP_WATERMELON,
    POWERUP_BANANA,
    POWERUP_GRAPES,
    POWERUP_APPLE,
    POWERUP_CARROT
]

# Weighted spawn chances for powerup drops
POWERUP_WEIGHTS = [
    # Utilities
    10,  # Shoes
    10,  # Blue Candy
    10,  # Yellow Candy
    12,  # Purple Giant Candy (30s 2x size!)
    8,   # Shield
    # High-value Gems & Bell
    5,   # Diamond (+2500)
    8,   # Ruby (+1500)
    6,   # Golden Bell (+2000)
    # Fruits & Vegetables
    12,  # Watermelon (+800)
    14,  # Banana (+700)
    14,  # Grapes (+600)
    16,  # Apple (+500)
    18   # Carrot (+400)
]

class PowerUp:
    """A floating or falling collectible power-up or fruit item."""
    def __init__(self, x, y, item_type=None):
        self.x = max(24.0, min(float(VIRTUAL_WIDTH - 24), float(x)))
        self.y = max(36.0, min(float(VIRTUAL_HEIGHT - 24), float(y)))
        self.item_type = item_type or random.choices(POWERUP_TYPES, weights=POWERUP_WEIGHTS, k=1)[0]
        self.rect = pygame.Rect(int(self.x - 8), int(self.y - 8), 16, 16)

        self.vy = -30.0  # gentle upward pop on spawn
        self.on_ground = False
        self.age = 0.0
        self.lifespan = 20.0  # disappears after 20s if uncollected
        self.is_alive = True
        self.bob_phase = random.uniform(0, 2 * math.pi)

    def update(self, dt, platforms):
        self.age += dt
        if self.age >= self.lifespan:
            self.is_alive = False
            return False

        if not self.on_ground:
            self.vy = min(MAX_FALL_SPEED * 0.5, self.vy + GRAVITY * 0.5 * dt)
            prev_bottom = self.rect.bottom
            self.y += self.vy * dt
            
            # Ceiling boundary clamp (keep well below HUD at y=36)
            if self.y < 36.0:
                self.y = 36.0
                self.vy = max(0.0, self.vy)
                
            self.rect.y = int(self.y - 8)

            # Platform landing
            for plat in platforms:
                if plat.check_player_landing(prev_bottom, self.rect, self.vy):
                    self.y = plat.rect.top - 8
                    self.rect.y = int(self.y - 8)
                    self.vy = 0.0
                    self.on_ground = True
                    break

            # Arena floor landing (row 19 at y = VIRTUAL_HEIGHT - 16)
            if self.y >= VIRTUAL_HEIGHT - 24.0:
                self.y = VIRTUAL_HEIGHT - 24.0
                self.rect.y = int(self.y - 8)
                self.vy = 0.0
                self.on_ground = True
        else:
            # Gentle ground hover bob
            bob = math.sin(self.age * 4.0 + self.bob_phase) * 2.0
            self.rect.y = int(self.y - 8 + bob)

        self.rect.x = int(self.x - 8)
        return self.is_alive

    def apply_to_player(self, player):
        """Applies the buff/effect or score bonus to the collecting player."""
        if self.item_type == POWERUP_SHOES:
            player.speed_buff_timer = 12.0
            return ("SPEED UP!", 200)
        elif self.item_type == POWERUP_BLUE_CANDY:
            player.range_buff_timer = 15.0
            return ("LONG RANGE!", 250)
        elif self.item_type == POWERUP_YELLOW_CANDY:
            player.rapid_buff_timer = 15.0
            return ("RAPID BUBBLE!", 250)
        elif self.item_type == POWERUP_PURPLE_CANDY:
            player.giant_buff_timer = GIANT_CANDY_DURATION  # 30.0 seconds!
            return ("MEGA BUBBLE (30s)!", 300)
        elif self.item_type == POWERUP_SHIELD:
            player.invulnerable_timer = 6.0
            return ("STAR SHIELD!", 300)
        elif self.item_type == POWERUP_DIAMOND:
            return ("DIAMOND +2500!", 2500)
        elif self.item_type == POWERUP_RUBY:
            return ("RUBY GEM +1500!", 1500)
        elif self.item_type == POWERUP_GOLDEN_BELL:
            return ("GOLDEN BELL +2000!", 2000)
        elif self.item_type == POWERUP_WATERMELON:
            return ("WATERMELON +800!", 800)
        elif self.item_type == POWERUP_BANANA:
            return ("BANANA +700!", 700)
        elif self.item_type == POWERUP_GRAPES:
            return ("GRAPES +600!", 600)
        elif self.item_type == POWERUP_APPLE:
            return ("APPLE +500!", 500)
        elif self.item_type == POWERUP_CARROT:
            return ("CARROT +400!", 400)
        elif self.item_type == POWERUP_FRUIT:
            return ("BONUS +800!", 800)
        return ("ITEM!", 100)

    def draw(self, surface, sprite_manager):
        img = sprite_manager.powerups.get(self.item_type, sprite_manager.powerups.get("apple"))
        if img:
            # Flash if about to despawn in final 4s
            if self.age >= (self.lifespan - 4.0) and int(self.age * 8) % 2 == 0:
                return
            surface.blit(img, self.rect)