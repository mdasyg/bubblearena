"""
network/lan_server.py - Non-blocking LAN host server for Bubble Arena.
"""
import socket
import select
import threading
import time
from constants import DEFAULT_PORT, BROADCAST_PORT, DISCOVERY_MAGIC, DISCOVERY_RESPONSE
from network.protocol import encode_packet, parse_packets, MSG_JOIN_REQUEST, MSG_JOIN_ACCEPT, MSG_INPUT, MSG_STATE_SYNC

class LANServer:
    """Manages LAN hosting, client connections, input ingestion, and state broadcasting."""
    def __init__(self, host="0.0.0.0", port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # {client_socket: {"player_id": int, "buffer": b""}}
        self.is_running = False
        self.server_thread = None
        self.beacon_thread = None
        self.latest_client_inputs = {}  # {player_id: action_dict}
        self.lock = threading.Lock()

    def get_local_ip(self):
        """Retrieves the local LAN IP address of this machine."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    def start(self):
        """Starts the server thread and UDP discovery broadcaster."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(4)
        self.server_socket.setblocking(False)

        self.is_running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()

        self.beacon_thread = threading.Thread(target=self._run_discovery_beacon, daemon=True)
        self.beacon_thread.start()
        print(f"[LANServer] Hosting match on {self.get_local_ip()}:{self.port}")

    def _run_discovery_beacon(self):
        """Broadcasts UDP beacon on LAN so clients can discover host."""
        b_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        b_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self.is_running:
            try:
                msg = f"{DISCOVERY_RESPONSE}:{self.get_local_ip()}:{self.port}".encode('utf-8')
                b_sock.sendto(msg, ("255.255.255.255", BROADCAST_PORT))
            except Exception:
                pass
            time.sleep(1.0)
        b_sock.close()

    def _run_server(self):
        """Server polling loop using select."""
        next_player_id = 1  # Host is Player 0, clients get Player 1, 2, 3

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
                            if next_player_id <= 3:
                                self.clients[client_sock] = {"player_id": next_player_id, "buffer": b""}
                                # Send join acceptance
                                client_sock.sendall(encode_packet(MSG_JOIN_ACCEPT, {"player_id": next_player_id}))
                                print(f"[LANServer] Client joined from {addr} as Player {next_player_id + 1}")
                                next_player_id += 1
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
                                            if pkt.get("type") == MSG_INPUT:
                                                p_id = client_info["player_id"]
                                                self.latest_client_inputs[p_id] = pkt.get("payload", {})
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
                print(f"[LANServer] Player {p_id + 1} disconnected.")
                try:
                    client_sock.close()
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
