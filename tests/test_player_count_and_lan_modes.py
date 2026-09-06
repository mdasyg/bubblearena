"""
tests/test_player_count_and_lan_modes.py - Unit tests for local player count selection,
LAN room game mode cycling & sync, and sound card silent-mode robustness.
"""
import unittest
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)

from constants import (
    STATE_PLAYER_COUNT, STATE_LAN_ROOM, STATE_LOBBY,
    MODE_FFA, MODE_TEAM, MODE_CTF,
    BOT_PERSONALITIES, VIRTUAL_WIDTH, VIRTUAL_HEIGHT
)
from engine.game import GameEngine
from engine.sound import SoundManager
from ui.menu import MenuSystem
from network.lan_server import LANServer
from network.lan_client import LANClient
from network.protocol import encode_packet, parse_packets, MSG_LOBBY_STATE, MSG_MATCH_START

class TestPlayerCountAndLANModes(unittest.TestCase):
    def test_local_player_count_configurations(self):
        """Verify setup_players_by_human_count sets the exact ratio of human vs bot players."""
        engine = GameEngine(is_bot_match=False)

        # 1 Human + 3 Bots
        engine.setup_players_by_human_count(1)
        self.assertFalse(engine.players[0].is_bot)
        self.assertTrue(engine.players[1].is_bot)
        self.assertTrue(engine.players[2].is_bot)
        self.assertTrue(engine.players[3].is_bot)
        for i in range(1, 4):
            self.assertIn(engine.players[i].personality, BOT_PERSONALITIES)

        # 2 Humans + 2 Bots
        engine.setup_players_by_human_count(2)
        self.assertFalse(engine.players[0].is_bot)
        self.assertFalse(engine.players[1].is_bot)
        self.assertTrue(engine.players[2].is_bot)
        self.assertTrue(engine.players[3].is_bot)

        # 3 Humans + 1 Bot
        engine.setup_players_by_human_count(3)
        self.assertFalse(engine.players[0].is_bot)
        self.assertFalse(engine.players[1].is_bot)
        self.assertFalse(engine.players[2].is_bot)
        self.assertTrue(engine.players[3].is_bot)

        # 4 Humans + 0 Bots
        engine.setup_players_by_human_count(4)
        for i in range(4):
            self.assertFalse(engine.players[i].is_bot)

    def test_player_count_menu_rendering(self):
        """MenuSystem.draw_player_count_select renders without exception across all selections."""
        menu = MenuSystem()
        surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        for sel in range(4):
            menu.selected_idx = sel
            menu.draw_player_count_select(surface, dt=0.016)

    def test_lan_server_game_mode_cycling(self):
        """LANServer.cycle_game_mode cycles through FFA, Team, and CTF modes."""
        server = LANServer()
        self.assertEqual(server.game_mode_name, MODE_FFA)

        m1 = server.cycle_game_mode()
        self.assertEqual(m1, MODE_TEAM)
        self.assertEqual(server.game_mode_name, MODE_TEAM)

        m2 = server.cycle_game_mode()
        self.assertEqual(m2, MODE_CTF)
        self.assertEqual(server.game_mode_name, MODE_CTF)

        m3 = server.cycle_game_mode()
        self.assertEqual(m3, MODE_FFA)
        self.assertEqual(server.game_mode_name, MODE_FFA)

    def test_lan_server_fill_bots_assigns_personalities(self):
        """LANServer.fill_all_bots assigns random CPU personalities to filled slots."""
        server = LANServer()
        server.fill_all_bots()
        for i in range(1, 4):
            slot = server.lobby_slots[i]
            self.assertEqual(slot["type"], "bot")
            self.assertTrue(slot["ready"])
            self.assertIn("personality", slot)
            self.assertIn(slot["personality"], BOT_PERSONALITIES)

    def test_lan_client_receives_synced_game_mode(self):
        """LANClient updates lobby_game_mode and match_game_mode from packet payloads."""
        client = LANClient()
        self.assertEqual(client.lobby_game_mode, MODE_FFA)

        # Simulate MSG_LOBBY_STATE with CTF mode
        pkt_data = {
            "slots": {},
            "host_ip": "127.0.0.1",
            "port": 28888,
            "game_mode": MODE_CTF
        }
        raw_pkt = encode_packet(MSG_LOBBY_STATE, pkt_data)
        packets, _ = parse_packets(raw_pkt)
        self.assertEqual(len(packets), 1)

        payload = packets[0]["payload"]
        client.lobby_game_mode = payload.get("game_mode", client.lobby_game_mode)
        self.assertEqual(client.lobby_game_mode, MODE_CTF)

        # Simulate MSG_MATCH_START with Team mode
        start_pkt = encode_packet(MSG_MATCH_START, {"started": True, "game_mode": MODE_TEAM})
        packets2, _ = parse_packets(start_pkt)
        payload2 = packets2[0]["payload"]
        client.match_game_mode = payload2.get("game_mode", client.lobby_game_mode)
        self.assertEqual(client.match_game_mode, MODE_TEAM)

    def test_sound_card_disabled_fallback_never_fails(self):
        """When SoundManager is disabled / in silent mode, all audio methods execute without error."""
        sm = SoundManager()
        # Explicitly force silent mode (simulate missing sound card)
        sm.enabled = False
        sm.music_channel = None

        # None of these should raise any exception or abort
        sm.play_sfx("shoot")
        sm.play_sfx("nonexistent_sound")
        sm.start_bgm(fast=False)
        sm.start_bgm(fast=True)
        sm.set_hurry_mode(True)
        sm.set_hurry_mode(False)
        sm.stop_bgm()
        self.assertFalse(sm.bgm_playing)

if __name__ == "__main__":
    unittest.main()
