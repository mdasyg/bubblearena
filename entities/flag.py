"""
entities/flag.py - Flag entity for Capture The Flag mode in Bubble Arena.
"""
import pygame
import math
from constants import COLOR_GOLD, COLOR_WHITE, COLOR_RED, COLOR_BLUE

class Flag:
    """The CTF flag that players fight to capture, carry, and score with."""
    def __init__(self, spawn_x, spawn_y):
        self.spawn_x = float(spawn_x)
        self.spawn_y = float(spawn_y)
        self.x = float(spawn_x)
        self.y = float(spawn_y)
        self.carrier = None  # Reference to Player holding the flag
        self.rect = pygame.Rect(int(self.x - 9), int(self.y - 11), 18, 22)

        self.anim_timer = 0.0
        self.anim_frame = 0
        self.drop_timer = 0.0
        self.hold_tick = 0.0

    def update(self, dt):
        self.anim_timer += dt
        if self.anim_timer >= 0.12:
            self.anim_timer = 0.0
            self.anim_frame = (self.anim_frame + 1) % 4

        if self.carrier is not None:
            # Check if carrier was trapped or killed
            if self.carrier.is_trapped or not self.carrier.is_alive:
                self.drop()
            else:
                # Follow carrier
                self.x = self.carrier.x
                self.y = self.carrier.y - 14
                self.rect.center = (int(self.x), int(self.y))

                # Periodic hold points (e.g. +10 points per 0.5s)
                self.hold_tick += dt
                if self.hold_tick >= 0.5:
                    self.hold_tick = 0.0
                    self.carrier.score += 15
        else:
            # Dropped state timer
            if (self.x, self.y) != (self.spawn_x, self.spawn_y):
                self.drop_timer += dt
                if self.drop_timer >= 12.0:
                    self.reset_to_spawn()
            self.rect.center = (int(self.x), int(self.y))

    def pickup(self, player):
        """Called when a player picks up the flag."""
        if not player.is_trapped and player.is_alive and self.carrier is None:
            self.carrier = player
            self.drop_timer = 0.0
            return True
        return False

    def drop(self):
        """Drops flag at carrier's current position."""
        if self.carrier:
            self.x = self.carrier.x
            self.y = self.carrier.y
            self.carrier = None
            self.drop_timer = 0.0

    def reset_to_spawn(self):
        """Returns flag to center spawn pedestal."""
        self.carrier = None
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.drop_timer = 0.0

    def draw(self, surface, sprite_manager):
        frames = sprite_manager.flag_frames
        frame = frames[self.anim_frame]
        surface.blit(frame, (int(self.x - frame.get_width() // 2), int(self.y - frame.get_height() // 2)))

        # Draw glowing halo if on ground
        if self.carrier is None:
            glow_surf = pygame.Surface((28, 28), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 215, 0, 80), (14, 14), 13)
            surface.blit(glow_surf, (int(self.x - 14), int(self.y - 14)))
