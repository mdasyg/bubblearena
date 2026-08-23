"""
entities/platform.py - Solid blocks and one-way pass-through platforms for Bubble Arena.
"""
import pygame
from constants import TILE_SIZE

class Platform:
    """Represents a tile in the arena grid."""
    def __init__(self, x, y, width=TILE_SIZE, height=TILE_SIZE, is_oneway=True, theme_id=0):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_oneway = is_oneway  # True = jump-through from bottom, solid from top
        self.theme_id = theme_id

    def check_player_landing(self, prev_bottom, player_rect, player_vy):
        """
        One-way collision resolution:
        Returns True if player was above the platform top in the previous frame
        and is now intersecting it while falling downwards (vy >= 0).
        """
        if self.is_oneway:
            if player_vy >= 0 and prev_bottom <= self.rect.top + 6 and player_rect.bottom >= self.rect.top:
                if player_rect.right > self.rect.left + 2 and player_rect.left < self.rect.right - 2:
                    return True
            return False
        else:
            # Solid block: full 4-direction collision
            return self.rect.colliderect(player_rect)

    def draw(self, surface, sprite_manager):
        tile_data = sprite_manager.tiles.get(self.theme_id, sprite_manager.tiles.get(0))
        img = tile_data["oneway"] if self.is_oneway else tile_data["solid"]
        surface.blit(img, self.rect)
