"""
tests/test_platform_edge.py - Verifies that players properly fall off platform edges and never float in air.
"""
import unittest
import pygame
from entities.player import Player
from entities.platform import Platform

class TestPlatformEdgeCollision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)

    def test_player_lands_when_feet_are_on_platform(self):
        """Player should land securely when standing squarely on a platform."""
        plat = Platform(x=100, y=100, width=16, height=16, is_oneway=True)
        player = Player(player_id=0, spawn_x=108, spawn_y=90)
        player.rect.bottom = 101
        prev_bottom = 98
        player.vy = 20.0
        
        # Center x is 108 (inside plat [100:116]) -> Should land!
        self.assertTrue(plat.check_player_landing(prev_bottom, player.rect, player.vy))

    def test_player_falls_when_center_is_past_platform_edge(self):
        """Player should NOT land and should fall when past the platform edge in empty air."""
        plat = Platform(x=100, y=100, width=16, height=16, is_oneway=True)
        
        # Player center x is 120 (past platform right edge 116)
        player = Player(player_id=0, spawn_x=120, spawn_y=90)
        player.rect.bottom = 101
        prev_bottom = 98
        player.vy = 20.0
        
        # Should NOT land!
        self.assertFalse(plat.check_player_landing(prev_bottom, player.rect, player.vy))

    def test_player_ledge_falloff_simulation(self):
        """Simulate walking off a ledge: player must become airborne (is_grounded=False) and fall."""
        plat = Platform(x=100, y=100, width=16, height=16, is_oneway=True)
        platforms = [plat]
        
        # Start standing on platform
        player = Player(player_id=0, spawn_x=108, spawn_y=92)
        player.is_grounded = True
        player.vy = 0.0
        
        # Walk right past platform edge
        player.vx = 80.0
        dt = 0.1  # moves by 8px -> x = 116 (right at edge)
        player.update(dt, platforms, [], [])
        
        # Walk further into empty air
        dt = 0.1  # moves by 8px -> x = 124 (completely off platform)
        player.update(dt, platforms, [], [])
        
        self.assertFalse(player.is_grounded, "Player should be airborne after walking off ledge")
        self.assertGreater(player.vy, 0.0, "Player should have downward falling velocity")
        self.assertEqual(player.anim_state, "fall", "Player animation state should be 'fall'")

if __name__ == "__main__":
    unittest.main()
