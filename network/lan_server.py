"""
network/lan_server.py - Non-blocking LAN host server for Bubble Arena.
"""
import socket
import select
import threading
import time
import random
from constants import (
    DEFAULT_PORT, BROADCAST_PORT, DISCOVERY_MAGIC, DISCOVERY_RESPONSE,
    MODE_FFA, MODE_TEAM, MODE_CTF, BOT_PERSONALITIES
)
from network.protocol import (
    encode_packet, parse_packets, MSG_JOIN_REQUEST, MSG_JOIN_ACCEPT,
    MSG_INPUT, MSG_STATE_SYNC, MSG_READY_TOGGLE, MSG_LOBBY_STATE,
    MSG_CHAT, MSG_MATCH_START
)

def get_available_network_interfaces():
    """Returns a sorted list of unique IPv4 addresses available on local network interfaces."""
    interfaces = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip not in interfaces and not ip.startswith('169.254.'):
                interfaces.append(ip)
    except Exception:
        pass

    try:
        _, _, ips = socket.gethostbyname_ex(socket.gethostname())
        for ip in ips:
            if ip not in interfaces and not ip.startswith('169.254.'):
                interfaces.append(ip)
    except Exception:
        pass

    for target in [('8.8.8.8', 80), ('192.168.1.1', 80), ('10.0.0.1', 80), ('1.1.1.1', 80)]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(target)
            ip = s.getsockname()[0]
            s.close()
            if ip not in interfaces and not ip.startswith('169.254.'):
                interfaces.append(ip)
        except Exception:
            pass

    if '127.0.0.1' not in interfaces:
        interfaces.append('127.0.0.1')

    def sort_key(ip):
        if ip.startswith('192.168.'): return 0
        if ip.startswith('10.'): return 1
        if ip.startswith('172.'): return 2
        if ip == '127.0.0.1': return 4
        return 3

    interfaces.sort(key=sort_key)
    return interfaces

class LANServer:
    """Manages LAN hosting, client connections, input ingestion, lobby ready-checks, broadcast chat, and state sync."""
    def __init__(self, host="0.0.0.0", port=DEFAULT_PORT, selected_ip=None):
        self.host = host
        self.port = port
        self.available_interfaces = get_available_network_interfaces()
        self.selected_ip = selected_ip if selected_ip in self.available_interfaces else (
            self.available_interfaces[0] if self.available_interfaces else "127.0.0.1"
        )
        self.server_socket = None
        self.clients = {}  # {client_socket: {"player_id": int, "buffer": b""}}
        self.is_running = False
        self.server_thread = None
        self.beacon_thread = None
        self.latest_client_inputs = {}  # {player_id: action_dict}
        self.lock = threading.Lock()

        # Lobby State Management (Slots 0..3)
        self.lobby_slots = {
            0: {"name": "Host (P1)", "type": "human", "ready": False},
            1: {"name": "Open Slot", "type": "open", "ready": False},
            2: {"name": "Open Slot", "type": "open", "ready": False},
            3: {"name": "Open Slot", "type": "open", "ready": False},
        }
        self.chat_history = []  # [{"sender": str, "message": str, "color": tuple}]
        self.match_started = False
        self.game_mode_name = MODE_FFA

    def get_local_ip(self):
        """Retrieves the user-selected LAN IP address of this machine."""
        return self.selected_ip

    def set_selected_ip(self, ip):
        """Updates the selected interface IP address."""
        if ip in self.available_interfaces:
            self.selected_ip = ip

    def start(self):
        """Starts the server thread and UDP discovery broadcaster."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(4)
        self.server_socket.setblocking(False)

        self.is_running = True
        self.match_started = False
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()

        self.beacon_thread = threading.Thread(target=self._run_discovery_beacon, daemon=True)
        self.beacon_thread.start()
        print(f"[LANServer] Hosting match on interface {self.selected_ip}:{self.port}")

    def _run_discovery_beacon(self):
        """Broadcasts UDP beacon on LAN advertising the selected IP."""
        b_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        b_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self.is_running:
            try:
                msg = f"{DISCOVERY_RESPONSE}:{self.selected_ip}:{self.port}".encode('utf-8')
                b_sock.sendto(msg, ("255.255.255.255", BROADCAST_PORT))
            except Exception:
                pass
            time.sleep(1.0)
        b_sock.close()

    def _run_server(self):
        """Server polling loop using select."""
        while self.is_running:
            try:
                read_sockets = [self.server_socket] + list(self.clients.keys())
                readable, _, exceptional = select.select(read_sockets, [], read_sockets, 0.05)

                for s in readable:
                    if s is self.server_socket:
                        # New client connection
                        client_sock, addr = self.server_socket.accept()
                        client_sock.setblocking(False)
                        with self.lock:
                            assigned_slot = None
                            for slot_idx in range(1, 4):
                                if self.lobby_slots[slot_idx]["type"] in ("open", "bot"):
                                    assigned_slot = slot_idx
                                    break

                            if assigned_slot is not None:
                                self.clients[client_sock] = {"player_id": assigned_slot, "buffer": b""}
                                self.lobby_slots[assigned_slot] = {
                                    "name": f"Player {assigned_slot + 1}",
                                    "type": "human",
                                    "ready": False
                                }
                                # Send join acceptance
                                client_sock.sendall(encode_packet(MSG_JOIN_ACCEPT, {"player_id": assigned_slot}))
                                print(f"[LANServer] Client joined from {addr} as Player {assigned_slot + 1}")
                                self._broadcast_lobby_state_locked()
                            else:
                                client_sock.close()
                    else:
                        # Data from existing client
                        try:
                            data = s.recv(2048)
                            if not data:
                                self._disconnect_client(s)
                            else:
                                with self.lock:
                                    client_info = self.clients.get(s)
                                    if client_info:
                                        client_info["buffer"] += data
                                        packets, remainder = parse_packets(client_info["buffer"])
                                        client_info["buffer"] = remainder
                                        for pkt in packets:
                                            p_type = pkt.get("type")
                                            payload = pkt.get("payload", {})
                                            p_id = client_info["player_id"]

                                            if p_type == MSG_INPUT:
                                                self.latest_client_inputs[p_id] = payload
                                            elif p_type == MSG_READY_TOGGLE:
                                                # Toggle client ready
                                                is_ready = payload.get("ready", not self.lobby_slots[p_id]["ready"])
                                                self.lobby_slots[p_id]["ready"] = is_ready
                                                self._broadcast_lobby_state_locked()
                                            elif p_type == MSG_CHAT:
                                                # Broadcast chat to all clients
                                                msg_text = payload.get("message", "").strip()
                                                if msg_text:
                                                    chat_entry = {
                                                        "sender": self.lobby_slots[p_id]["name"],
                                                        "message": msg_text[:120],
                                                        "player_id": p_id
                                                    }
                                                    self.chat_history.append(chat_entry)
                                                    if len(self.chat_history) > 30:
                                                        self.chat_history.pop(0)
                                                    self._broadcast_chat_locked(chat_entry)
                        except Exception:
                            self._disconnect_client(s)

                for s in exceptional:
                    self._disconnect_client(s)

            except Exception as e:
                if self.is_running:
                    print(f"[LANServer] Loop notice: {e}")

    def _disconnect_client(self, client_sock):
        with self.lock:
            if client_sock in self.clients:
                p_id = self.clients[client_sock]["player_id"]
                del self.clients[client_sock]
                self.lobby_slots[p_id] = {"name": "Open Slot", "type": "open", "ready": False}
                print(f"[LANServer] Player {p_id + 1} disconnected.")
                try:
                    client_sock.close()
                except Exception:
                    pass
                self._broadcast_lobby_state_locked()

    def toggle_slot_bot(self, slot_idx):
        """Host action to toggle an open slot between bot and open."""
        with self.lock:
            if slot_idx in (1, 2, 3):
                curr = self.lobby_slots[slot_idx]["type"]
                if curr == "open":
                    self.lobby_slots[slot_idx] = {
                        "name": f"Bot {slot_idx + 1}",
                        "type": "bot",
                        "ready": True  # Bots are automatically ready
                    }
                elif curr == "bot":
                    self.lobby_slots[slot_idx] = {
                        "name": "Open Slot",
                        "type": "open",
                        "ready": False
                    }
                self._broadcast_lobby_state_locked()

    def cycle_game_mode(self):
        """Cycles the LAN match game mode between FFA, 2v2 Team, and CTF."""
        with self.lock:
            modes = [MODE_FFA, MODE_TEAM, MODE_CTF]
            cur_idx = modes.index(self.game_mode_name) if self.game_mode_name in modes else 0
            self.game_mode_name = modes[(cur_idx + 1) % len(modes)]
            self._broadcast_lobby_state_locked()
            return self.game_mode_name

    def fill_all_bots(self):
        """Fills all currently open slots with CPU bots having random personalities."""
        with self.lock:
            for i in range(1, 4):
                if self.lobby_slots[i]["type"] == "open":
                    pers = random.choice(BOT_PERSONALITIES)
                    self.lobby_slots[i] = {
                        "name": f"Bot {i + 1} ({pers})",
                        "personality": pers,
                        "type": "bot",
                        "ready": True
                    }
            self._broadcast_lobby_state_locked()

    def toggle_host_ready(self):
        """Toggles ready status for Host (Player 0)."""
        with self.lock:
            self.lobby_slots[0]["ready"] = not self.lobby_slots[0]["ready"]
            self._broadcast_lobby_state_locked()

    def send_host_chat(self, message_text):
        """Sends chat from Host to all connected clients."""
        with self.lock:
            msg = message_text.strip()
            if not msg:
                return
            chat_entry = {
                "sender": "Host (P1)",
                "message": msg[:120],
                "player_id": 0
            }
            self.chat_history.append(chat_entry)
            if len(self.chat_history) > 30:
                self.chat_history.pop(0)
            self._broadcast_chat_locked(chat_entry)

    def is_all_players_ready(self):
        """Checks if all 4 slots are occupied (by human or bot) and marked ready."""
        with self.lock:
            for slot_idx in range(4):
                slot = self.lobby_slots[slot_idx]
                if slot["type"] == "open" or not slot["ready"]:
                    return False
            return True

    def _broadcast_lobby_state_locked(self):
        """Broadcasts current lobby player status, mode, and ready flags to all clients."""
        pkt = encode_packet(MSG_LOBBY_STATE, {
            "slots": self.lobby_slots,
            "host_ip": self.selected_ip,
            "port": self.port,
            "game_mode": self.game_mode_name
        })
        for s in list(self.clients.keys()):
            try:
                s.sendall(pkt)
            except Exception:
                pass

    def _broadcast_chat_locked(self, chat_entry):
        """Broadcasts a single chat entry to all clients."""
        pkt = encode_packet(MSG_CHAT, chat_entry)
        for s in list(self.clients.keys()):
            try:
                s.sendall(pkt)
            except Exception:
                pass

    def broadcast_match_start(self):
        """Broadcasts match start trigger with synced game mode to all connected clients."""
        with self.lock:
            self.match_started = True
            pkt = encode_packet(MSG_MATCH_START, {
                "started": True,
                "game_mode": self.game_mode_name
            })
            for s in list(self.clients.keys()):
                try:
                    s.sendall(pkt)
                except Exception:
                    pass

    def get_client_inputs(self):
        """Retrieves and clears recent client inputs."""
        with self.lock:
            return dict(self.latest_client_inputs)

    def broadcast_state(self, state_dict):
        """Sends game state update packet to all connected LAN clients."""
        packet = encode_packet(MSG_STATE_SYNC, state_dict)
        with self.lock:
            for s in list(self.clients.keys()):
                try:
                    s.sendall(packet)
                except Exception:
                    self._disconnect_client(s)

    def stop(self):
        """Shuts down server."""
        self.is_running = False
        with self.lock:
            for s in self.clients:
                try:
                    s.close()
                except Exception:
                    pass
            self.clients.clear()
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

