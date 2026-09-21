#!/usr/bin/env python3
"""
bubblearena_server.py - Standalone Headless Dedicated Server & Console Manager for Bubble Arena.

Designed for headless execution on Linux, FreeBSD, macOS, or Windows remote servers.
Provides interactive console commands for real-time player administration, kicking,
latency monitoring, mode/level switching, and IP banning.
"""
import sys
import os
import time
import signal
import shlex
import argparse
from constants import (
    DEFAULT_PORT, MODE_FFA, MODE_TEAM, MODE_CTF,
    BOT_PERSONALITIES, BOT_PERSONALITY_STANDARD
)
from network.server_core import BaseBubbleServer, get_available_network_interfaces

BANNER = r"""
========================================================================
   ____        __     __     __         ___                            
  / __ )__  __/ /_   / /_   / /__      /   |  ________  ____  ____ _ 
 / __  / / / / __ \ / __ \ / / _ \    / /| | / ___/ _ \/ __ \/ __ `/ 
/ /_/ / /_/ / /_/ // /_/ // /  __/   / ___ |/ /  /  __/ / / / /_/ /  
\____/\__,_/_.___/ \_.___/_/\___/   /_/  |_/_/   \___/_/ /_/\__,_/   
               DEDICATED CONSOLE SERVER (Headless)
========================================================================
"""

def parse_cli_arguments(args=None):
    """Parses command-line arguments for the dedicated server."""
    parser = argparse.ArgumentParser(
        description="Bubble Arena - Standalone Headless Dedicated Server"
    )
    parser.add_argument(
        "-i", "--interface",
        default="0.0.0.0",
        help="Interface IP to bind (e.g. 0.0.0.0 for all interfaces, 127.0.0.1 for local, or specific adapter IP)"
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port number to listen on (default: {DEFAULT_PORT})"
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["ffa", "team", "ctf"],
        default="ffa",
        help="Initial game mode (ffa, team, ctf)"
    )
    parser.add_argument(
        "-l", "--level",
        type=int,
        default=1,
        help="Initial map level (1-28)"
    )
    parser.add_argument(
        "--no-beacon",
        action="store_true",
        help="Disable UDP LAN discovery beacon (recommended for public Internet VPS)"
    )
    parser.add_argument(
        "--no-auto-start",
        action="store_true",
        help="Disable automatic match launch when all 4 player slots are ready"
    )
    return parser.parse_args(args)


class ConsoleManager:
    """
    Interactive managerial console shell for controlling the dedicated server.
    """
    def __init__(self, server):
        self.server = server
        self.is_running = True

    def print_help(self):
        """Displays available administrative console commands."""
        help_text = """
AVAILABLE ADMINISTRATIVE COMMANDS:
------------------------------------------------------------------------
  status | st               Display comprehensive server dashboard & player slots
  players | pl              Compact list of connected players, IP, and ping latency
  kick <slot|name> [reason] Kick a player from slot (1..4) or matching name
  ban <ip>                  Blacklist an IP address and disconnect matching clients
  unban <ip>                Remove an IP from the blacklist
  bans                      List all currently blacklisted IP addresses
  mode <ffa|team|ctf>       Change the active game mode and notify all clients
  level <1..28>             Change the active arena level and notify all clients
  bot add [slot] [pers]     Add bot (Aggressive, Passive, Standard) to slot (1..4)
  bot kick <slot>           Remove bot from slot (1..4)
  bots fill                 Fill all open slots with CPU bots
  say <message>             Broadcast a [SERVER] announcement to lobby chat
  start                     Force start the match immediately
  autostart <on|off>        Toggle auto-launching when all 4 slots are ready
  interfaces                List detected physical and virtual network interfaces
  clear | cls               Clear console terminal screen
  help | ?                  Show this command reference
  stop | exit | quit        Gracefully shut down dedicated server
------------------------------------------------------------------------
"""
        print(help_text)

    def execute_command(self, cmd_line):
        """Dispatches a single administrative console command string."""
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return True

        try:
            tokens = shlex.split(cmd_line)
        except Exception as e:
            print(f"[Admin] Parse error: {e}")
            return True

        cmd = tokens[0].lower()
        args = tokens[1:]

        if cmd in ("status", "st", "info"):
            print(self.server.format_status_table())

        elif cmd in ("players", "pl", "list"):
            rep = self.server.get_status_report()
            print(f"Connected Players ({rep['client_count']}/4):")
            for s in rep["slots"]:
                if s["type"] != "open":
                    ep = f"{s['ip']}:{s['port']}" if s['ip'] else "local"
                    ping = f"{s['latency_ms']:.1f}ms" if s['type'] == 'human' else "bot"
                    ready = "READY" if s['ready'] else "NOT READY"
                    print(f"  Slot {s['slot']}: {s['name']} | {s['type'].upper()} | {ep} | Ping: {ping} | {ready}")
            if rep['client_count'] == 0:
                print("  No human players currently connected.")

        elif cmd == "kick":
            if not args:
                print("Usage: kick <slot 1-4 | player_name> [reason]")
                return True
            target = args[0]
            reason = " ".join(args[1:]) if len(args) > 1 else "Kicked by administrator"
            slot_idx = None
            if target.isdigit():
                slot_idx = int(target) - 1
            else:
                rep = self.server.get_status_report()
                for s in rep["slots"]:
                    if target.lower() in s["name"].lower():
                        slot_idx = s["slot"] - 1
                        break
            if slot_idx is not None and 0 <= slot_idx <= 3:
                success, msg = self.server.kick_player(slot_idx, reason=reason)
                print(f"[Admin] {msg}")
            else:
                print(f"[Admin] Player or slot '{target}' not found.")

        elif cmd == "ban":
            if not args:
                print("Usage: ban <ip_address>")
                return True
            ip = args[0]
            _, msg = self.server.ban_ip(ip)
            print(f"[Admin] {msg}")

        elif cmd == "unban":
            if not args:
                print("Usage: unban <ip_address>")
                return True
            ip = args[0]
            _, msg = self.server.unban_ip(ip)
            print(f"[Admin] {msg}")

        elif cmd == "bans":
            bans = self.server.banned_ips
            if bans:
                print("Blacklisted IP Addresses:")
                for b in sorted(bans):
                    print(f"  - {b}")
            else:
                print("No IP addresses currently banned.")

        elif cmd in ("mode", "gamemode"):
            if not args:
                print(f"Current mode: {self.server.game_mode_name.upper()}. Usage: mode <ffa|team|ctf>")
                return True
            mode_input = args[0].lower()
            mode_map = {"ffa": MODE_FFA, "team": MODE_TEAM, "ctf": MODE_CTF}
            target_mode = mode_map.get(mode_input, mode_input)
            success, msg = self.server.set_game_mode(target_mode)
            print(f"[Admin] {msg}")

        elif cmd in ("level", "map", "stage"):
            if not args:
                print(f"Current level: Stage {self.server.level_idx}. Usage: level <1-28>")
                return True
            success, msg = self.server.set_level(args[0])
            print(f"[Admin] {msg}")

        elif cmd == "bot":
            if not args:
                print("Usage: bot add [slot 1-4] [Aggressive|Passive|Standard]  OR  bot kick <slot 1-4>")
                return True
            subcmd = args[0].lower()
            if subcmd == "add":
                target_slot = None
                pers = None
                if len(args) > 1 and args[1].isdigit():
                    target_slot = int(args[1]) - 1
                    if len(args) > 2:
                        pers = args[2].capitalize()
                elif len(args) > 1:
                    pers = args[1].capitalize()
                success, msg = self.server.add_bot(slot_idx=target_slot, personality=pers)
                print(f"[Admin] {msg}")
            elif subcmd in ("kick", "remove", "del"):
                if len(args) < 2 or not args[1].isdigit():
                    print("Usage: bot kick <slot 1-4>")
                    return True
                target_slot = int(args[1]) - 1
                success, msg = self.server.kick_bot(target_slot)
                print(f"[Admin] {msg}")
            else:
                print("Unknown bot subcommand. Use 'bot add' or 'bot kick'.")

        elif cmd == "bots" and args and args[0].lower() == "fill":
            added = self.server.fill_all_bots()
            print(f"[Admin] Filled {added} open slots with CPU bots.")

        elif cmd in ("say", "announce", "chat"):
            if not args:
                print("Usage: say <announcement message>")
                return True
            message = " ".join(args)
            success, msg = self.server.broadcast_announcement(message)
            print(f"[Admin] {msg}")

        elif cmd == "start":
            self.server.broadcast_match_start()
            print("[Admin] Match manually started!")

        elif cmd in ("autostart", "auto-start"):
            if not args:
                print(f"Auto-Start is currently: {'ON' if self.server.auto_start else 'OFF'}. Usage: autostart <on|off>")
                return True
            setting = args[0].lower() in ("1", "true", "on", "yes")
            self.server.auto_start = setting
            print(f"[Admin] Auto-Start match is now: {'ON' if self.server.auto_start else 'OFF'}.")

        elif cmd in ("interfaces", "ifaces", "ips"):
            ifaces = get_available_network_interfaces()
            print("Detected Network Interfaces:")
            for ip in ifaces:
                print(f"  - {ip}")

        elif cmd in ("clear", "cls"):
            os.system('cls' if os.name == 'nt' else 'clear')

        elif cmd in ("help", "?"):
            self.print_help()

        elif cmd in ("stop", "exit", "quit"):
            print("[Admin] Shutting down dedicated server...")
            self.server.stop()
            self.is_running = False
            return False

        else:
            print(f"Unknown command: '{cmd}'. Type 'help' for command list.")

        return True

    def run_interactive_loop(self):
        """Runs the interactive command loop until exit or EOF."""
        print(BANNER)
        print(f"Dedicated server running on {self.server.host}:{self.server.port}")
        print("Type 'help' or 'status' for commands. Press Ctrl+C or type 'stop' to shut down.\n")

        while self.is_running and self.server.is_running:
            try:
                # Handle non-interactive environments (nohup, systemd, docker)
                if not sys.stdin.isatty():
                    time.sleep(1.0)
                    continue

                prompt = "bubblearena-srv> "
                try:
                    cmd_line = input(prompt)
                except EOFError:
                    # In case of EOF, keep running non-interactively
                    time.sleep(1.0)
                    continue

                if not self.execute_command(cmd_line):
                    break

            except KeyboardInterrupt:
                print("\n[Admin] KeyboardInterrupt received. Shutting down...")
                self.server.stop()
                break
            except Exception as e:
                print(f"[Admin] Command loop error: {e}")


def main():
    """Main entrypoint for bubblearena_server.py."""
    args = parse_cli_arguments()

    mode_map = {"ffa": MODE_FFA, "team": MODE_TEAM, "ctf": MODE_CTF}
    selected_mode = mode_map.get(args.mode.lower(), MODE_FFA)

    server = BaseBubbleServer(
        host=args.interface,
        port=args.port,
        selected_ip=args.interface if args.interface != "0.0.0.0" else None,
        is_dedicated=True,
        enable_beacon=not args.no_beacon,
        initial_mode=selected_mode,
        initial_level=args.level,
        auto_start=not args.no_auto_start
    )

    # Graceful signal handling for systemd, kill, Ctrl+C
    def sig_handler(signum, frame):
        print(f"\n[Server] Signal {signum} received. Cleaning up...")
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, sig_handler)

    try:
        server.start()
    except Exception as e:
        print(f"[Fatal] Failed to bind server to {args.interface}:{args.port}: {e}")
        sys.exit(1)

    manager = ConsoleManager(server)
    manager.run_interactive_loop()


if __name__ == "__main__":
    main()
