"""
tests/test_lan_lobby.py - Unit tests for LAN interface selection, 4-player ready lobby, broadcast chat, and trapped bubble pop state.
"""
import unittest
import pygame

# Initialize minimal pygame headless display for testing
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)

from network.lan_server import LANServer, get_available_network_interfaces
from network.lan_client import LANClient
from network.protocol import encode_packet, parse_packets, MSG_CHAT, MSG_READY_TOGGLE
from entities.player import Player
from entities.bubble import Bubble
from entities.trapped_bubble import TrappedBubble
from engine.game import GameEngine

class TestLANLobbyAndBugfixes(unittest.TestCase):
    def test_network_interface_detection(self):
        """Interface enumeration must return valid IPv4 strings containing at least one IP."""
        ifaces = get_available_network_interfaces()
        self.assertIsInstance(ifaces, list)
        self.assertGreater(len(ifaces), 0)
        # Verify IPv4 formatting
        for ip in ifaces:
            parts = ip.split(".")
            self.assertEqual(len(parts), 4, f"Invalid IPv4 format: {ip}")
            for p in parts:
                self.assertTrue(p.isdigit(), f"Non-digit octet in {ip}")

    def test_server_custom_interface_binding(self):
        """LANServer must bind and report the user-selected network interface."""
        ifaces = get_available_network_interfaces()
        chosen_ip = ifaces[0]
        server = LANServer(selected_ip=chosen_ip)
        self.assertEqual(server.get_local_ip(), chosen_ip)

        # Test setting alternative IP
        if len(ifaces) > 1:
            server.set_selected_ip(ifaces[1])
            self.assertEqual(server.get_local_ip(), ifaces[1])

    def test_lobby_ready_state_machine(self):
        """Lobby must not report all ready until all 4 slots are filled and marked ready."""
        server = LANServer()
        # Initially Host is not ready, slots 1-3 are open
        self.assertFalse(server.is_all_players_ready())

        # Host toggles ready
        server.toggle_host_ready()
        self.assertTrue(server.lobby_slots[0]["ready"])
        # Still not ready because slots 1-3 are open
        self.assertFalse(server.is_all_players_ready())

        # Fill with bots (bots are auto-ready)
        server.fill_all_bots()
        self.assertEqual(server.lobby_slots[1]["type"], "bot")
        self.assertEqual(server.lobby_slots[2]["type"], "bot")
        self.assertEqual(server.lobby_slots[3]["type"], "bot")

        # Now all 4 slots are occupied and ready
        self.assertTrue(server.is_all_players_ready())

    def test_lobby_broadcast_chat(self):
        """Lobby chat messages must be recorded in chat history."""
        server = LANServer()
        self.assertEqual(len(server.chat_history), 0)

        server.send_host_chat("Hello LAN Arena!")
        self.assertEqual(len(server.chat_history), 1)
        self.assertEqual(server.chat_history[0]["sender"], "Host (P1)")
        self.assertEqual(server.chat_history[0]["message"], "Hello LAN Arena!")

    def test_trapped_bubble_pop_clears_player_trapped_state(self):
        """Popping a trapped bubble (either directly or via chain pop) MUST clear player.is_trapped."""
        opponent = Player(player_id=1, spawn_x=100, spawn_y=100, team=1)
        tb = TrappedBubble(trapped_player=opponent, captor_id=0, captor_team=0)

        self.assertTrue(opponent.is_trapped)
        self.assertTrue(tb.is_alive)

        # Simulating popping by Player 0 (opponent team in FFA / Team)
        popper = Player(player_id=0, spawn_x=100, spawn_y=100, team=0)
        result = tb.check_pop_by_player(popper, is_team_mode=False, force_pop=True)

        self.assertIsNotNone(result)
        self.assertEqual(result[0], "KILL")
        self.assertFalse(tb.is_alive)
        # CRITICAL BUGFIX VERIFICATION: Player must NEVER remain trapped!
        self.assertFalse(opponent.is_trapped, "Player must not be left in is_trapped=True after bubble pop")
        self.assertFalse(opponent.is_alive, "Eliminated player must have is_alive=False during respawn countdown")

    def test_trapped_bubble_chain_pop_in_engine(self):
        """Engine trigger_chain_pop must properly free or eliminate trapped players in chain explosions."""
        engine = GameEngine(is_bot_match=False)
        engine.start_match(use_random_map=False)

        p0 = engine.players[0]
        p1 = engine.players[1]
        p1.team = 1
        p0.team = 0

        tb = TrappedBubble(trapped_player=p1, captor_id=0, captor_team=0)
        engine.trapped_bubbles.append(tb)

        # Chain pop triggered by p0
        engine.trigger_chain_pop(tb, popping_player=p0)

        self.assertFalse(p1.is_trapped, "Player 1 must be freed from is_trapped state")
        self.assertNotIn(tb, engine.trapped_bubbles, "Popped trapped bubble must be removed from active list")

if __name__ == "__main__":
    unittest.main()
