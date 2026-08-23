"""
entities/powerup.py - Dropped power-ups and items (Shoes, Candies, Shield, Bonus Fruits).
"""
import pygame
import math
import random
from constants import (
    POWERUP_SHOES, POWERUP_BLUE_CANDY, POWERUP_YELLOW_CANDY,
    POWERUP_PURPLE_CANDY, POWERUP_SHIELD, POWERUP_FRUIT,
    GRAVITY, MAX_FALL_SPEED, TILE_SIZE
)

POWERUP_TYPES = [
    POWERUP_SHOES,
    POWERUP_BLUE_CANDY,
    POWERUP_YELLOW_CANDY,
    POWERUP_PURPLE_CANDY,
    POWERUP_SHIELD,
    POWERUP_FRUIT
]

class PowerUp:
    """A floating or falling collectible power-up."""
    def __init__(self, x, y, item_type=None):
        self.x = float(x)
        self.y = float(y)
        self.item_type = item_type or random.choice(POWERUP_TYPES)
        self.rect = pygame.Rect(int(self.x - 8), int(self.y - 8), 16, 16)

        self.vy = -60.0  # gentle pop upwards on spawn
        self.on_ground = False
        self.age = 0.0
        self.lifespan = 18.0  # disappears after 18 seconds if uncollected
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
            self.rect.y = int(self.y - 8)

            # Platform landing
            for plat in platforms:
                if plat.check_player_landing(prev_bottom, self.rect, self.vy):
                    self.y = plat.rect.top - 8
                    self.rect.y = int(self.y - 8)
                    self.vy = 0.0
                    self.on_ground = True
                    break
        else:
            # Gentle ground hover bob
            bob = math.sin(self.age * 4.0 + self.bob_phase) * 2.0
            self.rect.y = int(self.y - 8 + bob)

        self.rect.x = int(self.x - 8)
        return self.is_alive

    def apply_to_player(self, player):
        """Applies the buff/effect to the collecting player."""
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
            player.giant_buff_timer = 12.0
            return ("GIANT BUBBLE!", 300)
        elif self.item_type == POWERUP_SHIELD:
            player.invulnerable_timer = 6.0
            return ("STAR SHIELD!", 300)
        elif self.item_type == POWERUP_FRUIT:
            return ("BONUS +800!", 800)
        return ("ITEM!", 100)

    def draw(self, surface, sprite_manager):
        img = sprite_manager.powerups.get(self.item_type, sprite_manager.powerups.get("fruit"))
        if img:
            # Flash if about to despawn
            if self.age >= (self.lifespan - 4.0) and int(self.age * 8) % 2 == 0:
                return
            surface.blit(img, self.rect)
