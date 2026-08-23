"""
tests/test_boundaries_and_controls.py - Verifies border containment for bubbles, powerups, players, and control responsiveness.
"""
import unittest
import pygame
from constants import (
    VIRTUAL_WIDTH, VIRTUAL_HEIGHT, LOCAL_KEY_MAPPINGS
)
from entities.player import Player
from entities.bubble import Bubble
from entities.trapped_bubble import TrappedBubble
from entities.powerup import PowerUp
from engine.input_handler import InputHandler

class TestBoundariesAndControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)

    def test_powerup_boundaries(self):
        """PowerUps must never spawn or fly into the top HUD or drop below the floor."""
        # Test extreme spawn coordinates
        p1 = PowerUp(x=5, y=5)
        self.assertGreaterEqual(p1.x, 24.0)
        self.assertGreaterEqual(p1.y, 36.0)

        # Test physics clamping
        p1.y = 10
        p1.vy = -100
        p1.update(0.1, [])
        self.assertGreaterEqual(p1.y, 36.0, "Powerup should not penetrate top HUD")
        self.assertGreaterEqual(p1.vy, 0.0, "Powerup upward velocity should halt at ceiling")

        # Test floor landing
        p2 = PowerUp(x=100, y=310)
        p2.vy = 200
        p2.update(0.1, [])
        self.assertLessEqual(p2.y, VIRTUAL_HEIGHT - 24.0)
        self.assertTrue(p2.on_ground)

    def test_bubble_wall_containment(self):
        """Bubbles must stay strictly inside the 16px brick border walls."""
        # 1. Phase 1 (Shooting left into left border wall)
        b_left = Bubble(x=20, y=100, direction=-1, owner_id=0, owner_team=0)
        b_left.update(0.1, [])
        self.assertGreaterEqual(b_left.x, 16 + b_left.radius, "Bubble should not penetrate left brick wall")
        self.assertTrue(b_left.is_floating)

        # 2. Phase 1 (Shooting right into right border wall)
        b_right = Bubble(x=460, y=100, direction=1, owner_id=0, owner_team=0)
        b_right.update(0.1, [])
        self.assertLessEqual(b_right.x, VIRTUAL_WIDTH - 16 - b_right.radius, "Bubble should not penetrate right brick wall")
        self.assertTrue(b_right.is_floating)

        # 3. Phase 2 (Floating up into top border)
        b_top = Bubble(x=200, y=20, direction=1, owner_id=0, owner_team=0)
        b_top.is_floating = True
        b_top.update(0.1, [])
        self.assertGreaterEqual(b_top.y, 16 + b_top.radius, "Bubble should not penetrate top ceiling/HUD")

    def test_trapped_bubble_containment(self):
        """Trapped bubbles must stay strictly inside the playable arena."""
        dummy_p = Player(player_id=1, spawn_x=10, spawn_y=10)
        tb = TrappedBubble(trapped_player=dummy_p, captor_id=0, captor_team=0)
        tb.update(0.1, [])
        self.assertGreaterEqual(tb.x, 16 + tb.radius)
        self.assertGreaterEqual(tb.y, 16 + tb.radius)
        self.assertGreaterEqual(dummy_p.x, 16 + tb.radius)
        self.assertGreaterEqual(dummy_p.y, 16 + tb.radius)

    def test_player_border_confinement(self):
        """Player physics and sprite bounding boxes must stay inside arena walls."""
        p = Player(player_id=0, spawn_x=5, spawn_y=5)
        p.update(0.1, [], [], [])
        self.assertGreaterEqual(p.rect.left, 18, "Player left rect should stay inside left border")
        self.assertGreaterEqual(p.rect.top, 20, "Player top rect should stay below ceiling")

        p.x = 480
        p.update(0.1, [], [], [])
        self.assertLessEqual(p.rect.right, VIRTUAL_WIDTH - 18, "Player right rect should stay inside right border")

    def test_multi_key_and_jump_buffer_controls(self):
        """Player 1 key mappings should support WASD, Arrow keys, Space, and Jump buffering."""
        handler = InputHandler()
        p0_keys = LOCAL_KEY_MAPPINGS[0]
        
        # Verify Player 0 has multiple bindings for jump and shoot
        self.assertIn(pygame.K_SPACE, p0_keys["jump"])
        self.assertIn(pygame.K_w, p0_keys["jump"])
        self.assertIn(pygame.K_a, p0_keys["left"])
        self.assertIn(pygame.K_d, p0_keys["right"])

        # Test immediate Jump when grounded
        player = Player(player_id=0, spawn_x=100, spawn_y=100)
        player.is_grounded = True
        player.handle_input({"jump": True}, 0.016, [], None)
        self.assertLess(player.vy, 0.0, "Immediate jump should launch player upward")

        # Test Jump buffering while airborne
        player2 = Player(player_id=0, spawn_x=100, spawn_y=100)
        player2.is_grounded = False
        player2.vy = 50.0
        player2.handle_input({"jump": True}, 0.016, [], None)
        self.assertGreater(player2.jump_buffer_timer, 0.0, "Jump input in air should be buffered")
        
        # When player2 lands on ground, buffered jump should trigger
        player2.is_grounded = True
        player2.update(0.016, [], [], [])
        self.assertLess(player2.vy, 0.0, "Buffered jump should execute once grounded")

if __name__ == "__main__":
    unittest.main()
