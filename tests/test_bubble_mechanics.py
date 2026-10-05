"""
tests/test_bubble_mechanics.py - Unit tests for bubble trampoline bouncing,
vertical bubble climbing, and trapped player retention (preventing self-break).
"""
import unittest
import pygame
from constants import (
    BUBBLE_BOUNCE_SPEED, BUBBLE_TRAPPED_LIFESPAN, MODE_FFA, MODE_TEAM,
    VIRTUAL_WIDTH, VIRTUAL_HEIGHT
)
from entities.player import Player
from entities.bubble import Bubble
from entities.trapped_bubble import TrappedBubble
from engine.game import GameEngine

class TestBubbleMechanics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)

    def test_trapped_player_cannot_self_break(self):
        """A trapped player (human or bot) cannot break their own bubble by struggling or popping."""
        p0 = Player(player_id=0, spawn_x=100, spawn_y=100, team=0, is_bot=True)
        tb = TrappedBubble(p0, captor_id=1, captor_team=1)

        self.assertTrue(p0.is_trapped)
        self.assertTrue(tb.is_alive)
        self.assertEqual(p0.vx, 0.0)
        self.assertEqual(p0.vy, 0.0)

        # Mash struggle 50 times
        for _ in range(50):
            tb.register_struggle()

        # Update bubble for 0.5 seconds
        for _ in range(30):
            tb.update(0.016, [])

        # Player MUST still be trapped; bubble MUST still be alive!
        self.assertTrue(p0.is_trapped, "Trapped player should not self-escape via struggle")
        self.assertTrue(tb.is_alive, "Trapped bubble should not break from trapped player struggle")

        # The trapped player cannot pop their own bubble
        pop_res = tb.check_pop_by_player(p0)
        self.assertIsNone(pop_res, "Trapped player cannot pop their own bubble")
        self.assertTrue(tb.is_alive)
        self.assertTrue(p0.is_trapped)

    def test_trapped_player_popped_by_opponent(self):
        """An opponent touching the trapped bubble eliminates the player and awards points."""
        p_trapped = Player(player_id=1, spawn_x=100, spawn_y=100, team=1)
        p_opponent = Player(player_id=0, spawn_x=100, spawn_y=100, team=0)
        tb = TrappedBubble(p_trapped, captor_id=0, captor_team=0)

        res = tb.check_pop_by_player(p_opponent, is_team_mode=True)
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "KILL")
        self.assertEqual(res[1], 1000)
        self.assertFalse(tb.is_alive)
        self.assertFalse(p_trapped.is_trapped)
        self.assertFalse(p_trapped.is_alive)

    def test_trapped_player_rescued_by_teammate(self):
        """A teammate touching the trapped bubble frees the player with a shield."""
        p_trapped = Player(player_id=1, spawn_x=100, spawn_y=100, team=0)
        p_teammate = Player(player_id=2, spawn_x=100, spawn_y=100, team=0)
        tb = TrappedBubble(p_trapped, captor_id=3, captor_team=1)

        res = tb.check_pop_by_player(p_teammate, is_team_mode=True)
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "RESCUE")
        self.assertEqual(res[1], 500)
        self.assertFalse(tb.is_alive)
        self.assertFalse(p_trapped.is_trapped)
        self.assertTrue(p_trapped.is_alive)
        self.assertGreater(p_trapped.invulnerable_timer, 0.0)

    def test_empty_bubble_trampoline_bounce_does_not_break(self):
        """Landing on an empty bubble bounces the player upward without breaking the bubble."""
        p = Player(player_id=0, spawn_x=100, spawn_y=90)
        b = Bubble(x=100, y=110, direction=1, owner_id=0, owner_team=0)
        b.is_floating = True

        # Player is falling down onto the bubble
        p.vy = 120.0
        p.rect.bottom = b.rect.top - 1
        p.update(0.016, [], [b], [])

        # Verify player bounced
        self.assertLess(p.vy, 0.0, "Player should bounce upward off the bubble")
        self.assertEqual(p.vy, BUBBLE_BOUNCE_SPEED)
        # CRITICAL: The bubble must still be alive!
        self.assertTrue(b.is_alive, "Empty bubble must NOT break when jumped on")

        # Simulate subsequent frame where player is moving upward: bubble must still be alive
        p.update(0.016, [], [b], [])
        self.assertTrue(b.is_alive, "Bubble must not break during player upward ascent")

    def test_boosted_super_bounce_when_holding_jump(self):
        """Holding or buffering jump when bouncing off a bubble provides a super-bounce."""
        p = Player(player_id=0, spawn_x=100, spawn_y=90)
        b = Bubble(x=100, y=110, direction=1, owner_id=0, owner_team=0)
        b.is_floating = True

        p.is_jump_held = True
        p.vy = 80.0
        p.rect.bottom = b.rect.top - 1
        p.update(0.016, [], [b], [])

        expected_boost = BUBBLE_BOUNCE_SPEED * 1.15
        self.assertAlmostEqual(p.vy, expected_boost, places=2)
        self.assertTrue(b.is_alive, "Bubble must remain alive after super-bounce")

    def test_vertical_bubble_climbing(self):
        """Player can jump through lower bubbles and climb a vertical column to the top without breaking bubbles."""
        p = Player(player_id=0, spawn_x=100, spawn_y=190)
        b1 = Bubble(x=100, y=200, direction=1, owner_id=0, owner_team=0)
        b2 = Bubble(x=100, y=140, direction=1, owner_id=0, owner_team=0)
        b3 = Bubble(x=100, y=80, direction=1, owner_id=0, owner_team=0)
        for b in (b1, b2, b3):
            b.is_floating = True

        bubbles = [b1, b2, b3]

        # 1. Player lands on b1
        p.vy = 100.0
        p.rect.bottom = b1.rect.top - 1
        p.is_jump_held = True
        p.update(0.016, [], bubbles, [])
        self.assertLess(p.vy, 0.0)
        self.assertTrue(b1.is_alive)

        # 2. Player ascends towards b2 (vy < -50, ascending from below)
        # Verify passing through b2 from below does not break b2
        p.y = 150
        p.vy = -200.0
        p._update_rect()
        p.update(0.016, [], bubbles, [])
        self.assertTrue(b2.is_alive, "Rising through bubble from below must not pop it")

        # 3. Player reaches apex above b2 and lands on b2
        p.y = 130
        p.vy = 10.0
        p.rect.bottom = b2.rect.top - 1
        p.is_jump_held = True
        p.update(0.016, [], bubbles, [])
        self.assertLess(p.vy, 0.0)
        self.assertTrue(b2.is_alive, "b2 must remain alive after bounce")

        # 4. Player ascends to b3 and lands on b3
        p.y = 70
        p.vy = 10.0
        p.rect.bottom = b3.rect.top - 1
        p.update(0.016, [], bubbles, [])
        self.assertLess(p.vy, 0.0)
        self.assertTrue(b3.is_alive, "b3 must remain alive after bounce")

        # All 3 bubbles must remain completely intact!
        for b in (b1, b2, b3):
            self.assertTrue(b.is_alive, "All stacked bubbles must remain alive")

    def test_engine_trapped_bot_retention_over_time(self):
        """GameEngine update loop keeps trapped bots inside bubble without self-escaping."""
        engine = GameEngine(is_bot_match=True)
        engine.start_match(use_random_map=False)

        # Player 1 is a bot
        bot = engine.players[1]
        self.assertTrue(bot.is_bot)

        # Trap Player 1
        tb = TrappedBubble(bot, captor_id=0, captor_team=0)
        engine.trapped_bubbles.append(tb)

        # Run 60 frames (1 full second) of GameEngine update
        for _ in range(60):
            engine.update(0.016)

        # Bot MUST still be trapped!
        self.assertTrue(bot.is_trapped, "Bot should stay trapped in GameEngine update loop")
        self.assertTrue(tb.is_alive, "Trapped bubble must remain alive in GameEngine update loop")
        self.assertIn(tb, engine.trapped_bubbles)

    def test_floating_bubble_never_traps_players(self):
        """Floating bubbles (Phase 2, moving upwards) never trap players upon collision."""
        engine = GameEngine(is_bot_match=False)
        engine.start_match(use_random_map=False)
        p0 = engine.players[0]
        p1 = engine.players[1]
        p0.x, p0.y = 100, 100
        p1.x, p1.y = 100, 100
        p0._update_rect()
        p1._update_rect()

        # Create a floating bubble at p1's position
        b = Bubble(x=100, y=100, direction=1, owner_id=p0.id, owner_team=p0.team)
        b.is_floating = True  # Phase 2: buoyant upward drift
        engine.bubbles.append(b)

        # Update engine
        engine.update(0.016)

        # p1 MUST NOT be trapped by floating bubble
        self.assertFalse(p1.is_trapped, "Floating bubbles must never trap players")
        self.assertEqual(len(engine.trapped_bubbles), 0)

    def test_back_shield_pops_bubble_without_trapping(self):
        """When an incoming horizontal bubble hits a player's back, the bubble pops and the player is shielded."""
        engine = GameEngine(is_bot_match=False)
        engine.start_match(use_random_map=False)
        p0 = engine.players[0]
        p1 = engine.players[1]
        p0.invulnerable_timer = 0.0
        p1.invulnerable_timer = 0.0

        # p1 is facing Right (+1)
        p1.facing = 1
        p1.x, p1.y = 150, 100
        p1._update_rect()

        # p0 fires a bubble towards the Right (+1), approaching p1 from behind
        b = Bubble(x=145, y=100, direction=1, owner_id=p0.id, owner_team=p0.team)
        b.is_floating = False  # Phase 1: horizontal burst
        engine.bubbles.append(b)

        engine.update(0.016)

        # The bubble should have popped upon hitting p1's back shield!
        self.assertFalse(p1.is_trapped, "Player back shield should protect from entrapment")
        self.assertEqual(len(engine.trapped_bubbles), 0)
        self.assertFalse(b.is_alive, "Bubble must pop upon hitting the player's back shield")

    def test_front_hit_traps_player(self):
        """When an incoming horizontal bubble hits a player from the front, the player gets trapped."""
        engine = GameEngine(is_bot_match=False)
        engine.start_match(use_random_map=False)
        p0 = engine.players[0]
        p1 = engine.players[1]
        p0.invulnerable_timer = 0.0
        p1.invulnerable_timer = 0.0

        # p1 is facing Left (-1), directly facing the incoming bubble from p0
        p1.facing = -1
        p1.x, p1.y = 150, 100
        p1._update_rect()

        # p0 fires a bubble towards the Right (+1)
        b = Bubble(x=145, y=100, direction=1, owner_id=p0.id, owner_team=p0.team)
        b.is_floating = False
        engine.bubbles.append(b)

        engine.update(0.016)

        # p1 should now be trapped!
        self.assertTrue(p1.is_trapped, "Player hit from front should be trapped")
        self.assertEqual(len(engine.trapped_bubbles), 1)

    def test_trapped_bubble_struggle_timing(self):
        """Struggling speeds up popping up to 50% (min 8s), while inactive trapped bubble lasts 16s."""
        # 1. Active struggle case
        p_active = Player(player_id=0, spawn_x=100, spawn_y=100)
        tb_active = TrappedBubble(p_active, captor_id=1, captor_team=1)

        # Simulate 7.5 seconds with heavy mashing
        for sec in range(75):
            for _ in range(5):
                tb_active.register_struggle()
            tb_active.update(0.1, [])

        # At 7.5 seconds (< 8.0s min), player must STILL be trapped despite heavy mashing!
        self.assertTrue(p_active.is_trapped, "Bubble cannot pop before 8s minimum duration")
        self.assertTrue(tb_active.is_alive)

        # Advance past 8.0 seconds (e.g. 8.1s)
        for _ in range(6):
            tb_active.register_struggle()
            tb_active.update(0.1, [])

        # At 8.1s with heavy mashing, bubble should pop and free the player!
        self.assertFalse(tb_active.is_alive, "Bubble should pop after 8s of active struggle")
        self.assertFalse(p_active.is_trapped, "Player should be freed after 8s of struggle")

        # 2. Inactive case (no struggle)
        p_passive = Player(player_id=1, spawn_x=100, spawn_y=100)
        tb_passive = TrappedBubble(p_passive, captor_id=0, captor_team=0)

        # Update without struggle for 10 seconds
        for _ in range(100):
            tb_passive.update(0.1, [])

        # At 10 seconds without struggle, still trapped!
        self.assertTrue(p_passive.is_trapped, "Passive player remains trapped past 10 seconds")
        self.assertTrue(tb_passive.is_alive)

        # Advance to 16.5 seconds
        for _ in range(65):
            tb_passive.update(0.1, [])

        # At 16.5 seconds, naturally expires and frees player
        self.assertFalse(tb_passive.is_alive, "Bubble naturally pops after 16s")
        self.assertFalse(p_passive.is_trapped, "Player naturally freed after 16s")

    def test_continuous_unlimited_bubble_jumping(self):
        """Player can bounce repeatedly 20+ times on floating bubbles without any jump limit."""
        p = Player(player_id=0, spawn_x=100, spawn_y=90)
        b = Bubble(x=100, y=110, direction=1, owner_id=0, owner_team=0)
        b.is_floating = True

        # Perform 20 consecutive bounces
        for i in range(20):
            p.vy = 80.0
            p.rect.bottom = b.rect.top - 1
            p.is_jump_held = True
            p.update(0.016, [], [b], [])
            self.assertLess(p.vy, 0.0, f"Bounce {i+1} must propel player upward")
            self.assertTrue(b.is_alive, f"Bubble must stay intact after bounce {i+1}")

if __name__ == "__main__":
    unittest.main()
