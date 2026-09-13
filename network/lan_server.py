"""
network/lan_server.py - Non-blocking LAN listen-host server for Bubble Arena.
Refactored to subclass BaseBubbleServer from network.server_core to eliminate duplication.
"""
from constants import DEFAULT_PORT
from network.server_core import BaseBubbleServer, get_available_network_interfaces

class LANServer(BaseBubbleServer):
    """
    Local listen-host server for Bubble Arena.
    Inherits all core networking, select loops, slot management, and latency tracking from BaseBubbleServer.
    Slot 0 is reserved for the local Host player (P1), and LAN discovery beacon is active.
    """
    def __init__(self, host="0.0.0.0", port=DEFAULT_PORT, selected_ip=None):
        super().__init__(
            host=host,
            port=port,
            selected_ip=selected_ip,
            is_dedicated=False,
            enable_beacon=True,
            auto_start=False  # Listen host waits for synchronized ready countdown in GameEngine
        )

    def toggle_host_ready(self):
        """Toggles ready status for Host (Player 0)."""
        with self.lock:
            self.lobby_slots[0]["ready"] = not self.lobby_slots[0]["ready"]
            self._broadcast_lobby_state_locked()

    def send_host_chat(self, message_text):
        """Sends chat message from Host (P1) to all connected clients."""
        self.send_chat("Host (P1)", message_text, player_id=0)

    def toggle_slot_bot(self, slot_idx):
        """Host action to toggle an open slot between bot and open."""
        with self.lock:
            if slot_idx in (1, 2, 3):
                curr = self.lobby_slots[slot_idx]["type"]
                if curr == "open":
                    self.add_bot(slot_idx=slot_idx, personality="Standard")
                elif curr == "bot":
                    self.kick_bot(slot_idx)
