"""
tests/test_dedicated_server.py - Comprehensive isolated test suite for bubblearena_server.py.
Validates dedicated server lifecycle, CLI parser, console manager commands, ping latency,
slot assignment, player kicking, IP banning, and headless execution.
"""
import unittest
import socket
import time
import threading
from bubblearena_server import parse_cli_arguments, ConsoleManager
from network.server_core import BaseBubbleServer
from network.lan_client import LANClient
from network.protocol import encode_packet, parse_packets, MSG_PONG, MSG_KICK
from constants import MODE_FFA, MODE_TEAM, MODE_CTF

class TestDedicatedServer(unittest.TestCase):
    """Unit and integration tests for bubblearena_server.py and BaseBubbleServer."""

    def test_cli_argument_parsing(self):
        """CLI parser correctly parses interface, port, mode, level, and flags."""
        args = parse_cli_arguments([
            "-i", "127.0.0.1",
            "-p", "29999",
            "-m", "ctf",
            "-l", "7",
            "--no-beacon",
            "--no-auto-start"
        ])
        self.assertEqual(args.interface, "127.0.0.1")
        self.assertEqual(args.port, 29999)
        self.assertEqual(args.mode, "ctf")
        self.assertEqual(args.level, 7)
        self.assertTrue(args.no_beacon)
        self.assertTrue(args.no_auto_start)

    def test_dedicated_slots_all_open_initially(self):
        """In dedicated server mode, all 4 slots (0..3) must be open for remote players."""
        server = BaseBubbleServer(
            host="127.0.0.1",
            port=29101,
            is_dedicated=True,
            enable_beacon=False,
            auto_start=False
        )
        for i in range(4):
            self.assertEqual(server.lobby_slots[i]["type"], "open")
            self.assertFalse(server.lobby_slots[i]["ready"])
            self.assertEqual(server.lobby_slots[i]["name"], "Open Slot")

    def test_client_join_and_slot_allocation(self):
        """Dedicated server accepts clients and assigns slots starting from 0."""
        server = BaseBubbleServer(
            host="127.0.0.1",
            port=29102,
            is_dedicated=True,
            enable_beacon=False,
            auto_start=False
        )
        server.start()
        try:
            client1 = LANClient()
            self.assertTrue(client1.connect("127.0.0.1", 29102))
            time.sleep(0.3)

            self.assertEqual(client1.assigned_player_id, 0)
            self.assertEqual(server.lobby_slots[0]["type"], "human")
            self.assertEqual(server.lobby_slots[0]["ip"], "127.0.0.1")

            client2 = LANClient()
            self.assertTrue(client2.connect("127.0.0.1", 29102))
            time.sleep(0.3)

            self.assertEqual(client2.assigned_player_id, 1)
            self.assertEqual(server.lobby_slots[1]["type"], "human")

            client1.disconnect()
            client2.disconnect()
            time.sleep(0.3)
        finally:
            server.stop()

    def test_ping_pong_latency_tracking(self):
        """Server measures and records round-trip ping latency from PONG packets."""
        server = BaseBubbleServer(
            host="127.0.0.1",
            port=29103,
            is_dedicated=True,
            enable_beacon=False,
            auto_start=False
        )
        server.start()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("127.0.0.1", 29103))
            time.sleep(0.2)

            # Simulate simulated round-trip time of 42ms
            simulated_t0 = time.time() - 0.042
            pong_pkt = encode_packet(MSG_PONG, {"t0": simulated_t0})
            sock.sendall(pong_pkt)
            time.sleep(0.2)

            # Slot 0 latency should now reflect approximately 42ms
            lat = server.lobby_slots[0]["latency_ms"]
            self.assertGreaterEqual(lat, 30.0)
            self.assertLessEqual(lat, 100.0)

            sock.close()
        finally:
            server.stop()

    def test_console_manager_commands(self):
        """ConsoleManager dispatches status, mode, level, bots, kick, ban, say commands."""
        server = BaseBubbleServer(
            host="127.0.0.1",
            port=29104,
            is_dedicated=True,
            enable_beacon=False,
            auto_start=False
        )
        server.start()
        manager = ConsoleManager(server)
        try:
            # 1. Mode switching
            manager.execute_command("mode team")
            self.assertEqual(server.game_mode_name, MODE_TEAM)
            manager.execute_command("mode ctf")
            self.assertEqual(server.game_mode_name, MODE_CTF)

            # 2. Level switching
            manager.execute_command("level 8")
            self.assertEqual(server.level_idx, 8)

            # 3. Add bot
            manager.execute_command("bot add 2 Aggressive")
            self.assertEqual(server.lobby_slots[1]["type"], "bot")
            self.assertEqual(server.lobby_slots[1]["personality"], "Aggressive")
            self.assertTrue(server.lobby_slots[1]["ready"])

            # 4. Kick bot
            manager.execute_command("bot kick 2")
            self.assertEqual(server.lobby_slots[1]["type"], "open")

            # 5. Fill bots
            manager.execute_command("bots fill")
            for i in range(4):
                self.assertEqual(server.lobby_slots[i]["type"], "bot")

            # 6. Kick player/bot via slot number
            manager.execute_command("kick 1 Test Kick")
            self.assertEqual(server.lobby_slots[0]["type"], "open")

            # 7. Say / Broadcast announcement
            manager.execute_command("say Welcome to the arena!")
            self.assertTrue(any("Welcome to the arena!" in e["message"] for e in server.chat_history))

            # 8. Ban and Unban IP
            manager.execute_command("ban 10.99.99.1")
            self.assertIn("10.99.99.1", server.banned_ips)
            manager.execute_command("unban 10.99.99.1")
            self.assertNotIn("10.99.99.1", server.banned_ips)

            # 9. Autostart toggle
            manager.execute_command("autostart off")
            self.assertFalse(server.auto_start)
            manager.execute_command("autostart on")
            self.assertTrue(server.auto_start)

            # 10. Status report formatting
            status_table = server.format_status_table()
            self.assertIn("BUBBLE ARENA SERVER", status_table)
            self.assertIn("DEDICATED", status_table)

        finally:
            server.stop()

    def test_banned_ip_rejection(self):
        """Dedicated server rejects connections from banned IP addresses immediately."""
        server = BaseBubbleServer(
            host="127.0.0.1",
            port=29105,
            is_dedicated=True,
            enable_beacon=False
        )
        server.start()
        try:
            server.ban_ip("127.0.0.1")
            client = LANClient()
            client.connect("127.0.0.1", 29105)
            time.sleep(0.3)

            # Connection should have been dropped / refused
            self.assertFalse(client.is_connected)
            self.assertEqual(client.kick_reason, "Banned IP address")
            client.disconnect()
        finally:
            server.stop()

    def test_player_kick_with_reason(self):
        """Dedicated server kicks client with kick reason transmitted over protocol."""
        server = BaseBubbleServer(
            host="127.0.0.1",
            port=29106,
            is_dedicated=True,
            enable_beacon=False,
            auto_start=False
        )
        server.start()
        try:
            client = LANClient()
            self.assertTrue(client.connect("127.0.0.1", 29106))
            time.sleep(0.3)
            self.assertEqual(client.assigned_player_id, 0)

            # Kick Player 1 (Slot 0)
            success, msg = server.kick_player(0, reason="AFK for too long")
            self.assertTrue(success)
            time.sleep(0.3)

            # Client should have received kick notice and disconnected
            self.assertFalse(client.is_connected)
            self.assertEqual(client.kick_reason, "AFK for too long")
            self.assertEqual(server.lobby_slots[0]["type"], "open")
            client.disconnect()
        finally:
            server.stop()

if __name__ == "__main__":
    unittest.main()
