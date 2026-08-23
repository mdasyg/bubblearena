"""
entities/trapped_bubble.py - Trapped player bubble, team rescue/elimination, and struggle logic.
"""
import pygame
import math
import random
from constants import (
    BUBBLE_FLOAT_SPEED, BUBBLE_SWAY_AMPLITUDE, BUBBLE_SWAY_FREQUENCY,
    BUBBLE_LIFESPAN, BUBBLE_FLASH_TIME, VIRTUAL_WIDTH, VIRTUAL_HEIGHT, STRUGGLE_ESCAPE_PRESSES
)

class TrappedBubble:
    """A floating bubble containing a trapped player."""
    def __init__(self, trapped_player, captor_id, captor_team):
        self.trapped_player = trapped_player
        self.captor_id = captor_id
        self.captor_team = captor_team

        self.x = float(trapped_player.x)
        self.y = float(trapped_player.y)
        self.origin_x = float(self.x)
        self.radius = 14
        self.rect = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)

        self.lifespan = BUBBLE_LIFESPAN  # 30.0 seconds
        self.age = 0.0
        self.sway_phase = random.uniform(0, 2 * math.pi)
        self.is_alive = True
        self.struggle_count = 0
        self.anim_timer = 0.0
        self.anim_frame = 0

        # Sync trapped player state
        self.trapped_player.is_trapped = True
        self.trapped_player.vx = 0.0
        self.trapped_player.vy = 0.0

    def register_struggle(self):
        """Called when trapped player mashes action buttons."""
        self.struggle_count += 1
        # Each press shaves off ~1.5s of remaining time
        self.age += 1.5

    def update(self, dt, platforms):
        """Floats upward, checks 30s expiration or escape."""
        self.age += dt
        self.anim_timer += dt
        if self.anim_timer >= 0.12:
            self.anim_timer = 0.0
            self.anim_frame = (self.anim_frame + 1) % 4

        # Check if struggle escape complete or 30s timeout
        if self.struggle_count >= STRUGGLE_ESCAPE_PRESSES or self.age >= self.lifespan:
            # Auto-pop / struggle escape -> Free the player!
            self.is_alive = False
            self.trapped_player.free_from_bubble(was_rescued=False)
            return False

        # Upward float with sway
        self.y += BUBBLE_FLOAT_SPEED * dt
        sway_offset = math.sin(self.age * BUBBLE_SWAY_FREQUENCY * math.pi + self.sway_phase) * BUBBLE_SWAY_AMPLITUDE
        self.x = self.origin_x + sway_offset

        # Strict arena boundary limits (outer 16px brick border + visual radius)
        min_x = 16 + self.radius
        max_x = VIRTUAL_WIDTH - 16 - self.radius
        min_y = 16 + self.radius + 2
        max_y = VIRTUAL_HEIGHT - 16 - self.radius

        if self.x < min_x:
            self.x = min_x
            self.origin_x = min_x
        elif self.x > max_x:
            self.x = max_x
            self.origin_x = max_x

        if self.y < min_y:
            self.y = min_y
        elif self.y > max_y:
            self.y = max_y

        self._update_rect()

        # Keep trapped player aligned with bubble
        self.trapped_player.x = self.x
        self.trapped_player.y = self.y
        self.trapped_player._update_rect()

        return self.is_alive

    def _update_rect(self):
        self.rect.x = int(self.x - self.radius)
        self.rect.y = int(self.y - self.radius)

    def is_warning_flash(self):
        """Flashes when close to popping/expiring."""
        return (self.age >= BUBBLE_FLASH_TIME) and ((int(self.age * 10) % 2) == 0)

    def check_pop_by_player(self, popping_player, is_team_mode=False):
        """
        Determines the pop result when another player touches this trapped bubble:
        Returns: ('KILL', points), ('RESCUE', points), or None
        """
        if not self.is_alive or popping_player.id == self.trapped_player.id:
            return None

        # Check collision with popping player
        if not self.rect.colliderect(popping_player.rect):
            return None

        # Team vs Opponent logic
        is_teammate = is_team_mode and (popping_player.team == self.trapped_player.team)

        if is_teammate:
            # Case B: TEAMMATE Pops -> RESCUE
            self.is_alive = False
            self.trapped_player.free_from_bubble(was_rescued=True)
            return ("RESCUE", 500)
        else:
            # Case A: OPPONENT Pops -> ELIMINATION / KILL
            self.is_alive = False
            self.trapped_player.kill_and_respawn()
            return ("KILL", 1000)

    def draw(self, surface, sprite_manager):
        """Draws the trapped bubble containing the animated squished player sprite."""
        player_dict = sprite_manager.players.get(self.trapped_player.id, sprite_manager.players[0])
        frames = player_dict.get("trapped", player_dict["idle"])
        frame = frames[self.anim_frame % len(frames)]

        pos = (int(self.x - frame.get_width() // 2), int(self.y - frame.get_height() // 2))

        if self.is_warning_flash():
            tint_surf = frame.copy()
            tint_surf.fill((255, 70, 70, 120), special_flags=pygame.BLEND_RGBA_ADD)
            surface.blit(tint_surf, pos)
        else:
            surface.blit(frame, pos)
