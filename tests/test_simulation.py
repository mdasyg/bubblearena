"""
tests/test_simulation.py - Headless 200-frame simulation of active gameplay across all 3 game modes.
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import unittest
import pygame
from engine.game import GameEngine
from constants import MODE_FFA, MODE_TEAM, MODE_CTF

class TestGameSimulation(unittest.TestCase):
    def test_full_match_simulation(self):
        """Simulates 150 frames of active match in FFA, 2v2 Team, and CTF modes."""
        engine = GameEngine(is_bot_match=True)

        for mode in [MODE_FFA, MODE_TEAM, MODE_CTF]:
            engine.set_game_mode(mode)
            engine.start_match()
            self.assertEqual(engine.state, 4)  # STATE_PLAYING

            # Simulate 150 frames with delta time
            for frame in range(150):
                engine.update(0.016)
                engine.render(0.016)

            # Ensure players and HUD updated smoothly
            self.assertEqual(len(engine.players), 4)

if __name__ == "__main__":
    unittest.main()
