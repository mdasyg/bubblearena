"""
tests/test_settings_and_audio.py - Automated unit tests for audio settings, volume controls,
minimum stage duration, round time limit, and bot personality configurations.
"""
import unittest
import os
import pygame

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
pygame.init()

from constants import (
    STATE_SETTINGS, STATE_MENU, SPEED_OPTIONS,
    MUSIC_VOLUME_OPTIONS, SFX_VOLUME_OPTIONS,
    MIN_DURATION_OPTIONS, ROUND_TIMER_OPTIONS, BOT_PREFERENCE_OPTIONS,
    BOT_PERSONALITY_AGGRESSIVE, BOT_PERSONALITY_PASSIVE, BOT_PERSONALITY_STANDARD,
    MODE_FFA, MODE_TEAM, MODE_CTF
)
from engine.sound import SoundManager
from engine.game import GameEngine
from modes.base_mode import BaseGameMode
from modes.ffa_mode import FFAMode
from modes.team_mode import TeamMode
from modes.ctf_mode import CTFMode
from entities.player import Player
from entities.trapped_bubble import TrappedBubble

class TestSettingsAndAudio(unittest.TestCase):
    def setUp(self):
        self.sound_mgr = SoundManager()

    def test_music_volume_levels_and_mute(self):
        """Verify music volume setter clamps, mutes at 0.0, and un-mutes cleanly."""
        self.assertEqual(self.sound_mgr.music_volume, 1.0)

        # Set to low volume (35%)
        self.sound_mgr.set_music_volume(0.35)
        self.assertAlmostEqual(self.sound_mgr.music_volume, 0.35)

        # Set to mute (0.0)
        self.sound_mgr.set_music_volume(0.0)
        self.assertEqual(self.sound_mgr.music_volume, 0.0)

        # Attempt to start BGM while muted
        self.sound_mgr.start_bgm()
        self.assertTrue(self.sound_mgr.bgm_playing)

        # Restore normal volume
        self.sound_mgr.set_music_volume(1.0)
        self.assertEqual(self.sound_mgr.music_volume, 1.0)

        # Clamping checks
        self.sound_mgr.set_music_volume(-0.5)
        self.assertEqual(self.sound_mgr.music_volume, 0.0)
        self.sound_mgr.set_music_volume(2.5)
        self.assertEqual(self.sound_mgr.music_volume, 1.0)

    def test_sfx_volume_levels_and_mute(self):
        """Verify SFX volume setter clamps and mutes sound effects."""
        self.assertEqual(self.sound_mgr.sfx_volume, 1.0)

        # Low volume
        self.sound_mgr.set_sfx_volume(0.35)
        self.assertAlmostEqual(self.sound_mgr.sfx_volume, 0.35)

        # Mute
        self.sound_mgr.set_sfx_volume(0.0)
        self.assertEqual(self.sound_mgr.sfx_volume, 0.0)

        # play_sfx with volume 0 should safely return without playing
        self.sound_mgr.play_sfx("select")
        self.sound_mgr.play_sfx("pop")

        # Restore
        self.sound_mgr.set_sfx_volume(1.0)
        self.assertEqual(self.sound_mgr.sfx_volume, 1.0)

    def test_configurable_min_round_duration_ffa(self):
        """Verify FFAMode respects custom minimum round duration."""
        # 1. With min_round_duration = 0.0 (None), score limit ends match immediately
        ffa_zero = FFAMode(score_limit=5000, min_round_duration=0.0)
        p1 = Player(player_id=0, spawn_x=100, spawn_y=100)
        p2 = Player(player_id=1, spawn_x=150, spawn_y=100)
        tb = TrappedBubble(trapped_player=p2, captor_id=0, captor_team=0)

        ffa_zero.start_round([p1, p2])
        ffa_zero.round_elapsed_time = 1.0
        ffa_zero.on_player_popped(p1, tb, "KILL", 6000)
        self.assertTrue(ffa_zero.is_match_over, "Match should end immediately when min_duration is 0.0")

        # 2. With min_round_duration = 60.0, score limit is held until 60s
        ffa_sixty = FFAMode(score_limit=5000, min_round_duration=60.0)
        p1_b = Player(player_id=0, spawn_x=100, spawn_y=100)
        p2_b = Player(player_id=1, spawn_x=150, spawn_y=100)
        tb_b = TrappedBubble(trapped_player=p2_b, captor_id=0, captor_team=0)

        ffa_sixty.start_round([p1_b, p2_b])
        ffa_sixty.round_elapsed_time = 45.0
        ffa_sixty.on_player_popped(p1_b, tb_b, "KILL", 6000)
        self.assertFalse(ffa_sixty.is_match_over, "Match must not end before 60s min_duration")

        ffa_sixty.round_elapsed_time = 60.5
        ffa_sixty.on_player_popped(p1_b, tb_b, "KILL", 100)
        self.assertTrue(ffa_sixty.is_match_over, "Match should end once 60s min_duration has elapsed")

    def test_configurable_min_round_duration_team_and_ctf(self):
        """Verify TeamMode and CTFMode respect custom minimum round duration."""
        # CTF Mode
        ctf = CTFMode(score_limit=5000, min_round_duration=30.0)
        p1 = Player(player_id=0, spawn_x=100, spawn_y=100)
        p1.score = 6000
        ctf.start_round([p1])
        p1.score = 6000

        ctf.round_elapsed_time = 15.0
        ctf.update(0.1, [p1])
        self.assertFalse(ctf.is_match_over)

        ctf.round_elapsed_time = 31.0
        ctf.update(0.1, [p1])
        self.assertTrue(ctf.is_match_over)

        # Team Mode
        team = TeamMode(score_limit=5000, min_round_duration=30.0)
        p_team0 = Player(player_id=0, spawn_x=100, spawn_y=100, team=0)
        p_team1 = Player(player_id=1, spawn_x=150, spawn_y=100, team=1)
        team.start_round([p_team0, p_team1])
        p_team0.score = 6000

        team.round_elapsed_time = 15.0
        team.update(0.1, [p_team0, p_team1])
        self.assertFalse(team.is_match_over)

        team.round_elapsed_time = 31.0
        team.update(0.1, [p_team0, p_team1])
        self.assertTrue(team.is_match_over)

    def test_custom_round_match_time(self):
        """Verify custom round time limit sets match duration properly."""
        mode = BaseGameMode("Custom Mode", match_duration=120.0)
        self.assertEqual(mode.match_duration, 120.0)
        self.assertEqual(mode.match_time_remaining, 120.0)

        p1 = Player(player_id=0, spawn_x=100, spawn_y=100)
        mode.start_round([p1])
        self.assertEqual(mode.match_time_remaining, 120.0)

    def test_bot_personality_preference_in_game_engine(self):
        """Verify game engine applies selected bot personality preference to spawned bots."""
        engine = GameEngine(is_bot_match=True)

        # 1. Set bot preference to All Aggressive
        agg_idx = [i for i, opt in enumerate(BOT_PREFERENCE_OPTIONS) if opt[1] == BOT_PERSONALITY_AGGRESSIVE][0]
        engine.bot_personality_idx = agg_idx
        engine.setup_players_by_human_count(1)
        for p in engine.players[1:]:
            self.assertTrue(p.is_bot)
            self.assertEqual(p.personality, BOT_PERSONALITY_AGGRESSIVE)

        # 2. Set bot preference to All Passive
        pas_idx = [i for i, opt in enumerate(BOT_PREFERENCE_OPTIONS) if opt[1] == BOT_PERSONALITY_PASSIVE][0]
        engine.bot_personality_idx = pas_idx
        engine.setup_players_by_human_count(1)
        for p in engine.players[1:]:
            self.assertTrue(p.is_bot)
            self.assertEqual(p.personality, BOT_PERSONALITY_PASSIVE)

        # 3. Set bot preference to All Standard
        std_idx = [i for i, opt in enumerate(BOT_PREFERENCE_OPTIONS) if opt[1] == BOT_PERSONALITY_STANDARD][0]
        engine.bot_personality_idx = std_idx
        engine.setup_players_by_human_count(1)
        for p in engine.players[1:]:
            self.assertTrue(p.is_bot)
            self.assertEqual(p.personality, BOT_PERSONALITY_STANDARD)

    def test_settings_state_navigation_and_rendering(self):
        """Verify settings screen responds to keyboard navigation and renders cleanly."""
        engine = GameEngine()
        engine.state = STATE_SETTINGS
        engine.menu.selected_idx = 0

        # Simulate Down key to step through all 8 options
        down_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        for expected_idx in range(1, 8):
            pygame.event.post(down_event)
            engine.handle_events()
            self.assertEqual(engine.menu.selected_idx, expected_idx)

        # Wrap around back to 0
        pygame.event.post(down_event)
        engine.handle_events()
        self.assertEqual(engine.menu.selected_idx, 0)

        # Test adjusting Music Volume (index 2)
        engine.menu.selected_idx = 2
        right_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
        old_vol_idx = engine.music_vol_idx
        pygame.event.post(right_event)
        engine.handle_events()
        self.assertEqual(engine.music_vol_idx, (old_vol_idx + 1) % len(MUSIC_VOLUME_OPTIONS))

        # Test adjusting Min Duration (index 4)
        engine.menu.selected_idx = 4
        old_dur_idx = engine.min_duration_idx
        pygame.event.post(right_event)
        engine.handle_events()
        self.assertEqual(engine.min_duration_idx, (old_dur_idx + 1) % len(MIN_DURATION_OPTIONS))

        # Test rendering
        test_surface = pygame.Surface((480, 320))
        engine.menu.draw_settings_screen(
            test_surface,
            SPEED_OPTIONS[engine.speed_idx][0],
            engine.total_rounds,
            0.016,
            music_vol_name=MUSIC_VOLUME_OPTIONS[engine.music_vol_idx][0],
            sfx_vol_name=SFX_VOLUME_OPTIONS[engine.sfx_vol_idx][0],
            min_duration_name=MIN_DURATION_OPTIONS[engine.min_duration_idx][0],
            round_timer_name=ROUND_TIMER_OPTIONS[engine.round_timer_idx][0],
            bot_pref_name=BOT_PREFERENCE_OPTIONS[engine.bot_personality_idx][0]
        )
        self.assertEqual(test_surface.get_size(), (480, 320))

if __name__ == "__main__":
    unittest.main()
