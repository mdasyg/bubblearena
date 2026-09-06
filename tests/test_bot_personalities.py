"""
tests/test_bot_personalities.py - Unit tests for CPU bot personalities (Aggressive, Passive, Standard),
game-mode tactics (FFA, Team, CTF), and bonus utility appraisal.
"""
import unittest
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)

from constants import (
    BOT_PERSONALITY_AGGRESSIVE, BOT_PERSONALITY_PASSIVE, BOT_PERSONALITY_STANDARD,
    MODE_FFA, MODE_TEAM, MODE_CTF,
    POWERUP_SHIELD, POWERUP_PURPLE_CANDY, POWERUP_APPLE, POWERUP_DIAMOND
)
from entities.player import Player
from entities.powerup import PowerUp
from entities.flag import Flag
from entities.trapped_bubble import TrappedBubble
from engine.bot_ai import BotAI, ITEM_UTILITY

class TestBotPersonalities(unittest.TestCase):
    def setUp(self):
        self.bot_agg = Player(player_id=1, spawn_x=100, spawn_y=100, team=1, is_bot=True, personality=BOT_PERSONALITY_AGGRESSIVE)
        self.bot_pas = Player(player_id=2, spawn_x=200, spawn_y=100, team=0, is_bot=True, personality=BOT_PERSONALITY_PASSIVE)
        self.bot_std = Player(player_id=3, spawn_x=300, spawn_y=100, team=1, is_bot=True, personality=BOT_PERSONALITY_STANDARD)

    def test_personality_initialization(self):
        """Verify bot personalities are correctly stored and reflected in player name."""
        self.assertEqual(self.bot_agg.personality, BOT_PERSONALITY_AGGRESSIVE)
        self.assertIn("Aggressive", self.bot_agg.name)
        self.assertEqual(self.bot_pas.personality, BOT_PERSONALITY_PASSIVE)
        self.assertIn("Passive", self.bot_pas.name)
        self.assertEqual(self.bot_std.personality, BOT_PERSONALITY_STANDARD)
        self.assertIn("Standard", self.bot_std.name)

    def test_bonus_appraisal_aggressive_skips_during_combat(self):
        """Aggressive bot must skip bonus if an urgent combat target exists."""
        shield = PowerUp(120, 100, item_type=POWERUP_SHIELD)
        all_players = [self.bot_agg]
        
        # When urgent combat target is present, Aggressive skips bonus
        chosen = BotAI.evaluate_best_bonus(self.bot_agg, [shield], all_players, has_urgent_combat_target=True)
        self.assertIsNone(chosen)

        # When no urgent combat target, Aggressive pursues high-utility combat item
        chosen = BotAI.evaluate_best_bonus(self.bot_agg, [shield], all_players, has_urgent_combat_target=False)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.item_type, POWERUP_SHIELD)

    def test_bonus_appraisal_passive_avoids_danger(self):
        """Passive bot must skip bonus if an enemy is camping near the item."""
        shield = PowerUp(210, 100, item_type=POWERUP_SHIELD)
        enemy = Player(player_id=0, spawn_x=220, spawn_y=100, team=1, is_bot=False)
        
        # Enemy is within 75px of the shield -> Passive bot skips it for safety
        chosen = BotAI.evaluate_best_bonus(self.bot_pas, [shield], [self.bot_pas, enemy])
        self.assertIsNone(chosen)

        # Enemy is far away (300px) -> Passive bot grabs shield
        enemy.x = 450
        chosen = BotAI.evaluate_best_bonus(self.bot_pas, [shield], [self.bot_pas, enemy])
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.item_type, POWERUP_SHIELD)

    def test_bonus_appraisal_standard_ignores_distant_low_tier(self):
        """Standard bot evaluates utility vs distance: ignores distant low-tier items."""
        apple = PowerUp(250, 100, item_type=POWERUP_APPLE) # 50px away, low tier
        diamond = PowerUp(400, 100, item_type=POWERUP_DIAMOND) # 100px away, high tier (80 utility)
        
        # Diamond has high utility and is within 210px -> chosen over low-tier apple
        chosen = BotAI.evaluate_best_bonus(self.bot_std, [apple, diamond], [self.bot_std])
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.item_type, POWERUP_DIAMOND)

    def test_ctf_retrieval_strategy_when_flag_stolen(self):
        """In CTF, when an enemy carries the flag, bots must target the carrier to retrieve it."""
        enemy_carrier = Player(player_id=0, spawn_x=50, spawn_y=100, team=0)
        flag = Flag(50, 100)
        flag.carrier = enemy_carrier

        # Bot is Team 1 -> enemy has flag!
        action = BotAI.decide_action(
            self.bot_agg, dt=0.016, all_players=[self.bot_agg, enemy_carrier],
            bubbles=[], trapped_bubbles=[], flag=flag, game_mode=MODE_CTF
        )
        # Bot should steer left towards enemy carrier at x=50
        self.assertTrue(action["left"])
        self.assertTrue(action["shoot"])

    def test_ctf_home_delivery_when_bot_has_flag(self):
        """In CTF, when the bot holds the flag, it must steer towards its home spawn point."""
        flag = Flag(self.bot_agg.x, self.bot_agg.y)
        flag.carrier = self.bot_agg
        self.bot_agg.x = 300
        self.bot_agg.spawn_x = 40  # Home base is to the left

        action = BotAI.decide_action(
            self.bot_agg, dt=0.016, all_players=[self.bot_agg],
            bubbles=[], trapped_bubbles=[], flag=flag, game_mode=MODE_CTF
        )
        # Should steer left towards home spawn point
        self.assertTrue(action["left"])

    def test_team_rescue_priority_for_passive_bot(self):
        """In 2v2 Team Mode, Passive bot prioritizes rescuing a trapped teammate."""
        ally = Player(player_id=0, spawn_x=50, spawn_y=100, team=0) # Same team as bot_pas
        tb_ally = TrappedBubble(trapped_player=ally, captor_id=1, captor_team=1)
        tb_ally.x = 50
        tb_ally.y = 100

        action = BotAI.decide_action(
            self.bot_pas, dt=0.016, all_players=[self.bot_pas, ally],
            bubbles=[], trapped_bubbles=[tb_ally], game_mode=MODE_TEAM
        )
        # bot_pas is at x=200, ally is at x=50 -> steer left to rescue!
        self.assertTrue(action["left"])

    def test_passive_bot_flees_from_close_enemy(self):
        """Passive bot flees away when an active enemy is right next to it."""
        enemy = Player(player_id=0, spawn_x=190, spawn_y=100, team=1) # 10px to left of bot_pas (at 200)
        action = BotAI.decide_action(
            self.bot_pas, dt=0.016, all_players=[self.bot_pas, enemy],
            bubbles=[], trapped_bubbles=[], game_mode=MODE_FFA
        )
        # Bot should flee right (away from enemy on the left)
        self.assertTrue(action["right"])
        # Should also provide defensive covering fire
        self.assertTrue(action["shoot"])

if __name__ == "__main__":
    unittest.main()
