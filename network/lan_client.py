import socket
import select
import threading
import time
from constants import DEFAULT_PORT, BROADCAST_PORT, DISCOVERY_RESPONSE
from network.protocol import (
    encode_packet, parse_packets, MSG_INPUT, MSG_JOIN_ACCEPT,
    MSG_STATE_SYNC, MSG_READY_TOGGLE, MSG_LOBBY_STATE, MSG_CHAT, MSG_MATCH_START
)

class LANClient:
    """Connects to a LAN host, sends local player controls, and receives replicated state/lobby sync."""
    def __init__(self):
        self.sock = None
        self.assigned_player_id = None
        self.is_connected = False
        self.is_running = False
        self.receive_thread = None
        self.recv_buffer = b""
        self.latest_state = None
        self.lock = threading.Lock()

        # Lobby State
        self.lobby_slots = {
            0: {"name": "Host (P1)", "type": "human", "ready": False},
            1: {"name": "Open Slot", "type": "open", "ready": False},
            2: {"name": "Open Slot", "type": "open", "ready": False},
            3: {"name": "Open Slot", "type": "open", "ready": False},
        }
        self.chat_history = []
        self.match_started = False
        self.host_ip = ""
        self.host_port = DEFAULT_PORT

    @staticmethod
    def discover_hosts(timeout=2.0):
        """Listens for UDP host discovery broadcasts on LAN."""
        found_hosts = []
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(timeout)
        try:
            sock.bind(("", BROADCAST_PORT))
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data, addr = sock.recvfrom(1024)
                    text = data.decode('utf-8')
                    if text.startswith(DISCOVERY_RESPONSE):
                        parts = text.split(":")
                        if len(parts) >= 3:
                            host_ip = parts[1]
                            host_port = int(parts[2])
                            if (host_ip, host_port) not in found_hosts:
                                found_hosts.append((host_ip, host_port))
                except socket.timeout:
                    break
                except Exception:
                    pass
        except Exception as e:
            print(f"[LANClient] Discovery error: {e}")
        finally:
            sock.close()
        return found_hosts

    def connect(self, host_ip, port=DEFAULT_PORT):
        """Establishes TCP connection to LAN host."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(4.0)
            self.sock.connect((host_ip, port))
            self.sock.setblocking(False)
            self.is_connected = True
            self.is_running = True
            self.match_started = False
            self.host_ip = host_ip
            self.host_port = port

            self.receive_thread = threading.Thread(target=self._run_receiver, daemon=True)
            self.receive_thread.start()
            print(f"[LANClient] Connected to {host_ip}:{port}")
            return True
        except Exception as e:
            print(f"[LANClient] Connection failed: {e}")
            self.is_connected = False
            return False

    def _run_receiver(self):
        """Continuously reads incoming state packets and lobby messages from host."""
        while self.is_running and self.is_connected:
            try:
                readable, _, _ = select.select([self.sock], [], [], 0.05)
                if readable:
                    data = self.sock.recv(4096)
                    if not data:
                        self.is_connected = False
                        break
                    self.recv_buffer += data
                    packets, remainder = parse_packets(self.recv_buffer)
                    self.recv_buffer = remainder

                    for pkt in packets:
                        p_type = pkt.get("type")
                        payload = pkt.get("payload", {})
                        if p_type == MSG_JOIN_ACCEPT:
                            self.assigned_player_id = payload.get("player_id")
                            print(f"[LANClient] Joined as Player {self.assigned_player_id + 1}")
                        elif p_type == MSG_LOBBY_STATE:
                            with self.lock:
                                slots = payload.get("slots", {})
                                for k, v in slots.items():
                                    self.lobby_slots[int(k)] = v
                                self.host_ip = payload.get("host_ip", self.host_ip)
                        elif p_type == MSG_CHAT:
                            with self.lock:
                                self.chat_history.append(payload)
                                if len(self.chat_history) > 30:
                                    self.chat_history.pop(0)
                        elif p_type == MSG_MATCH_START:
                            with self.lock:
                                self.match_started = True
                        elif p_type == MSG_STATE_SYNC:
                            with self.lock:
                                self.latest_state = payload
            except Exception as e:
                if self.is_running:
                    print(f"[LANClient] Receiver notice: {e}")
                self.is_connected = False
                break

    def send_input(self, actions_dict):
        """Sends local player's input dictionary to host."""
        if not self.is_connected or not self.sock:
            return
        try:
            packet = encode_packet(MSG_INPUT, actions_dict)
            self.sock.sendall(packet)
        except Exception:
            self.is_connected = False

    def send_ready_toggle(self, is_ready=None):
        """Sends ready status toggle to host."""
        if not self.is_connected or not self.sock:
            return
        try:
            packet = encode_packet(MSG_READY_TOGGLE, {"ready": is_ready})
            self.sock.sendall(packet)
        except Exception:
            self.is_connected = False

    def send_chat(self, text):
        """Sends chat message to host to broadcast."""
        if not self.is_connected or not self.sock:
            return
        try:
            packet = encode_packet(MSG_CHAT, {"message": text})
            self.sock.sendall(packet)
        except Exception:
            self.is_connected = False

    def get_latest_state(self):
        """Returns the most recent replicated game state."""
        with self.lock:
            return self.latest_state

    def get_lobby_slots(self):
        """Returns the current lobby slots snapshot."""
        with self.lock:
            return dict(self.lobby_slots)

    def get_chat_history(self):
        """Returns the chat log."""
        with self.lock:
            return list(self.chat_history)

    def is_match_started(self):
        """Checks whether the host triggered match start."""
        with self.lock:
            return self.match_started

    def disconnect(self):
        """Closes connection."""
        self.is_running = False
        self.is_connected = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
