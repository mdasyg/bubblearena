"""
network/protocol.py - Packet structure and serialization for LAN multiplayer in Bubble Arena.
"""
import json

MSG_JOIN_REQUEST = "JOIN_REQ"
MSG_JOIN_ACCEPT = "JOIN_ACC"
MSG_INPUT = "INPUT"
MSG_STATE_SYNC = "STATE_SYNC"
MSG_PING = "PING"
MSG_PONG = "PONG"

def encode_packet(msg_type, payload):
    """Encodes message type and payload to utf-8 JSON bytes with newline delimiter."""
    data = {
        "type": msg_type,
        "payload": payload
    }
    return (json.dumps(data) + "\n").encode('utf-8')

def parse_packets(raw_buffer):
    """Splits raw byte stream on newline delimiters into JSON packet dictionaries."""
    packets = []
    lines = raw_buffer.split(b'\n')
    remainder = lines[-1]
    for line in lines[:-1]:
        if line.strip():
            try:
                packets.append(json.loads(line.decode('utf-8')))
            except Exception as e:
                print(f"[Protocol] Error decoding packet: {e}")
    return packets, remainder
