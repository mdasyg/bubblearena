"""
tests/test_game.py - Automated test suite for Bubble Arena.
"""
import unittest
import pygame
import os

# Use dummy video & audio driver for headless testing
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

pygame.init()
pygame.display.set_mode((1, 1))

from constants import (
    BUBBLE_LIFESPAN, BUBBLE_INITIAL_SPEED, BUBBLE_FLOAT_SPEED,
    MODE_FFA, MODE_TEAM, MODE_CTF
)
from engine.sprites import SpriteManager
from engine.sound import SoundManager
from levels.level_manager import LevelManager
from entities.player import Player
from entities.bubble import Bubble
from entities.trapped_bubble import TrappedBubble
from entities.powerup import PowerUp, POWERUP_SHOES, POWERUP_BLUE_CANDY, POWERUP_YELLOW_CANDY
from entities.flag import Flag
from modes.ffa_mode import FFAMode
from modes.team_mode import TeamMode
from modes.ctf_mode import CTFMode
from network.protocol import encode_packet, parse_packets, MSG_INPUT

class TestBubbleArena(unittest.TestCase):
    def setUp(self):
        self.sprite_mgr = SpriteManager()
        self.sound_mgr = SoundManager()
        self.level_mgr = LevelManager()

    def test_sprite_generation(self):
        """Verify all 4 players, bubbles, 10 tiles, powerups, and flags are generated."""
        self.assertEqual(len(self.sprite_mgr.players), 4)
        for p_id, p_dict in self.sprite_mgr.players.items():
            self.assertIn("idle", p_dict)
            self.assertIn("walk", p_dict)
            self.assertIn("jump", p_dict)
            self.assertIn("shoot", p_dict)
            self.assertIn("trapped", p_dict)
            self.assertIn("pop_death", p_dict)
            self.assertIn("victory", p_dict)

        self.assertGreaterEqual(len(self.sprite_mgr.bubbles), 4)
        self.assertGreaterEqual(len(self.sprite_mgr.giant_bubbles), 4)
        self.assertEqual(len(self.sprite_mgr.tiles), 10)
        self.assertIn("shoes", self.sprite_mgr.powerups)
        self.assertIn("candy_blue", self.sprite_mgr.powerups)
        self.assertIn("candy_yellow", self.sprite_mgr.powerups)
        self.assertIn("shield", self.sprite_mgr.powerups)
        self.assertGreaterEqual(len(self.sprite_mgr.flag_frames), 4)

    def test_sound_synthesis(self):
        """Verify procedural sound generation and BGM compilation."""
        sfx_keys = ["shoot", "pop", "jump", "bounce", "trap", "rescue", "powerup", "death", "hurry", "victory"]
        for key in sfx_keys:
            self.assertIn(key, self.sound_mgr.sfx)
            self.assertIsNotNone(self.sound_mgr.sfx[key])

        self.assertIsNotNone(self.sound_mgr.normal_bgm)
        self.assertIsNotNone(self.sound_mgr.fast_bgm_sound)

    def test_all_10_levels_loading(self):
        """Verify that at least 10 levels exist, load, and have platforms and spawns."""
        self.assertGreaterEqual(self.level_mgr.get_level_count(), 10)
        for idx in range(10):
            self.level_mgr.load_level(idx)
            self.assertGreater(len(self.level_mgr.platforms), 10)
            self.assertIn(0, self.level_mgr.spawn_points)
            self.assertIn(1, self.level_mgr.spawn_points)
            self.assertIn(2, self.level_mgr.spawn_points)
            self.assertIn(3, self.level_mgr.spawn_points)
            self.assertIsNotNone(self.level_mgr.flag_spawn)

    def test_bubble_physics_and_30s_lifespan(self):
        """Verify bubble starts with horizontal burst, switches to buoyant drift, and expires at 30s."""
        bubble = Bubble(x=100, y=100, direction=1, owner_id=0, owner_team=0, max_distance=50.0)
        self.assertFalse(bubble.is_floating)
        self.assertGreater(bubble.vx, 0)

        # Update 0.5 seconds -> reaches max horizontal distance and starts buoyant rise
        bubble.update(0.5, self.level_mgr.platforms)
        self.assertTrue(bubble.is_floating)
        self.assertEqual(bubble.vy, BUBBLE_FLOAT_SPEED)

        # Fast forward time to 29.0s -> Still alive, warning flash active
        bubble.update(28.5, self.level_mgr.platforms)
        self.assertTrue(bubble.is_alive)
        self.assertTrue(bubble.is_warning_flash())

        # Fast forward past 30.0s -> Expires/pops
        is_still_alive = bubble.update(2.0, self.level_mgr.platforms)
        self.assertFalse(is_still_alive)
        self.assertFalse(bubble.is_alive)

    def test_player_platform_one_way_and_jumping(self):
        """Verify player jumps through bottom of one-way platforms and lands solidly on top."""
        self.level_mgr.load_level(0)
        player = Player(player_id=0, spawn_x=50, spawn_y=30, team=0)

        # Update falling down
        player.vy = 100.0
        player.update(0.1, self.level_mgr.platforms, [], [])
        self.assertGreater(player.y, 30)

        # Jump impulse
        player.is_grounded = True
        player.handle_input({"jump": True}, 0.016, [], self.sound_mgr)
        self.assertLess(player.vy, 0)

    def test_player_jump_into_ceiling_no_stick(self):
        """Verify player jumping all the way into top ceiling does not stick and falls back down."""
        self.level_mgr.load_level(0)
        player = Player(player_id=1, spawn_x=40, spawn_y=40, team=1)
        player.vy = -300.0  # powerful jump into ceiling

        # Update frame hitting ceiling
        player.update(0.1, self.level_mgr.platforms, [], [])
        # Player rect top must be >= 16 (below ceiling row 0)
        self.assertGreaterEqual(player.rect.top, 16)
        # Player must NOT be marked grounded on the ceiling!
        self.assertFalse(player.is_grounded)

        # In next frames, gravity pulls player down immediately
        player.update(0.1, self.level_mgr.platforms, [], [])
        self.assertGreater(player.vy, 0) # Falling downwards!
        self.assertGreater(player.y, 24) # Moving away from ceiling!

    def test_bubble_riding_and_trampoline_bounce(self):
        """Verify player landing on a floating bubble triggers a trampoline bounce."""
        player = Player(player_id=0, spawn_x=100, spawn_y=80, team=0)
        player.vy = 150.0  # falling down

        bubble = Bubble(x=100, y=100, direction=1, owner_id=0, owner_team=0)
        bubble.is_floating = True

        player.update(0.016, self.level_mgr.platforms, [bubble], [], self.sound_mgr)
        # Verify trampoline upward bounce velocity applied
        self.assertLess(player.vy, 0)

    def test_trapped_bubble_rescue_vs_kill(self):
        """Verify opponent pops trapped bubble for KILL vs teammate pops for RESCUE."""
        # Team 0: Green (p0) + Yellow (p2)
        # Team 1: Blue (p1) + Pink (p3)
        p0 = Player(player_id=0, spawn_x=100, spawn_y=100, team=0)
        p1 = Player(player_id=1, spawn_x=100, spawn_y=100, team=1)
        p2 = Player(player_id=2, spawn_x=100, spawn_y=100, team=0)

        # Trap Player 0
        tb = TrappedBubble(p0, captor_id=1, captor_team=1)
        self.assertTrue(p0.is_trapped)

        # Teammate (p2) touches trapped bubble -> RESCUE
        res = tb.check_pop_by_player(p2, is_team_mode=True)
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "RESCUE")
        self.assertFalse(p0.is_trapped)
        self.assertTrue(p0.is_alive)
        self.assertGreater(p0.invulnerable_timer, 0)

        # Trap Player 0 again
        tb2 = TrappedBubble(p0, captor_id=1, captor_team=1)
        # Opponent (p1) touches trapped bubble -> KILL
        res2 = tb2.check_pop_by_player(p1, is_team_mode=True)
        self.assertIsNotNone(res2)
        self.assertEqual(res2[0], "KILL")
        self.assertFalse(p0.is_alive)
        self.assertGreater(p0.respawn_timer, 0)

    def test_powerup_effects(self):
        """Verify power-up application (speed, range, rapid fire, shield)."""
        player = Player(player_id=0, spawn_x=100, spawn_y=100, team=0)

        pw_shoes = PowerUp(100, 100, item_type=POWERUP_SHOES)
        pw_shoes.apply_to_player(player)
        self.assertGreater(player.speed_buff_timer, 0)

        pw_blue = PowerUp(100, 100, item_type=POWERUP_BLUE_CANDY)
        pw_blue.apply_to_player(player)
        self.assertGreater(player.range_buff_timer, 0)

        pw_yellow = PowerUp(100, 100, item_type=POWERUP_YELLOW_CANDY)
        pw_yellow.apply_to_player(player)
        self.assertGreater(player.rapid_buff_timer, 0)

    def test_ctf_flag_mechanics(self):
        """Verify flag pickup, carrier holding, dropping, and scoring."""
        flag = Flag(spawn_x=200, spawn_y=150)
        p0 = Player(player_id=0, spawn_x=200, spawn_y=150, team=0)

        # Pickup
        success = flag.pickup(p0)
        self.assertTrue(success)
        self.assertEqual(flag.carrier, p0)

        # Update flag holding
        p0.score = 0
        flag.update(0.6)
        self.assertGreater(p0.score, 0)

        # Carrier trapped -> drops flag
        p0.is_trapped = True
        flag.update(0.016)
        self.assertIsNone(flag.carrier)

    def test_game_engine_bubble_trap_flow(self):
        """Verify full GameEngine update flow: bubble shot, opponent trap, and trapped bubble list handling."""
        from engine.game import GameEngine
        engine = GameEngine(is_bot_match=False)
        engine.start_match()
        
        # Position P0 and P1 near each other
        p0 = engine.players[0]
        p1 = engine.players[1]
        p0.x = 100
        p0.y = 100
        p1.x = 120
        p1.y = 100
        p0.invulnerable_timer = 0
        p1.invulnerable_timer = 0
        
        # P0 shoots bubble towards P1
        p0.facing = 1
        p0.handle_input({"shoot": True}, 0.016, engine.bubbles, engine.sound_mgr)
        self.assertGreater(len(engine.bubbles), 0)
        
        # Engine updates -> Bubble hits P1 -> creates TrappedBubble without error!
        engine.update(0.05)
        self.assertGreater(len(engine.trapped_bubbles), 0)
        self.assertTrue(p1.is_trapped)

if __name__ == "__main__":
    unittest.main()
