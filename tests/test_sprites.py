"""
tests/test_sprites.py - Verifies loading, extraction, and rendering of player sprite sheets.
"""
import unittest
import pygame
from engine.sprites import SpriteManager
from entities.player import Player

class TestSpriteAnimations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)

    def test_all_player_sprite_animations_loaded(self):
        """Verify all 4 players have rich sprite animations loaded across all action states."""
        mgr = SpriteManager()
        required_states = ["idle", "walk", "jump", "fall", "shoot", "bubble_ride", "trapped", "pop_death", "victory"]
        
        for p_id in range(4):
            self.assertIn(p_id, mgr.players, f"Player {p_id} missing from SpriteManager")
            p_anims = mgr.players[p_id]
            for state in required_states:
                self.assertIn(state, p_anims, f"State '{state}' missing for Player {p_id}")
                frames = p_anims[state]
                self.assertGreater(len(frames), 0, f"No frames for state '{state}' for Player {p_id}")
                for f_idx, surf in enumerate(frames):
                    self.assertIsInstance(surf, pygame.Surface)
                    self.assertGreater(surf.get_width(), 0)
                    self.assertGreater(surf.get_height(), 0)

    def test_player_animation_states_and_draw(self):
        """Test that Player advances animation frames and renders without error across all states."""
        mgr = SpriteManager()
        player = Player(player_id=0, spawn_x=100, spawn_y=100, team=0, is_bot=False)
        test_surf = pygame.Surface((480, 320), pygame.SRCALPHA)

        # Test idle
        player.is_grounded = True
        player.vx = 0.0
        player.vy = 0.0
        player._update_animation(0.2)
        self.assertEqual(player.anim_state, "idle")
        player.draw(test_surf, mgr)

        # Test walk
        player.vx = 80.0
        player._update_animation(0.1)
        self.assertEqual(player.anim_state, "walk")
        player.draw(test_surf, mgr)

        # Test jump
        player.is_grounded = False
        player.vy = -150.0
        player._update_animation(0.1)
        self.assertEqual(player.anim_state, "jump")
        player.draw(test_surf, mgr)

        # Test fall
        player.vy = 150.0
        player._update_animation(0.1)
        self.assertEqual(player.anim_state, "fall")
        player.draw(test_surf, mgr)

        # Test shoot
        player.shoot_anim_timer = 0.2
        player._update_animation(0.05)
        self.assertEqual(player.anim_state, "shoot")
        player.draw(test_surf, mgr)

        # Test bubble ride
        player.shoot_anim_timer = 0.0
        player.bubble_ride_timer = 0.3
        player._update_animation(0.05)
        self.assertEqual(player.anim_state, "bubble_ride")
        player.draw(test_surf, mgr)

        # Test pop death
        player.is_alive = False
        player.respawn_timer = 3.0
        player._update_animation(0.2)
        self.assertEqual(player.anim_state, "pop_death")
        player.draw(test_surf, mgr)

if __name__ == "__main__":
    unittest.main()
