"""
network/server_core.py - Unified server core for Bubble Arena.
Shared by both headless dedicated server (bubblearena_server.py) and local LAN listen host (lan_server.py).
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
    MSG_INPUT, MSG_STATE_SYNC, MSG_PING, MSG_PONG, MSG_READY_TOGGLE,
    MSG_LOBBY_STATE, MSG_CHAT, MSG_MATCH_START, MSG_KICK, MSG_SERVER_ANNOUNCE
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

class BaseBubbleServer:
    """
    Core non-blocking TCP server for Bubble Arena.
    Supports both Dedicated Server (all 4 slots for remote clients) and Listen Host (slot 0 local host).
    Includes ping/latency calculation, slot management, broadcast chat, player kicking, IP banning, and state replication.
    """
    def __init__(self, host="0.0.0.0", port=DEFAULT_PORT, selected_ip=None,
                 is_dedicated=False, enable_beacon=True, initial_mode=MODE_FFA,
                 initial_level=1, auto_start=True):
        self.host = host
        self.port = port
        self.is_dedicated = is_dedicated
        self.enable_beacon = enable_beacon
        self.auto_start = auto_start
        self.game_mode_name = initial_mode
        self.level_idx = initial_level

        self.available_interfaces = get_available_network_interfaces()
        if selected_ip and (selected_ip in self.available_interfaces or selected_ip == "0.0.0.0"):
            self.selected_ip = selected_ip
        elif self.available_interfaces:
            self.selected_ip = self.available_interfaces[0]
        else:
            self.selected_ip = "127.0.0.1"

        self.server_socket = None
        # clients: {socket: {"player_id": int, "buffer": b"", "ip": str, "port": int, "latency_ms": float, "last_ping": float}}
        self.clients = {}
        self.banned_ips = set()
        self.is_running = False
        self.server_thread = None
        self.beacon_thread = None
        self.ping_thread = None
        self.latest_client_inputs = {}
        self.lock = threading.Lock()
        self.start_time = time.time()

        # Lobby Slots Configuration (0..3)
        self.lobby_slots = {}
        self._reset_slots()

        self.chat_history = []
        self.match_started = False

    def _reset_slots(self):
        """Initializes slot structures according to dedicated or listen-host mode."""
        if self.is_dedicated:
            for i in range(4):
                self.lobby_slots[i] = {
                    "name": "Open Slot",
                    "type": "open",
                    "ready": False,
                    "personality": None,
                    "ip": None,
                    "port": None,
                    "latency_ms": 0.0
                }
        else:
            self.lobby_slots[0] = {
                "name": "Host (P1)",
                "type": "human",
                "ready": False,
                "personality": None,
                "ip": "127.0.0.1",
                "port": self.port,
                "latency_ms": 0.0
            }
            for i in range(1, 4):
                self.lobby_slots[i] = {
                    "name": "Open Slot",
                    "type": "open",
                    "ready": False,
                    "personality": None,
                    "ip": None,
                    "port": None,
                    "latency_ms": 0.0
                }

    def get_local_ip(self):
        """Retrieves the user-selected or active IP address."""
        return self.selected_ip

    def set_selected_ip(self, ip):
        """Updates the selected interface IP address."""
        if ip in self.available_interfaces or ip in ("0.0.0.0", "127.0.0.1"):
            self.selected_ip = ip

    def start(self):
        """Binds TCP socket and launches listener, beacon, and ping monitor threads."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(4)
        self.server_socket.setblocking(False)

        self.is_running = True
        self.match_started = False
        self.start_time = time.time()

        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()

        if self.enable_beacon:
            self.beacon_thread = threading.Thread(target=self._run_discovery_beacon, daemon=True)
            self.beacon_thread.start()

        self.ping_thread = threading.Thread(target=self._run_ping_monitor, daemon=True)
        self.ping_thread.start()

        tag = "Dedicated Server" if self.is_dedicated else "LAN Listen Host"
        print(f"[{tag}] Listening on {self.host}:{self.port} (Advertised IP: {self.selected_ip})")

    def _run_discovery_beacon(self):
        """Broadcasts UDP discovery beacon on LAN advertising the server IP and port."""
        b_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        b_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        adv_ip = self.selected_ip if self.selected_ip != "0.0.0.0" else "127.0.0.1"
        while self.is_running:
            try:
                msg = f"{DISCOVERY_RESPONSE}:{adv_ip}:{self.port}".encode('utf-8')
                b_sock.sendto(msg, ("255.255.255.255", BROADCAST_PORT))
            except Exception:
                pass
            time.sleep(1.0)
        b_sock.close()

    def _run_ping_monitor(self):
        """Periodically measures round-trip ping latency for connected clients."""
        while self.is_running:
            time.sleep(2.0)
            now = time.time()
            with self.lock:
                for s, info in list(self.clients.items()):
                    try:
                        info["last_ping"] = now
                        pkt = encode_packet(MSG_PING, {"t0": now})
                        s.sendall(pkt)
                    except Exception:
                        pass

    def _run_server(self):
        """Non-blocking polling loop using select.select()."""
        while self.is_running:
            try:
                read_sockets = [self.server_socket] + list(self.clients.keys())
                readable, _, exceptional = select.select(read_sockets, [], read_sockets, 0.05)

                for s in readable:
                    if s is self.server_socket:
                        client_sock, addr = self.server_socket.accept()
                        client_ip = addr[0]
                        client_port = addr[1]

                        if client_ip in self.banned_ips:
                            try:
                                client_sock.sendall(encode_packet(MSG_KICK, {"reason": "Banned IP address"}))
                                client_sock.close()
                            except Exception:
                                pass
                            continue

                        client_sock.setblocking(False)
                        with self.lock:
                            assigned_slot = None
                            start_slot = 0 if self.is_dedicated else 1
                            for slot_idx in range(start_slot, 4):
                                if self.lobby_slots[slot_idx]["type"] in ("open", "bot"):
                                    assigned_slot = slot_idx
                                    break

                            if assigned_slot is not None:
                                self.clients[client_sock] = {
                                    "player_id": assigned_slot,
                                    "buffer": b"",
                                    "ip": client_ip,
                                    "port": client_port,
                                    "latency_ms": 0.0,
                                    "last_ping": time.time()
                                }
                                self.lobby_slots[assigned_slot] = {
                                    "name": f"Player {assigned_slot + 1}",
                                    "type": "human",
                                    "ready": False,
                                    "personality": None,
                                    "ip": client_ip,
                                    "port": client_port,
                                    "latency_ms": 0.0
                                }
                                client_sock.sendall(encode_packet(MSG_JOIN_ACCEPT, {
                                    "player_id": assigned_slot,
                                    "game_mode": self.game_mode_name,
                                    "level": self.level_idx
                                }))
                                print(f"[Server] Client joined from {client_ip}:{client_port} as Player {assigned_slot + 1}")
                                self._broadcast_lobby_state_locked()
                            else:
                                try:
                                    client_sock.sendall(encode_packet(MSG_KICK, {"reason": "Server is full (4/4)"}))
                                    client_sock.close()
                                except Exception:
                                    pass
                    else:
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
                                            self._handle_client_packet_locked(s, client_info, pkt)
                        except Exception:
                            self._disconnect_client(s)

                for s in exceptional:
                    self._disconnect_client(s)

            except Exception as e:
                if self.is_running:
                    print(f"[Server] Loop notice: {e}")

    def _handle_client_packet_locked(self, s, client_info, pkt):
        """Processes an incoming validated JSON packet from an active client."""
        p_type = pkt.get("type")
        payload = pkt.get("payload", {})
        p_id = client_info["player_id"]

        if p_type == MSG_INPUT:
            self.latest_client_inputs[p_id] = payload
        elif p_type == MSG_READY_TOGGLE:
            is_ready = payload.get("ready", not self.lobby_slots[p_id]["ready"])
            self.lobby_slots[p_id]["ready"] = is_ready
            self._broadcast_lobby_state_locked()
            if self.auto_start and self.is_all_players_ready():
                self.broadcast_match_start()
        elif p_type == MSG_PONG:
            t0 = payload.get("t0", 0.0)
            if t0 > 0:
                rtt = max(0.0, round((time.time() - t0) * 1000.0, 1))
                client_info["latency_ms"] = rtt
                if p_id in self.lobby_slots:
                    self.lobby_slots[p_id]["latency_ms"] = rtt
        elif p_type == MSG_CHAT:
            msg_text = payload.get("message", "").strip()
            if msg_text:
                chat_entry = {
                    "sender": self.lobby_slots[p_id]["name"],
                    "message": msg_text[:120],
                    "player_id": p_id
                }
                self.chat_history.append(chat_entry)
                if len(self.chat_history) > 40:
                    self.chat_history.pop(0)
                self._broadcast_chat_locked(chat_entry)

    def _disconnect_client(self, client_sock):
        """Handles socket disconnection and resets the corresponding slot to open."""
        with self.lock:
            if client_sock in self.clients:
                p_id = self.clients[client_sock]["player_id"]
                c_ip = self.clients[client_sock]["ip"]
                c_port = self.clients[client_sock]["port"]
                del self.clients[client_sock]
                self.lobby_slots[p_id] = {
                    "name": "Open Slot",
                    "type": "open",
                    "ready": False,
                    "personality": None,
                    "ip": None,
                    "port": None,
                    "latency_ms": 0.0
                }
                if p_id in self.latest_client_inputs:
                    del self.latest_client_inputs[p_id]
                print(f"[Server] Player {p_id + 1} ({c_ip}:{c_port}) disconnected.")
                try:
                    client_sock.close()
                except Exception:
                    pass
                self._broadcast_lobby_state_locked()

    def kick_player(self, slot_idx, reason="Kicked by administrator"):
        """Kicks player from specified slot (0..3) with optional notification."""
        with self.lock:
            if slot_idx < 0 or slot_idx > 3:
                return False, f"Invalid slot index {slot_idx}. Must be 0..3."
            slot = self.lobby_slots.get(slot_idx)
            if not slot or slot["type"] == "open":
                return False, f"Slot {slot_idx + 1} is already open."

            if slot["type"] == "bot":
                self.lobby_slots[slot_idx] = {
                    "name": "Open Slot",
                    "type": "open",
                    "ready": False,
                    "personality": None,
                    "ip": None,
                    "port": None,
                    "latency_ms": 0.0
                }
                self._broadcast_lobby_state_locked()
                return True, f"Bot in Slot {slot_idx + 1} removed."

            target_sock = None
            for s, info in self.clients.items():
                if info["player_id"] == slot_idx:
                    target_sock = s
                    break

            if target_sock:
                try:
                    target_sock.sendall(encode_packet(MSG_KICK, {"reason": reason}))
                except Exception:
                    pass
                if target_sock in self.clients:
                    del self.clients[target_sock]
                try:
                    target_sock.close()
                except Exception:
                    pass

            self.lobby_slots[slot_idx] = {
                "name": "Open Slot",
                "type": "open",
                "ready": False,
                "personality": None,
                "ip": None,
                "port": None,
                "latency_ms": 0.0
            }
            if slot_idx in self.latest_client_inputs:
                del self.latest_client_inputs[slot_idx]
            self._broadcast_lobby_state_locked()
            return True, f"Player {slot_idx + 1} kicked ({reason})."

    def ban_ip(self, ip):
        """Adds an IP address to the blacklist and kicks any currently connected client from that IP."""
        with self.lock:
            self.banned_ips.add(ip)
            kicked = []
            for s, info in list(self.clients.items()):
                if info["ip"] == ip:
                    p_id = info["player_id"]
                    try:
                        s.sendall(encode_packet(MSG_KICK, {"reason": "IP Banned by server administrator"}))
                        s.close()
                    except Exception:
                        pass
                    del self.clients[s]
                    self.lobby_slots[p_id] = {
                        "name": "Open Slot",
                        "type": "open",
                        "ready": False,
                        "personality": None,
                        "ip": None,
                        "port": None,
                        "latency_ms": 0.0
                    }
                    kicked.append(f"Player {p_id + 1}")
            if kicked:
                self._broadcast_lobby_state_locked()
            return True, f"Banned IP {ip}." + (f" Kicked active: {', '.join(kicked)}" if kicked else "")

    def unban_ip(self, ip):
        """Removes an IP address from the blacklist."""
        with self.lock:
            if ip in self.banned_ips:
                self.banned_ips.remove(ip)
                return True, f"Unbanned IP {ip}."
            return False, f"IP {ip} is not in ban list."

    def set_game_mode(self, mode_name):
        """Sets active match game mode and broadcasts to all clients."""
        with self.lock:
            mode_input = str(mode_name).strip()
            mode_map = {
                "ffa": MODE_FFA,
                "free for all": MODE_FFA,
                "team": MODE_TEAM,
                "2v2 team brawler": MODE_TEAM,
                "ctf": MODE_CTF,
                "capture the flag": MODE_CTF
            }
            resolved = mode_map.get(mode_input.lower())
            if not resolved and mode_input in (MODE_FFA, MODE_TEAM, MODE_CTF):
                resolved = mode_input
            if not resolved:
                return False, f"Unknown mode '{mode_name}'. Valid: ffa, team, ctf"
            self.game_mode_name = resolved
            self._broadcast_lobby_state_locked()
            return True, f"Game mode set to [{self.game_mode_name}]."

    def cycle_game_mode(self):
        """Cycles game mode between FFA, 2v2 Team, and CTF."""
        with self.lock:
            modes = [MODE_FFA, MODE_TEAM, MODE_CTF]
            cur_idx = modes.index(self.game_mode_name) if self.game_mode_name in modes else 0
            self.game_mode_name = modes[(cur_idx + 1) % len(modes)]
            self._broadcast_lobby_state_locked()
            return self.game_mode_name

    def set_level(self, level_idx):
        """Sets stage level (1..14) and broadcasts to all clients."""
        with self.lock:
            try:
                idx = int(level_idx)
                if not (1 <= idx <= 14):
                    return False, "Level must be between 1 and 14."
                self.level_idx = idx
                self._broadcast_lobby_state_locked()
                return True, f"Level set to Stage {self.level_idx}."
            except ValueError:
                return False, "Invalid level number."

    def add_bot(self, slot_idx=None, personality=None):
        """Adds a CPU bot with specified personality to a specific or next open slot."""
        with self.lock:
            if personality is None:
                personality = random.choice(BOT_PERSONALITIES)
            elif personality not in BOT_PERSONALITIES:
                personality = "Standard"

            if slot_idx is not None:
                if slot_idx < 0 or slot_idx > 3:
                    return False, "Slot index must be 0..3."
                target_slot = slot_idx
            else:
                target_slot = None
                start_slot = 0 if self.is_dedicated else 1
                for i in range(start_slot, 4):
                    if self.lobby_slots[i]["type"] == "open":
                        target_slot = i
                        break

            if target_slot is None:
                return False, "No open slots available for bot."

            self.lobby_slots[target_slot] = {
                "name": f"Bot {target_slot + 1} ({personality})",
                "type": "bot",
                "personality": personality,
                "ready": True,
                "ip": "127.0.0.1",
                "port": 0,
                "latency_ms": 0.0
            }
            self._broadcast_lobby_state_locked()
            if self.auto_start and self.is_all_players_ready():
                self.broadcast_match_start()
            return True, f"Added {personality} Bot into Slot {target_slot + 1}."

    def kick_bot(self, slot_idx):
        """Removes a bot from specified slot."""
        with self.lock:
            if slot_idx < 0 or slot_idx > 3:
                return False, "Slot index must be 0..3."
            if self.lobby_slots[slot_idx]["type"] != "bot":
                return False, f"Slot {slot_idx + 1} does not contain a bot."
            self.lobby_slots[slot_idx] = {
                "name": "Open Slot",
                "type": "open",
                "ready": False,
                "personality": None,
                "ip": None,
                "port": None,
                "latency_ms": 0.0
            }
            self._broadcast_lobby_state_locked()
            return True, f"Bot in Slot {slot_idx + 1} removed."

    def fill_all_bots(self):
        """Fills all currently open slots with CPU bots having random personalities."""
        with self.lock:
            start_slot = 0 if self.is_dedicated else 1
            added = 0
            for i in range(start_slot, 4):
                if self.lobby_slots[i]["type"] == "open":
                    pers = random.choice(BOT_PERSONALITIES)
                    self.lobby_slots[i] = {
                        "name": f"Bot {i + 1} ({pers})",
                        "personality": pers,
                        "type": "bot",
                        "ready": True,
                        "ip": "127.0.0.1",
                        "port": 0,
                        "latency_ms": 0.0
                    }
                    added += 1
            self._broadcast_lobby_state_locked()
            if self.auto_start and self.is_all_players_ready():
                self.broadcast_match_start()
            return added

    def broadcast_announcement(self, message_text):
        """Sends server-wide announcement chat to all connected clients."""
        with self.lock:
            msg = message_text.strip()
            if not msg:
                return False, "Empty message."
            chat_entry = {
                "sender": "[SERVER]",
                "message": msg[:120],
                "player_id": -1
            }
            self.chat_history.append(chat_entry)
            if len(self.chat_history) > 40:
                self.chat_history.pop(0)
            self._broadcast_chat_locked(chat_entry)
            return True, f"Broadcasted: {msg}"

    def send_chat(self, sender_name, message_text, player_id=0):
        """Broadcasts a user chat entry to all connected clients."""
        with self.lock:
            msg = message_text.strip()
            if not msg:
                return
            chat_entry = {
                "sender": sender_name,
                "message": msg[:120],
                "player_id": player_id
            }
            self.chat_history.append(chat_entry)
            if len(self.chat_history) > 40:
                self.chat_history.pop(0)
            self._broadcast_chat_locked(chat_entry)

    def is_all_players_ready(self):
        """Checks if all 4 slots are occupied (human or bot) and marked ready."""
        with self.lock:
            for slot_idx in range(4):
                slot = self.lobby_slots[slot_idx]
                if slot["type"] == "open" or not slot["ready"]:
                    return False
            return True

    def broadcast_match_start(self):
        """Broadcasts match start trigger with synced game mode and level to all connected clients."""
        with self.lock:
            self.match_started = True
            pkt = encode_packet(MSG_MATCH_START, {
                "started": True,
                "game_mode": self.game_mode_name,
                "level": self.level_idx
            })
            for s in list(self.clients.keys()):
                try:
                    s.sendall(pkt)
                except Exception:
                    pass
            print(f"[Server] Match started! Mode: {self.game_mode_name.upper()}, Level: {self.level_idx}")

    def _broadcast_lobby_state_locked(self):
        """Broadcasts current lobby player status, mode, and ready flags to all clients."""
        pkt = encode_packet(MSG_LOBBY_STATE, {
            "slots": self.lobby_slots,
            "host_ip": self.selected_ip,
            "port": self.port,
            "game_mode": self.game_mode_name,
            "level": self.level_idx
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

    def get_status_report(self):
        """Returns structured dictionary of server health, configuration, and player status."""
        with self.lock:
            uptime = int(time.time() - self.start_time)
            slots_summary = []
            for i in range(4):
                s = self.lobby_slots[i]
                slots_summary.append({
                    "slot": i + 1,
                    "name": s["name"],
                    "type": s["type"],
                    "ready": s["ready"],
                    "ip": s.get("ip"),
                    "port": s.get("port"),
                    "latency_ms": s.get("latency_ms", 0.0),
                    "personality": s.get("personality")
                })
            return {
                "uptime_seconds": uptime,
                "host": self.host,
                "port": self.port,
                "selected_ip": self.selected_ip,
                "is_dedicated": self.is_dedicated,
                "game_mode": self.game_mode_name,
                "level": self.level_idx,
                "match_started": self.match_started,
                "auto_start": self.auto_start,
                "client_count": len(self.clients),
                "banned_ips": list(self.banned_ips),
                "slots": slots_summary
            }

    def format_status_table(self):
        """Renders formatted ASCII table for terminal display."""
        rep = self.get_status_report()
        mins, secs = divmod(rep["uptime_seconds"], 60)
        hrs, mins = divmod(mins, 60)
        uptime_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"

        lines = [
            "=" * 72,
            f" BUBBLE ARENA SERVER - {'DEDICATED' if rep['is_dedicated'] else 'LISTEN HOST'}",
            "=" * 72,
            f" Bound: {rep['host']}:{rep['port']} | Advertised IP: {rep['selected_ip']}",
            f" Uptime: {uptime_str} | Mode: {rep['game_mode'].upper()} | Level: Stage {rep['level']} | AutoStart: {rep['auto_start']}",
            f" Match In Progress: {'YES' if rep['match_started'] else 'NO (Lobby)'} | Banned IPs: {len(rep['banned_ips'])}",
            "-" * 72,
            f" {'SLOT':<6} {'TYPE':<8} {'NAME':<20} {'ENDPOINT':<18} {'PING':<8} {'STATUS':<8}",
            "-" * 72
        ]

        for s in rep["slots"]:
            ep = f"{s['ip']}:{s['port']}" if s["ip"] else "-"
            ping_str = f"{s['latency_ms']:.1f}ms" if s["ip"] and s["type"] == "human" else "-"
            ready_str = "READY" if s["ready"] else "WAIT"
            if s["type"] == "open":
                ready_str = "-"
            lines.append(
                f" P{s['slot']:<5} {s['type'].upper():<8} {s['name'][:19]:<20} {ep:<18} {ping_str:<8} {ready_str:<8}"
            )

        lines.append("=" * 72)
        return "\n".join(lines)

    def stop(self):
        """Shuts down server gracefully, disconnecting clients."""
        self.is_running = False
        with self.lock:
            for s in list(self.clients.keys()):
                try:
                    s.sendall(encode_packet(MSG_KICK, {"reason": "Server shutting down"}))
                    s.close()
                except Exception:
                    pass
            self.clients.clear()
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
