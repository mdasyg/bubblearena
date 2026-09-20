"""
entities/trapped_bubble.py - Trapped player bubble, team rescue/elimination, and struggle logic.
"""
import pygame
import math
import random
from constants import (
    BUBBLE_FLOAT_SPEED, BUBBLE_SWAY_AMPLITUDE, BUBBLE_SWAY_FREQUENCY,
    BUBBLE_TRAPPED_LIFESPAN, BUBBLE_TRAPPED_FLASH_TIME, VIRTUAL_WIDTH, VIRTUAL_HEIGHT, STRUGGLE_ESCAPE_PRESSES
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

        self.lifespan = BUBBLE_TRAPPED_LIFESPAN  # 18.0 seconds
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
        if getattr(self.trapped_player, "is_bot", False):
            self.trapped_player.bot_action = {}

    def register_struggle(self):
        """Called when trapped player mashes action buttons (cosmetic struggle wobble)."""
        self.struggle_count += 1
        self.sway_phase += 0.25  # Visual wiggle wobble, but never self-breaks

    def update(self, dt, platforms):
        """Floats upward, checks 30s expiration."""
        self.age += dt
        self.anim_timer += dt
        if self.anim_timer >= 0.12:
            self.anim_timer = 0.0
            self.anim_frame = (self.anim_frame + 1) % 4

        # Only expires naturally after full lifespan (cannot be broken by trapped player)
        if self.age >= self.lifespan:
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
        return (self.age >= BUBBLE_TRAPPED_FLASH_TIME) and ((int(self.age * 10) % 2) == 0)

    def check_pop_by_player(self, popping_player, is_team_mode=False, force_pop=False):
        """
        Determines the pop result when another player touches this trapped bubble
        or when popped via chain explosion (force_pop=True):
        Returns: ('KILL', points), ('RESCUE', points), or None
        """
        # The trapped player CANNOT pop their own bubble
        if popping_player.id == self.trapped_player.id:
            return None

        if not force_pop and not self.rect.colliderect(popping_player.rect):
            return None

        self.is_alive = False

        # Team vs Opponent logic
        is_teammate = is_team_mode and (popping_player.team == self.trapped_player.team)

        if is_teammate:
            # Case B: TEAMMATE Pops -> RESCUE
            self.trapped_player.free_from_bubble(was_rescued=True)
            return ("RESCUE", 500)
        else:
            # Case A: OPPONENT Pops -> ELIMINATION / KILL
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
