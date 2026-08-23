"""
entities/player.py - Player character physics, one-way collision, bubble shooting, bubble riding, and state machine.
"""
import pygame
import math
import random
from constants import (
    GRAVITY, MAX_FALL_SPEED, PLAYER_SPEED, PLAYER_JUMP_SPEED,
    BUBBLE_BOUNCE_SPEED, ACCELERATION, FRICTION, AIR_ACCEL, AIR_FRICTION,
    BUBBLE_FIRE_COOLDOWN, RAPID_FIRE_COOLDOWN, BUBBLE_SHOT_DISTANCE,
    RESPAWN_DELAY, INVULNERABLE_DURATION, VIRTUAL_WIDTH, VIRTUAL_HEIGHT,
    COLOR_WHITE, COLOR_GOLD, PLAYER_COLORS
)
from entities.bubble import Bubble

class Player:
    """Represents a player character (human or AI controlled)."""
    def __init__(self, player_id, spawn_x, spawn_y, team=0, is_bot=False):
        self.id = player_id
        self.name = PLAYER_COLORS[player_id]["name"]
        self.team = team
        self.is_bot = is_bot

        # Spawn coordinates
        self.spawn_x = float(spawn_x)
        self.spawn_y = float(spawn_y)
        self.x = float(spawn_x)
        self.y = float(spawn_y)

        # Dimensions & Hitbox (20x20 sprite, 14x16 physics hitbox)
        self.width = 14
        self.height = 16
        self.rect = pygame.Rect(int(self.x - self.width // 2), int(self.y - self.height // 2), self.width, self.height)

        # Physics variables
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1  # 1 = Right, -1 = Left
        self.is_grounded = False
        self.can_double_jump = False
        self.jump_buffer_timer = 0.0
        self.coyote_timer = 0.0

        # States & Lifecycle
        self.is_alive = True
        self.is_trapped = False
        self.respawn_timer = 0.0
        self.invulnerable_timer = INVULNERABLE_DURATION  # spawn shield

        # Shooting variables
        self.shoot_cooldown = 0.0
        self.shoot_anim_timer = 0.0
        self.bubble_ride_timer = 0.0

        # Power-up buff timers
        self.speed_buff_timer = 0.0
        self.range_buff_timer = 0.0
        self.rapid_buff_timer = 0.0
        self.giant_buff_timer = 0.0

        # Stats
        self.score = 0
        self.kills = 0
        self.deaths = 0
        self.rescues = 0
        self.flag_captures = 0

        # Animation state
        self.anim_state = "idle"
        self.anim_frame = 0
        self.anim_timer = 0.0

        # AI decision timer
        self.bot_think_timer = random.uniform(0.1, 0.3)
        self.bot_action = {"left": False, "right": False, "jump": False, "shoot": False, "struggle": False}

    def reset_for_round(self, spawn_x, spawn_y):
        """Resets player position and buffs for a new round/level."""
        self.spawn_x = float(spawn_x)
        self.spawn_y = float(spawn_y)
        self.x = float(spawn_x)
        self.y = float(spawn_y)
        self.vx = 0.0
        self.vy = 0.0
        self.is_alive = True
        self.is_trapped = False
        self.is_grounded = True
        self.respawn_timer = 0.0
        self.invulnerable_timer = INVULNERABLE_DURATION
        self.bubble_ride_timer = 0.0
        self.speed_buff_timer = 0.0
        self.range_buff_timer = 0.0
        self.rapid_buff_timer = 0.0
        self.giant_buff_timer = 0.0
        self._update_rect()

    def kill_and_respawn(self):
        """Called when eliminated/popped by opponent."""
        self.is_alive = False
        self.is_trapped = False
        self.deaths += 1
        self.respawn_timer = RESPAWN_DELAY
        self.vx = 0.0
        self.vy = 0.0

    def free_from_bubble(self, was_rescued=True):
        """Called when popped out of bubble by teammate or timeout."""
        self.is_trapped = False
        self.is_alive = True
        self.vy = -120.0  # gentle hop out of bubble
        self.invulnerable_timer = 2.0 if was_rescued else 1.0

    def handle_input(self, inputs, dt, spawned_bubbles, sound_mgr=None, particle_mgr=None):
        """Processes player control inputs (move, jump, shoot, struggle)."""
        if not self.is_alive or self.is_trapped:
            return

        # Calculate current move speed with buff
        base_speed = PLAYER_SPEED * (1.4 if self.speed_buff_timer > 0 else 1.0)

        # Horizontal movement
        move_dir = 0
        if inputs.get("left"):
            move_dir -= 1
            self.facing = -1
        if inputs.get("right"):
            move_dir += 1
            self.facing = 1

        # Acceleration & Friction
        target_vx = move_dir * base_speed
        accel = ACCELERATION if self.is_grounded else AIR_ACCEL
        fric = FRICTION if self.is_grounded else AIR_FRICTION

        if move_dir != 0:
            if self.vx < target_vx:
                self.vx = min(target_vx, self.vx + accel * dt)
            elif self.vx > target_vx:
                self.vx = max(target_vx, self.vx - accel * dt)
        else:
            if self.vx > 0:
                self.vx = max(0.0, self.vx - fric * dt)
            elif self.vx < 0:
                self.vx = min(0.0, self.vx + fric * dt)

        # Jump (immediate if grounded, otherwise buffered)
        if inputs.get("jump"):
            self.jump_buffer_timer = 0.14
            if self.is_grounded or self.coyote_timer > 0.0:
                self.vy = PLAYER_JUMP_SPEED
                self.is_grounded = False
                self.coyote_timer = 0.0
                self.jump_buffer_timer = 0.0
                if sound_mgr:
                    sound_mgr.play_sfx("jump")
                if particle_mgr:
                    particle_mgr.spawn_jump_dust(self.x, self.rect.bottom)

        # Shoot Bubble
        if inputs.get("shoot") and self.shoot_cooldown <= 0.0:
            cooldown = RAPID_FIRE_COOLDOWN if self.rapid_buff_timer > 0 else BUBBLE_FIRE_COOLDOWN
            self.shoot_cooldown = cooldown
            self.shoot_anim_timer = 0.20

            # Bubble spawn parameters
            shot_dist = BUBBLE_SHOT_DISTANCE * (1.6 if self.range_buff_timer > 0 else 1.0)
            is_giant = (self.giant_buff_timer > 0)
            bubble_spawn_x = self.x + (self.facing * 12)
            bubble_spawn_y = self.y - 2

            new_bubble = Bubble(
                bubble_spawn_x, bubble_spawn_y, self.facing,
                owner_id=self.id, owner_team=self.team,
                max_distance=shot_dist, is_giant=is_giant
            )
            spawned_bubbles.append(new_bubble)

            if sound_mgr:
                sound_mgr.play_sfx("shoot")

    def update(self, dt, platforms, bubbles, trapped_bubbles, sound_mgr=None, particle_mgr=None, level_mgr=None):
        """Updates physics, platform collisions, bubble riding, and timers."""
        # Timers
        if self.invulnerable_timer > 0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)
        if self.speed_buff_timer > 0:
            self.speed_buff_timer = max(0.0, self.speed_buff_timer - dt)
        if self.range_buff_timer > 0:
            self.range_buff_timer = max(0.0, self.range_buff_timer - dt)
        if self.rapid_buff_timer > 0:
            self.rapid_buff_timer = max(0.0, self.rapid_buff_timer - dt)
        if self.giant_buff_timer > 0:
            self.giant_buff_timer = max(0.0, self.giant_buff_timer - dt)
        if self.shoot_cooldown > 0:
            self.shoot_cooldown = max(0.0, self.shoot_cooldown - dt)
        if self.shoot_anim_timer > 0:
            self.shoot_anim_timer = max(0.0, self.shoot_anim_timer - dt)
        if self.bubble_ride_timer > 0:
            self.bubble_ride_timer = max(0.0, self.bubble_ride_timer - dt)

        # Handle respawn countdown if dead
        if not self.is_alive:
            self.respawn_timer -= dt
            self._update_animation(dt)
            if self.respawn_timer <= 0:
                if level_mgr:
                    rx, ry = level_mgr.get_random_platform_spawn()
                    self.reset_for_round(rx, ry)
                else:
                    self.reset_for_round(self.spawn_x, self.spawn_y)
                self.is_grounded = True
                if particle_mgr:
                    particle_mgr.spawn_sparkles(self.x, self.y, COLOR_GOLD, count=12)
            return

        # If trapped inside bubble, physics are managed by TrappedBubble
        if self.is_trapped:
            self._update_rect()
            return

        # --- 0. Jump Buffering & Coyote Grace Execution ---
        if self.jump_buffer_timer > 0.0:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)
            if self.is_grounded or self.coyote_timer > 0.0:
                self.vy = PLAYER_JUMP_SPEED
                self.is_grounded = False
                self.coyote_timer = 0.0
                self.jump_buffer_timer = 0.0
                if sound_mgr:
                    sound_mgr.play_sfx("jump")
                if particle_mgr:
                    particle_mgr.spawn_jump_dust(self.x, self.rect.bottom)

        # Update coyote timer when falling off a ledge
        if self.is_grounded:
            self.coyote_timer = 0.10
        elif self.coyote_timer > 0.0:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)

        # --- 1. Apply Gravity ---
        self.vy = min(MAX_FALL_SPEED, self.vy + GRAVITY * dt)

        # --- 2. Horizontal Movement & Solid Wall Collisions ---
        self.x += self.vx * dt
        self._update_rect()

        # Enforce arena screen horizontal boundaries (inside 16px border walls)
        # Hitbox width is 14, visual sprite width is 24 (12px on each side of self.x).
        if self.rect.left < 18:
            self.rect.left = 18
            self.x = self.rect.centerx
            self.vx = max(0.0, self.vx)
        elif self.rect.right > VIRTUAL_WIDTH - 18:
            self.rect.right = VIRTUAL_WIDTH - 18
            self.x = self.rect.centerx
            self.vx = min(0.0, self.vx)

        for plat in platforms:
            if not plat.is_oneway and plat.rect.colliderect(self.rect):
                if self.vx > 0:
                    self.rect.right = plat.rect.left
                    self.x = self.rect.centerx
                    self.vx = 0.0
                elif self.vx < 0:
                    self.rect.left = plat.rect.right
                    self.x = self.rect.centerx
                    self.vx = 0.0

        # --- 3. Vertical Movement & Platform / Bubble Collisions ---
        prev_bottom = self.rect.bottom
        prev_top = self.rect.top
        self.y += self.vy * dt
        self._update_rect()
        self.is_grounded = False

        # One-way & solid platform collisions
        for plat in platforms:
            if self.vy >= 0:
                # Falling downward: check landing on top of platform
                if plat.check_player_landing(prev_bottom, self.rect, self.vy):
                    self.rect.bottom = plat.rect.top
                    self.y = self.rect.centery
                    self.vy = 0.0
                    self.is_grounded = True
                    break
            elif self.vy < 0 and not plat.is_oneway:
                # Rising upward: check bumping head into solid ceiling block from below
                if prev_top >= plat.rect.bottom - 8 and self.rect.top <= plat.rect.bottom:
                    if (plat.rect.left - 2) <= self.rect.centerx <= (plat.rect.right + 2):
                        self.rect.top = plat.rect.bottom
                        self.y = self.rect.centery
                        self.vy = 0.0
                        break

        # Enforce screen vertical boundaries (below HUD/ceiling row 0 at y=16 and above floor row 19 at y=304)
        if self.rect.top < 20:
            self.rect.top = 20
            self.y = self.rect.centery
            if self.vy < 0:
                self.vy = 0.0
        elif self.rect.bottom >= VIRTUAL_HEIGHT - 16:
            self.rect.bottom = VIRTUAL_HEIGHT - 16
            self.y = self.rect.centery
            self.vy = 0.0
            self.is_grounded = True

        # --- 4. Bubble Riding & Trampoline Jumping ---
        # When falling or jumping on top of any floating bubble, bounce upward!
        all_floating_bubbles = [b for b in bubbles if b.is_floating] + [tb for tb in trapped_bubbles if tb.is_alive]
        for b in all_floating_bubbles:
            # Check landing on top of bubble
            if self.vy > 0 and prev_bottom <= b.rect.centery and self.rect.bottom >= b.rect.top:
                if abs(self.rect.centerx - b.rect.centerx) < b.radius + 6:
                    self.rect.bottom = b.rect.top
                    self.y = self.rect.centery
                    self.vy = BUBBLE_BOUNCE_SPEED  # Trampoline bounce!
                    self.is_grounded = False
                    self.bubble_ride_timer = 0.35
                    if sound_mgr:
                        sound_mgr.play_sfx("bounce")
                    if particle_mgr:
                        particle_mgr.spawn_jump_dust(self.x, self.rect.bottom)
                    break

        # --- 5. Animation State Determination ---
        self._update_animation(dt)

    def _update_rect(self):
        self.rect.x = int(self.x - self.width // 2)
        self.rect.y = int(self.y - self.height // 2)

    def _update_animation(self, dt):
        self.anim_timer += dt
        if not self.is_alive:
            self.anim_state = "pop_death"
            frame_interval = 0.15
        elif self.is_trapped:
            self.anim_state = "trapped"
            frame_interval = 0.20
        elif self.shoot_anim_timer > 0:
            self.anim_state = "shoot"
            frame_interval = 0.04
        elif self.bubble_ride_timer > 0:
            self.anim_state = "bubble_ride"
            frame_interval = 0.08
        elif not self.is_grounded:
            self.anim_state = "jump" if self.vy < 0 else "fall"
            frame_interval = 0.08
        elif abs(self.vx) > 10.0:
            self.anim_state = "walk"
            frame_interval = 0.08
        else:
            self.anim_state = "idle"
            frame_interval = 0.16

        # Frame advancement
        if self.anim_timer >= frame_interval:
            self.anim_timer = 0.0
            self.anim_frame += 1

    def update_bot_ai(self, dt, all_players, bubbles, trapped_bubbles, flag=None):
        """Intelligent retro arcade bot logic."""
        if not self.is_bot or not self.is_alive or self.is_trapped:
            return self.bot_action

        self.bot_think_timer -= dt
        if self.bot_think_timer > 0:
            return self.bot_action

        self.bot_think_timer = random.uniform(0.1, 0.25)
        actions = {"left": False, "right": False, "jump": False, "shoot": False, "struggle": True}

        # 1. Look for trapped enemies to pop / trapped allies to rescue
        target_tb = None
        for tb in trapped_bubbles:
            if tb.is_alive:
                target_tb = tb
                break

        # 2. Look for closest active enemy or flag
        target_x, target_y = None, None
        if target_tb:
            target_x, target_y = target_tb.x, target_tb.y
        elif flag and flag.carrier != self:
            target_x, target_y = flag.x, flag.y
        else:
            # Find closest enemy player
            opponents = [p for p in all_players if p.id != self.id and p.is_alive and not p.is_trapped]
            if opponents:
                closest_opp = min(opponents, key=lambda p: (p.x - self.x)**2 + (p.y - self.y)**2)
                target_x, target_y = closest_opp.x, closest_opp.y

        if target_x is not None:
            # Horizontal steering
            if target_x < self.x - 12:
                actions["left"] = True
            elif target_x > self.x + 12:
                actions["right"] = True

            # Jump if target is higher than bot
            if target_y < self.y - 20 and self.is_grounded:
                actions["jump"] = True

            # Shoot if on roughly same vertical level as target
            if abs(target_y - self.y) < 24 and random.random() < 0.7:
                # Shoot towards target
                facing_target = (target_x > self.x and self.facing > 0) or (target_x < self.x and self.facing < 0)
                if facing_target:
                    actions["shoot"] = True

        # Random occasional jump for agility
        if self.is_grounded and random.random() < 0.08:
            actions["jump"] = True

        self.bot_action = actions
        return self.bot_action

    def draw(self, surface, sprite_manager):
        """Renders the player character sprite with facing flip, invulnerability flash, and smooth alignments."""
        if not self.is_alive:
            # Render pop death animation during first 1.2s of death
            if self.respawn_timer < (RESPAWN_DELAY - 1.2):
                return

        # Invulnerability flashing
        if self.invulnerable_timer > 0 and (int(self.invulnerable_timer * 12) % 2 == 0):
            # Flash / skip render frame
            return

        player_sprites = sprite_manager.players.get(self.id, sprite_manager.players[0])
        frames = player_sprites.get(self.anim_state, player_sprites.get("idle", []))
        if not frames:
            return

        if self.anim_state == "pop_death":
            frame_idx = min(self.anim_frame, len(frames) - 1)
        else:
            frame_idx = self.anim_frame % len(frames)

        frame = frames[frame_idx]

        # Flip horizontally if facing left
        if self.facing < 0:
            frame = pygame.transform.flip(frame, True, False)

        draw_x = int(self.x - frame.get_width() // 2)
        if self.is_trapped:
            draw_y = int(self.y - frame.get_height() // 2)
        else:
            draw_y = int(self.rect.bottom - frame.get_height())

        surface.blit(frame, (draw_x, draw_y))

        # Speed buff indicator (sparkle trail)
        if self.speed_buff_timer > 0:
            pygame.draw.circle(surface, COLOR_YELLOW, (int(self.x), int(self.rect.bottom)), 2)

        # Star Shield aura
        if self.invulnerable_timer > 0:
            shield_surf = pygame.Surface((28, 28), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (255, 220, 50, 90), (14, 14), 13, width=2)
            surface.blit(shield_surf, (int(self.x - 14), int(self.y - 14)))
