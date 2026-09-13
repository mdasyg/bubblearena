"""
main.py - Entry point and CLI launcher for Bubble Arena.
"""
import sys
import argparse
from engine.game import GameEngine
from constants import MODE_FFA, MODE_TEAM, MODE_CTF

def parse_arguments():
    parser = argparse.ArgumentParser(description="Bubble Arena - 4-Player Retro 2D Arcade Brawler in Python Pygame")
    parser.add_argument("--mode", choices=["ffa", "team", "ctf"], default="ffa", help="Starting game mode")
    parser.add_argument("--level", type=int, default=1, help="Starting level (1-10)")
    parser.add_argument("--bots", action="store_true", help="Start instantly in 1-Player vs 3 AI Bots mode")
    parser.add_argument("--host", action="store_true", help="Host a LAN multiplayer room")
    parser.add_argument("--join", type=str, default=None, help="Join a LAN host IP (e.g. 192.168.1.5)")
    return parser.parse_args()

def main():
    args = parse_arguments()
    engine = GameEngine(is_bot_match=args.bots)

    # Apply CLI level
    if 1 <= args.level <= engine.level_mgr.get_level_count():
        engine.level_mgr.load_level(args.level - 1)

    # Apply CLI mode
    mode_map = {"ffa": MODE_FFA, "team": MODE_TEAM, "ctf": MODE_CTF}
    selected_mode = mode_map.get(args.mode, MODE_FFA)
    engine.set_game_mode(selected_mode)

    if args.bots:
        engine.start_match()

    if args.host:
        from network.lan_server import LANServer
        from constants import STATE_LAN_ROOM
        engine.lan_server = LANServer()
        engine.lan_server.start()
        engine.is_lan_host = True
        engine.state = STATE_LAN_ROOM

    if args.join:
        from network.lan_client import LANClient
        from constants import STATE_LAN_ROOM
        engine.lan_client = LANClient()
        if engine.lan_client.connect(args.join):
            engine.is_lan_client = True
            engine.state = STATE_LAN_ROOM

    engine.run()

if __name__ == "__main__":
    main()
