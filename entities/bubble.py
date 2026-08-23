"""
entities/bubble.py - Bubble projectile, buoyant drift, 30s lifespan, and rideable physics.
"""
import pygame
import math
import random
from constants import (
    BUBBLE_INITIAL_SPEED, BUBBLE_FLOAT_SPEED, BUBBLE_SWAY_AMPLITUDE,
    BUBBLE_SWAY_FREQUENCY, BUBBLE_LIFESPAN, BUBBLE_FLASH_TIME,
    BUBBLE_RADIUS, GIANT_BUBBLE_RADIUS, VIRTUAL_WIDTH, VIRTUAL_HEIGHT,
    COLOR_WHITE, COLOR_RED, COLOR_CYAN
)

class Bubble:
    """A floating retro bubble entity with 2-phase physics and a 30-second lifespan."""
    def __init__(self, x, y, direction, owner_id, owner_team, max_distance=110.0, is_giant=False):
        self.x = float(x)
        self.y = float(y)
        self.direction = 1 if direction >= 0 else -1  # 1 = Right, -1 = Left
        self.owner_id = owner_id
        self.owner_team = owner_team
        self.max_distance = float(max_distance)
        self.is_giant = is_giant

        self.radius = GIANT_BUBBLE_RADIUS if is_giant else BUBBLE_RADIUS
        self.rect = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)

        # Physics state
        self.is_floating = False  # False = Phase 1 (horizontal shot), True = Phase 2 (buoyant drift)
        self.distance_traveled = 0.0
        self.vx = BUBBLE_INITIAL_SPEED * self.direction
        self.vy = 0.0
        self.origin_x = float(x)

        # Sway and lifespan
        self.lifespan = BUBBLE_LIFESPAN  # 30.0 seconds
        self.age = 0.0
        self.sway_phase = random.uniform(0, 2 * math.pi)
        self.is_alive = True
        self.anim_timer = 0.0
        self.anim_frame = 0

    def update(self, dt, platforms):
        """Updates bubble movement, collision with platforms, and lifespan."""
        self.age += dt
        self.anim_timer += dt
        if self.anim_timer >= 0.15:
            self.anim_timer = 0.0
            self.anim_frame = (self.anim_frame + 1) % 4

        # Check 30-second lifespan expiration
        if self.age >= self.lifespan:
            self.is_alive = False
            return False

        if not self.is_floating:
            # Phase 1: Rapid horizontal burst
            move_step = self.vx * dt
            self.x += move_step
            self.distance_traveled += abs(move_step)

            # Check if reached max travel distance
            if self.distance_traveled >= self.max_distance:
                self.is_floating = True
                self.origin_x = self.x
                self.vx = 0.0
                self.vy = BUBBLE_FLOAT_SPEED

            # Horizontal solid collision check
            self._update_rect()
            for plat in platforms:
                if not plat.is_oneway and plat.rect.colliderect(self.rect):
                    # Hit solid wall, start floating immediately
                    self.is_floating = True
                    self.origin_x = self.x
                    self.vx = 0.0
                    self.vy = BUBBLE_FLOAT_SPEED
                    break
        else:
            # Phase 2: Buoyant upward drift with sinusoidal left/right sway
            self.vy = BUBBLE_FLOAT_SPEED
            self.y += self.vy * dt

            # Sinusoidal horizontal sway
            sway_offset = math.sin(self.age * BUBBLE_SWAY_FREQUENCY * math.pi + self.sway_phase) * BUBBLE_SWAY_AMPLITUDE
            self.x = self.origin_x + sway_offset

            # Keep inside horizontal bounds or screen wrap
            if self.x < self.radius + 8:
                self.x = self.radius + 8
                self.origin_x = self.x
            elif self.x > VIRTUAL_WIDTH - self.radius - 8:
                self.x = VIRTUAL_WIDTH - self.radius - 8
                self.origin_x = self.x

            # Upward ceiling / platform collision (does not penetrate solid ceilings, glides around)
            self._update_rect()
            for plat in platforms:
                if not plat.is_oneway and plat.rect.colliderect(self.rect):
                    # If hitting the underside of a solid ceiling
                    if self.rect.top <= plat.rect.bottom and self.rect.centery > plat.rect.bottom:
                        self.y = plat.rect.bottom + self.radius
                        # Slide sideways along ceiling
                        self.origin_x += (20.0 * dt * self.direction)
                        break

            # Top screen boundary (stop at top or gently float)
            if self.y < self.radius + 18:
                self.y = self.radius + 18

        self._update_rect()
        return self.is_alive

    def _update_rect(self):
        self.rect.x = int(self.x - self.radius)
        self.rect.y = int(self.y - self.radius)

    def is_warning_flash(self):
        """Returns True when bubble is close to 30s expiration to flash warning."""
        if self.age >= BUBBLE_FLASH_TIME:
            # Flash fast in the final 6 seconds
            return (int(self.age * 8) % 2) == 0
        return False

    def draw(self, surface, sprite_manager):
        """Draws the animated bubble with warning flash if close to popping."""
        frames = sprite_manager.giant_bubbles if self.is_giant else sprite_manager.bubbles
        frame = frames[self.anim_frame]

        pos = (int(self.x - frame.get_width() // 2), int(self.y - frame.get_height() // 2))

        if self.is_warning_flash():
            # Draw with red warning tint
            tint_surf = frame.copy()
            tint_surf.fill((255, 60, 60, 100), special_flags=pygame.BLEND_RGBA_ADD)
            surface.blit(tint_surf, pos)
        else:
            surface.blit(frame, pos)
