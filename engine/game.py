"""
engine/game.py - Core game loop, state machine, physics accumulator, and rendering orchestrator for Bubble Arena.
"""
import pygame
import sys
import random
import math
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, VIRTUAL_WIDTH, VIRTUAL_HEIGHT, FPS, TITLE,
    STATE_MENU, STATE_MODE_SELECT, STATE_LEVEL_SELECT, STATE_LOBBY,
    STATE_PLAYING, STATE_PAUSED, STATE_GAMEOVER, STATE_VICTORY, STATE_CONTROLS, STATE_LAN_ROOM,
    STATE_PLAYER_COUNT, STATE_SETTINGS, SPEED_OPTIONS, DEFAULT_ROUNDS, BOT_PERSONALITIES,
    MUSIC_VOLUME_OPTIONS, SFX_VOLUME_OPTIONS, MIN_DURATION_OPTIONS, ROUND_TIMER_OPTIONS, BOT_PREFERENCE_OPTIONS,
    MODE_FFA, MODE_TEAM, MODE_CTF, GAME_MODES, PLAYER_COLORS,
    COLOR_GOLD, COLOR_RED, COLOR_GREEN, DEFAULT_PORT, BUBBLE_BOUNCE_SPEED
)
from engine.sound import SoundManager
from engine.sprites import SpriteManager
from engine.particles import ParticleManager
from engine.input_handler import InputHandler
from levels.level_manager import LevelManager
from entities.player import Player
from entities.bubble import Bubble
from entities.trapped_bubble import TrappedBubble
from entities.powerup import PowerUp
from entities.flag import Flag
from modes.ffa_mode import FFAMode
from modes.team_mode import TeamMode
from modes.ctf_mode import CTFMode
from ui.hud import HUD
from ui.menu import MenuSystem
from network.lan_server import LANServer, get_available_network_interfaces
from network.lan_client import LANClient

class GameEngine:
    """The central game orchestrator."""
    def __init__(self, is_bot_match=False):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.is_running = True

        # Subsystems
        self.sound_mgr = SoundManager()
        self.sprite_mgr = SpriteManager()
        self.particle_mgr = ParticleManager()
        self.input_handler = InputHandler()
        self.level_mgr = LevelManager()
        self.hud = HUD()
        self.menu = MenuSystem()

        # Network & Interfaces
        self.lan_server = None
        self.lan_client = None
        self.is_lan_host = False
        self.is_lan_client = False
        self.found_hosts = []
        self.net_status_msg = ""
        self.net_interfaces = get_available_network_interfaces()
        self.selected_iface_idx = 0
        self.lan_chat_input = ""
        self.is_chat_active = False
        self.room_slots = {
            0: {"name": "Host (P1)", "type": "human", "ready": False},
            1: {"name": "Open Slot", "type": "open", "ready": False},
            2: {"name": "Open Slot", "type": "open", "ready": False},
            3: {"name": "Open Slot", "type": "open", "ready": False},
        }
        self.room_chat_history = []
        self.target_remote_ip = "127.0.0.1"
        self.remote_ip_idx = 0

        # Match setup
        self.state = STATE_MENU
        self.current_mode_name = MODE_FFA
        self.game_mode = FFAMode()
        self.is_bot_match = is_bot_match

        # Speed & Multi-Round Match Settings
        self.speed_idx = 1  # Default Normal (1.0x)
        self.game_speed_mult = 1.0
        self.total_rounds = DEFAULT_ROUNDS  # Default 4 rounds
        self.current_round = 1
        self.round_transition_timer = 0.0
        self.round_transition_text = ""

        # Audio & Game Customization Settings
        self.music_vol_idx = 2  # Default Normal (100%)
        self.sfx_vol_idx = 2    # Default Normal (100%)
        self.min_duration_idx = 2  # Default 45s
        self.min_round_duration = 45.0
        self.round_timer_idx = 1  # Default 90s
        self.round_match_time = 90.0
        self.bot_personality_idx = 0  # Default Mixed (Random)

        # Entities
        self.players = []
        self.bubbles = []
        self.trapped_bubbles = []
        self.powerups = []
        self.flag = None
        self.item_spawn_timer = 8.0

        self._init_players()

    def setup_players_by_human_count(self, human_count=1):
        """Sets the first `human_count` players as humans, and the remaining up to 4 as CPU bots with chosen personality preference."""
        human_count = max(1, min(4, human_count))
        self.players.clear()
        pref = BOT_PREFERENCE_OPTIONS[self.bot_personality_idx][1]
        for i in range(4):
            sp = self.level_mgr.spawn_points.get(i, (40 + i * 100, 50))
            is_bot = (i >= human_count)
            team = 0 if i in (0, 2) else 1
            if is_bot:
                pers = pref if pref is not None else random.choice(BOT_PERSONALITIES)
            else:
                pers = None
            p = Player(player_id=i, spawn_x=sp[0], spawn_y=sp[1], team=team, is_bot=is_bot, personality=pers)
            self.players.append(p)

    def _init_players(self):
        """Creates 4 player instances based on is_bot_match or default settings."""
        if self.is_bot_match:
            self.setup_players_by_human_count(1)
        else:
            self.setup_players_by_human_count(4)

    def set_game_mode(self, mode_name):
        """Switches the active game mode rules."""
        self.current_mode_name = mode_name
        if mode_name == MODE_FFA:
            self.game_mode = FFAMode(match_duration=self.round_match_time, min_round_duration=self.min_round_duration)
            for p in self.players:
                p.team = p.id
        elif mode_name == MODE_TEAM:
            self.game_mode = TeamMode(match_duration=self.round_match_time, min_round_duration=self.min_round_duration)
            for p in self.players:
                p.team = 0 if p.id in (0, 2) else 1
        elif mode_name == MODE_CTF:
            self.game_mode = CTFMode(match_duration=self.round_match_time, min_round_duration=self.min_round_duration)
            for p in self.players:
                p.team = 0 if p.id in (0, 2) else 1

    def start_match(self, use_random_map=True, is_new_match=True):
        """Starts a fresh match on a random or selected level and mode."""
        if is_new_match:
            self.current_round = 1
            for p in self.players:
                p.score = 0
                p.kills = 0
                p.deaths = 0
                p.rescues = 0

        if use_random_map:
            self.level_mgr.load_random_level()

        self.bubbles.clear()
        self.trapped_bubbles.clear()
        self.powerups.clear()
        self.item_spawn_timer = random.uniform(6.0, 12.0)

        # Reposition players to randomized distinct platform spawn points
        random_spawns = self.level_mgr.get_distinct_platform_spawns(len(self.players))
        for i, p in enumerate(self.players):
            sp = random_spawns[i] if i < len(random_spawns) else self.level_mgr.spawn_points.get(i, (40 + i * 100, 50))
            p.reset_for_round(sp[0], sp[1])

        # Flag setup for CTF
        if self.current_mode_name == MODE_CTF:
            fx, fy = self.level_mgr.flag_spawn
            self.flag = Flag(fx, fy)
        else:
            self.flag = None

        self.game_mode.match_duration = self.round_match_time
        self.game_mode.min_round_duration = self.min_round_duration
        self.game_mode.start_round(self.players)
        self.sound_mgr.start_bgm(fast=False)
        self.round_transition_timer = 2.5
        self.round_transition_text = f"ROUND {self.current_round} OF {self.total_rounds}"
        self.state = STATE_PLAYING

    def start_next_round(self):
        """Advances to next round of the match, preserving cumulative player scores and statistics."""
        self.level_mgr.load_random_level()
        self.bubbles.clear()
        self.trapped_bubbles.clear()
        self.powerups.clear()
        self.item_spawn_timer = random.uniform(6.0, 12.0)

        # Reposition players to randomized distinct platform spawn points (keeping scores and stats intact)
        random_spawns = self.level_mgr.get_distinct_platform_spawns(len(self.players))
        for i, p in enumerate(self.players):
            sp = random_spawns[i] if i < len(random_spawns) else self.level_mgr.spawn_points.get(i, (40 + i * 100, 50))
            p.reset_for_round(sp[0], sp[1])

        # Flag setup for CTF
        if self.current_mode_name == MODE_CTF:
            fx, fy = self.level_mgr.flag_spawn
            self.flag = Flag(fx, fy)
        else:
            self.flag = None

        self.game_mode.match_duration = self.round_match_time
        self.game_mode.min_round_duration = self.min_round_duration
        self.game_mode.start_round(self.players, reset_scores=False)
        self.sound_mgr.start_bgm(fast=False)
        self.round_transition_timer = 2.5
        self.round_transition_text = f"ROUND {self.current_round} OF {self.total_rounds}"
        self.sound_mgr.play_sfx("victory")
        self.state = STATE_PLAYING

    def run(self):
        """Main game loop with fixed delta-time capping."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # Cap delta time to prevent tunneling

            self.handle_events()
            self.update(dt)
            self.render(dt)

        # Clean shutdown
        if self.lan_server:
            self.lan_server.stop()
        if self.lan_client:
            self.lan_client.disconnect()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        """Dispatches keyboard, mouse, and window events based on active state."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if self.state == STATE_MENU:
                action = self.menu.handle_navigation(event, len(self.menu.main_options))
                if action == "MOVE":
                    self.sound_mgr.play_sfx("select")
                elif action == "SELECT":
                    self.sound_mgr.play_sfx("select")
                    idx = self.menu.selected_idx
                    if idx == 0:  # Start Local Match -> Ask how many human players
                        self.menu.selected_idx = 0
                        self.state = STATE_PLAYER_COUNT
                    elif idx == 1:  # Select Mode
                        self.menu.selected_idx = GAME_MODES.index(self.current_mode_name) if self.current_mode_name in GAME_MODES else 0
                        self.state = STATE_MODE_SELECT
                    elif idx == 2:  # Select Level
                        self.menu.selected_idx = self.level_mgr.current_level_idx
                        self.state = STATE_LEVEL_SELECT
                    elif idx == 3:  # Game Settings
                        self.menu.selected_idx = 0
                        self.state = STATE_SETTINGS
                    elif idx == 4:  # LAN Multiplayer
                        self.menu.selected_idx = 0
                        self.state = STATE_LOBBY
                    elif idx == 5:  # Controls
                        self.state = STATE_CONTROLS
                    elif idx == 6:  # Quit
                        self.running = False

            elif self.state == STATE_SETTINGS:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.menu.selected_idx = (self.menu.selected_idx - 1) % 8
                        self.sound_mgr.play_sfx("select")
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.menu.selected_idx = (self.menu.selected_idx + 1) % 8
                        self.sound_mgr.play_sfx("select")
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        if self.menu.selected_idx == 0:  # Game Speed
                            self.speed_idx = (self.speed_idx - 1) % len(SPEED_OPTIONS)
                            self.game_speed_mult = SPEED_OPTIONS[self.speed_idx][1]
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 1:  # Rounds count
                            self.total_rounds = max(1, self.total_rounds - 1)
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 2:  # Music Volume
                            self.music_vol_idx = (self.music_vol_idx - 1) % len(MUSIC_VOLUME_OPTIONS)
                            self.sound_mgr.set_music_volume(MUSIC_VOLUME_OPTIONS[self.music_vol_idx][1])
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 3:  # SFX Volume
                            self.sfx_vol_idx = (self.sfx_vol_idx - 1) % len(SFX_VOLUME_OPTIONS)
                            self.sound_mgr.set_sfx_volume(SFX_VOLUME_OPTIONS[self.sfx_vol_idx][1])
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 4:  # Min Stage Duration
                            self.min_duration_idx = (self.min_duration_idx - 1) % len(MIN_DURATION_OPTIONS)
                            self.min_round_duration = MIN_DURATION_OPTIONS[self.min_duration_idx][1]
                            self.game_mode.min_round_duration = self.min_round_duration
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 5:  # Round Time Limit
                            self.round_timer_idx = (self.round_timer_idx - 1) % len(ROUND_TIMER_OPTIONS)
                            self.round_match_time = ROUND_TIMER_OPTIONS[self.round_timer_idx][1]
                            self.game_mode.match_duration = self.round_match_time
                            self.game_mode.match_time_remaining = self.round_match_time
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 6:  # Bot Personalities
                            self.bot_personality_idx = (self.bot_personality_idx - 1) % len(BOT_PREFERENCE_OPTIONS)
                            self.sound_mgr.play_sfx("select")
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        if self.menu.selected_idx == 0:  # Game Speed
                            self.speed_idx = (self.speed_idx + 1) % len(SPEED_OPTIONS)
                            self.game_speed_mult = SPEED_OPTIONS[self.speed_idx][1]
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 1:  # Rounds count
                            self.total_rounds = min(10, self.total_rounds + 1)
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 2:  # Music Volume
                            self.music_vol_idx = (self.music_vol_idx + 1) % len(MUSIC_VOLUME_OPTIONS)
                            self.sound_mgr.set_music_volume(MUSIC_VOLUME_OPTIONS[self.music_vol_idx][1])
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 3:  # SFX Volume
                            self.sfx_vol_idx = (self.sfx_vol_idx + 1) % len(SFX_VOLUME_OPTIONS)
                            self.sound_mgr.set_sfx_volume(SFX_VOLUME_OPTIONS[self.sfx_vol_idx][1])
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 4:  # Min Stage Duration
                            self.min_duration_idx = (self.min_duration_idx + 1) % len(MIN_DURATION_OPTIONS)
                            self.min_round_duration = MIN_DURATION_OPTIONS[self.min_duration_idx][1]
                            self.game_mode.min_round_duration = self.min_round_duration
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 5:  # Round Time Limit
                            self.round_timer_idx = (self.round_timer_idx + 1) % len(ROUND_TIMER_OPTIONS)
                            self.round_match_time = ROUND_TIMER_OPTIONS[self.round_timer_idx][1]
                            self.game_mode.match_duration = self.round_match_time
                            self.game_mode.match_time_remaining = self.round_match_time
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 6:  # Bot Personalities
                            self.bot_personality_idx = (self.bot_personality_idx + 1) % len(BOT_PREFERENCE_OPTIONS)
                            self.sound_mgr.play_sfx("select")
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_f):
                        if self.menu.selected_idx == 7:  # Back to Main Menu
                            self.menu.selected_idx = 0
                            self.state = STATE_MENU
                            self.sound_mgr.play_sfx("select")
                        else:
                            # Forward cycle option on Enter / Action
                            if self.menu.selected_idx == 0:
                                self.speed_idx = (self.speed_idx + 1) % len(SPEED_OPTIONS)
                                self.game_speed_mult = SPEED_OPTIONS[self.speed_idx][1]
                            elif self.menu.selected_idx == 1:
                                self.total_rounds = 1 if self.total_rounds >= 10 else self.total_rounds + 1
                            elif self.menu.selected_idx == 2:
                                self.music_vol_idx = (self.music_vol_idx + 1) % len(MUSIC_VOLUME_OPTIONS)
                                self.sound_mgr.set_music_volume(MUSIC_VOLUME_OPTIONS[self.music_vol_idx][1])
                            elif self.menu.selected_idx == 3:
                                self.sfx_vol_idx = (self.sfx_vol_idx + 1) % len(SFX_VOLUME_OPTIONS)
                                self.sound_mgr.set_sfx_volume(SFX_VOLUME_OPTIONS[self.sfx_vol_idx][1])
                            elif self.menu.selected_idx == 4:
                                self.min_duration_idx = (self.min_duration_idx + 1) % len(MIN_DURATION_OPTIONS)
                                self.min_round_duration = MIN_DURATION_OPTIONS[self.min_duration_idx][1]
                                self.game_mode.min_round_duration = self.min_round_duration
                            elif self.menu.selected_idx == 5:
                                self.round_timer_idx = (self.round_timer_idx + 1) % len(ROUND_TIMER_OPTIONS)
                                self.round_match_time = ROUND_TIMER_OPTIONS[self.round_timer_idx][1]
                                self.game_mode.match_duration = self.round_match_time
                                self.game_mode.match_time_remaining = self.round_match_time
                            elif self.menu.selected_idx == 6:
                                self.bot_personality_idx = (self.bot_personality_idx + 1) % len(BOT_PREFERENCE_OPTIONS)
                            self.sound_mgr.play_sfx("select")
                    elif event.key == pygame.K_ESCAPE:
                        self.menu.selected_idx = 0
                        self.state = STATE_MENU
                        self.sound_mgr.play_sfx("select")


            elif self.state == STATE_PLAYER_COUNT:
                action = self.menu.handle_navigation(event, 4)
                if action == "MOVE":
                    self.sound_mgr.play_sfx("select")
                elif action == "SELECT":
                    human_count = self.menu.selected_idx + 1  # 1, 2, 3, or 4
                    self.setup_players_by_human_count(human_count)
                    self.sound_mgr.play_sfx("select")
                    self.start_match()
                elif action == "BACK":
                    self.menu.selected_idx = 0
                    self.state = STATE_MENU

            elif self.state == STATE_MODE_SELECT:
                action = self.menu.handle_navigation(event, 3)
                if action == "MOVE":
                    self.sound_mgr.play_sfx("select")
                elif action == "SELECT":
                    modes = [MODE_FFA, MODE_TEAM, MODE_CTF]
                    self.set_game_mode(modes[self.menu.selected_idx])
                    self.sound_mgr.play_sfx("select")
                    self.menu.selected_idx = 0
                    self.state = STATE_MENU
                elif action == "BACK":
                    self.menu.selected_idx = 0
                    self.state = STATE_MENU

            elif self.state == STATE_LEVEL_SELECT:
                count = self.level_mgr.get_level_count()
                per_page = 14
                rows_per_col = 7
                total_pages = max(1, (count + per_page - 1) // per_page)
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        cur_col = (self.menu.selected_idx % per_page) // rows_per_col
                        cur_row = (self.menu.selected_idx % per_page) % rows_per_col
                        new_row = (cur_row - 1) % rows_per_col
                        page_start = (self.menu.selected_idx // per_page) * per_page
                        candidate = page_start + cur_col * rows_per_col + new_row
                        if candidate < count:
                            self.menu.selected_idx = candidate
                        self.sound_mgr.play_sfx("select")
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        cur_col = (self.menu.selected_idx % per_page) // rows_per_col
                        cur_row = (self.menu.selected_idx % per_page) % rows_per_col
                        new_row = (cur_row + 1) % rows_per_col
                        page_start = (self.menu.selected_idx // per_page) * per_page
                        candidate = page_start + cur_col * rows_per_col + new_row
                        if candidate < count:
                            self.menu.selected_idx = candidate
                        self.sound_mgr.play_sfx("select")
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        cur_col = (self.menu.selected_idx % per_page) // rows_per_col
                        if cur_col == 1:
                            self.menu.selected_idx -= rows_per_col
                        else:
                            # Flip to previous page, column 1
                            cur_page = self.menu.selected_idx // per_page
                            prev_page = (cur_page - 1) % total_pages
                            row_offset = (self.menu.selected_idx % per_page) % rows_per_col
                            candidate = prev_page * per_page + rows_per_col + row_offset
                            if candidate >= count:
                                candidate = prev_page * per_page + row_offset
                            self.menu.selected_idx = min(count - 1, candidate)
                        self.sound_mgr.play_sfx("select")
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        cur_col = (self.menu.selected_idx % per_page) // rows_per_col
                        if cur_col == 0 and (self.menu.selected_idx + rows_per_col) < count:
                            self.menu.selected_idx += rows_per_col
                        else:
                            # Flip to next page, column 0
                            cur_page = self.menu.selected_idx // per_page
                            next_page = (cur_page + 1) % total_pages
                            row_offset = (self.menu.selected_idx % per_page) % rows_per_col
                            candidate = next_page * per_page + row_offset
                            self.menu.selected_idx = min(count - 1, candidate)
                        self.sound_mgr.play_sfx("select")
                    elif event.key in (pygame.K_PAGEUP, pygame.K_TAB):
                        cur_page = self.menu.selected_idx // per_page
                        new_page = (cur_page - 1) % total_pages
                        local_idx = self.menu.selected_idx % per_page
                        candidate = new_page * per_page + local_idx
                        self.menu.selected_idx = min(count - 1, candidate)
                        self.sound_mgr.play_sfx("select")
                    elif event.key == pygame.K_PAGEDOWN:
                        cur_page = self.menu.selected_idx // per_page
                        new_page = (cur_page + 1) % total_pages
                        local_idx = self.menu.selected_idx % per_page
                        candidate = new_page * per_page + local_idx
                        self.menu.selected_idx = min(count - 1, candidate)
                        self.sound_mgr.play_sfx("select")
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_f):
                        self.level_mgr.load_level(self.menu.selected_idx)
                        self.sound_mgr.play_sfx("select")
                        self.menu.selected_idx = 0
                        self.state = STATE_MENU
                    elif event.key == pygame.K_ESCAPE:
                        self.menu.selected_idx = 0
                        self.state = STATE_MENU

            elif self.state == STATE_CONTROLS:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_f):
                    self.sound_mgr.play_sfx("select")
                    self.state = STATE_MENU

            elif self.state == STATE_LOBBY:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        if self.menu.selected_idx == 0 and self.net_interfaces:
                            self.selected_iface_idx = (self.selected_iface_idx - 1) % len(self.net_interfaces)
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 3:
                            targets = ["127.0.0.1"] + [h[0] for h in self.found_hosts if h[0] != "127.0.0.1"] + [ip for ip in self.net_interfaces if ip != "127.0.0.1"]
                            self.remote_ip_idx = (self.remote_ip_idx - 1) % len(targets)
                            self.target_remote_ip = targets[self.remote_ip_idx]
                            self.sound_mgr.play_sfx("select")
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        if self.menu.selected_idx == 0 and self.net_interfaces:
                            self.selected_iface_idx = (self.selected_iface_idx + 1) % len(self.net_interfaces)
                            self.sound_mgr.play_sfx("select")
                        elif self.menu.selected_idx == 3:
                            targets = ["127.0.0.1"] + [h[0] for h in self.found_hosts if h[0] != "127.0.0.1"] + [ip for ip in self.net_interfaces if ip != "127.0.0.1"]
                            self.remote_ip_idx = (self.remote_ip_idx + 1) % len(targets)
                            self.target_remote_ip = targets[self.remote_ip_idx]
                            self.sound_mgr.play_sfx("select")

                action = self.menu.handle_navigation(event, 5)
                if action == "MOVE":
                    self.sound_mgr.play_sfx("select")
                elif action == "SELECT":
                    idx = self.menu.selected_idx
                    if idx == 0:  # Cycle Interface
                        if self.net_interfaces:
                            self.selected_iface_idx = (self.selected_iface_idx + 1) % len(self.net_interfaces)
                            self.sound_mgr.play_sfx("select")
                    elif idx == 1:  # Host Match -> Enter LAN Room Lobby
                        selected_ip = self.net_interfaces[self.selected_iface_idx] if self.net_interfaces else "127.0.0.1"
                        if not self.lan_server:
                            self.lan_server = LANServer(selected_ip=selected_ip)
                            self.lan_server.start()
                        self.is_lan_host = True
                        self.is_lan_client = False
                        self.state = STATE_LAN_ROOM
                        self.net_status_msg = f"Hosting on {selected_ip}:{DEFAULT_PORT}"
                        self.sound_mgr.play_sfx("select")
                    elif idx == 2:  # Auto-Discover
                        self.net_status_msg = "Scanning LAN for hosts..."
                        self.found_hosts = LANClient.discover_hosts(timeout=1.5)
                        if self.found_hosts:
                            host_ip, host_port = self.found_hosts[0]
                            self.target_remote_ip = f"{host_ip}:{host_port}"
                            self.lan_client = LANClient()
                            if self.lan_client.connect(host_ip, host_port):
                                self.is_lan_client = True
                                self.is_lan_host = False
                                self.state = STATE_LAN_ROOM
                                self.net_status_msg = f"Connected to {host_ip}:{host_port}!"
                                self.sound_mgr.play_sfx("select")
                            else:
                                self.net_status_msg = "Connection failed."
                        else:
                            self.net_status_msg = "No LAN hosts found."
                    elif idx == 3:  # Direct Connect to target_remote_ip (LAN or Internet)
                        self.lan_client = LANClient()
                        target = self.target_remote_ip
                        if self.lan_client.connect(target):
                            self.is_lan_client = True
                            self.is_lan_host = False
                            self.state = STATE_LAN_ROOM
                            self.net_status_msg = f"Connected to {target}!"
                            self.sound_mgr.play_sfx("select")
                        else:
                            err = getattr(self.lan_client, "kick_reason", None) or f"Could not connect to {target}"
                            self.net_status_msg = err
                    elif idx == 4:  # Return
                        self.state = STATE_MENU
                elif action == "BACK":
                    self.state = STATE_MENU

            elif self.state == STATE_LAN_ROOM:
                if event.type == pygame.KEYDOWN:
                    if self.is_chat_active:
                        if event.key == pygame.K_ESCAPE:
                            self.is_chat_active = False
                        elif event.key == pygame.K_RETURN:
                            # Send broadcast chat
                            if self.lan_chat_input.strip():
                                if self.is_lan_host and self.lan_server:
                                    self.lan_server.send_host_chat(self.lan_chat_input)
                                elif self.is_lan_client and self.lan_client:
                                    self.lan_client.send_chat(self.lan_chat_input)
                                self.lan_chat_input = ""
                                self.sound_mgr.play_sfx("select")
                        elif event.key == pygame.K_BACKSPACE:
                            self.lan_chat_input = self.lan_chat_input[:-1]
                        else:
                            if event.unicode and len(self.lan_chat_input) < 32 and event.unicode.isprintable():
                                self.lan_chat_input += event.unicode
                    else:
                        if event.key in (pygame.K_TAB, pygame.K_c):
                            self.is_chat_active = True
                        elif event.key in (pygame.K_r, pygame.K_SPACE):
                            # Toggle Ready
                            if self.is_lan_host and self.lan_server:
                                self.lan_server.toggle_host_ready()
                                self.sound_mgr.play_sfx("select")
                            elif self.is_lan_client and self.lan_client:
                                self.lan_client.send_ready_toggle()
                                self.sound_mgr.play_sfx("select")
                        elif self.is_lan_host and event.key == pygame.K_b:
                            # Host shortcut to fill open slots with bots
                            if self.lan_server:
                                self.lan_server.fill_all_bots()
                                self.sound_mgr.play_sfx("select")
                        elif self.is_lan_host and event.key == pygame.K_m:
                            # Host shortcut to cycle Game Mode in LAN Room
                            if self.lan_server:
                                new_mode = self.lan_server.cycle_game_mode()
                                self.set_game_mode(new_mode)
                                self.sound_mgr.play_sfx("select")
                        elif event.key == pygame.K_ESCAPE:
                            # Leave LAN Room
                            if self.is_lan_host and self.lan_server:
                                self.lan_server.stop()
                                self.lan_server = None
                                self.is_lan_host = False
                            if self.is_lan_client and self.lan_client:
                                self.lan_client.disconnect()
                                self.lan_client = None
                                self.is_lan_client = False
                            self.state = STATE_LOBBY

            elif self.state == STATE_PLAYING:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = STATE_PAUSED
                    self.sound_mgr.stop_bgm()

            elif self.state == STATE_PAUSED:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = STATE_PLAYING
                        self.sound_mgr.start_bgm(fast=self.game_mode.is_hurry_up)
                    elif event.key == pygame.K_q:
                        self.state = STATE_MENU

            elif self.state == STATE_VICTORY:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_f):
                        self.sound_mgr.play_sfx("select")
                        self.start_match()
                    elif event.key == pygame.K_ESCAPE:
                        self.sound_mgr.play_sfx("select")
                        self.state = STATE_MENU

    def trigger_chain_pop(self, initial_bubble, popping_player=None):
        """
        Triggers a chain reaction explosion when a bubble is popped by a player or expires:
        Pops all touching/connected bubbles in cascade and awards combo multipliers!
        """
        queue = [initial_bubble]
        popped_bubbles = []
        popped_trapped = []

        is_team_mode = (self.current_mode_name != MODE_FFA)
        chain_count = 0

        while queue:
            current = queue.pop(0)
            if current in popped_bubbles or current in popped_trapped:
                continue

            chain_count += 1
            if isinstance(current, TrappedBubble):
                popped_trapped.append(current)
            else:
                popped_bubbles.append(current)

            # Find all touching / connected bubbles in proximity
            all_remaining = [b for b in self.bubbles if b not in popped_bubbles and b not in queue]
            # Trapped bubbles only chain-pop if an active other player initiated the pop
            if popping_player is not None:
                all_remaining_trapped = [
                    tb for tb in self.trapped_bubbles
                    if tb not in popped_trapped and tb not in queue and tb.trapped_player.id != popping_player.id
                ]
            else:
                all_remaining_trapped = []

            for other in (all_remaining + all_remaining_trapped):
                dx = current.x - other.x
                dy = current.y - other.y
                dist = math.hypot(dx, dy)
                # Touching threshold: radius sum + contact tolerance margin
                if dist <= (current.radius + other.radius + 8):
                    queue.append(other)

        # Process all chained standard bubbles
        for b in popped_bubbles:
            b.is_alive = False
            self.particle_mgr.spawn_pop_burst(b.x, b.y, count=12)
            self.sound_mgr.play_sfx("pop")

            # Award chain combo points to popping player
            if popping_player:
                pts = min(1600, 100 * (2 ** min(chain_count - 1, 4)))
                popping_player.score += pts
                if chain_count >= 2:
                    self.particle_mgr.add_floating_text(f"+{pts} (CHAIN x{chain_count})", b.x, b.y - 12, color=COLOR_GOLD)

            # 35% chance to drop bonus fruits/gems in chain explosion!
            if random.random() < 0.35:
                self.powerups.append(PowerUp(b.x, b.y))

        # Process all chained trapped bubbles
        for tb in popped_trapped:
            if popping_player and popping_player.id != tb.trapped_player.id:
                tb.is_alive = False
                result = tb.check_pop_by_player(popping_player, is_team_mode=is_team_mode, force_pop=True)
                if result:
                    res_type, points = result
                    combo_pts = points + (chain_count * 100)
                    self.game_mode.on_player_popped(popping_player, tb, res_type, combo_pts)

                    if res_type == "KILL":
                        self.particle_mgr.spawn_pop_burst(tb.x, tb.y, count=18)
                        self.particle_mgr.add_floating_text(f"+{combo_pts} POP!", tb.x, tb.y - 14, color=COLOR_RED)
                        self.sound_mgr.play_sfx("pop")
                        self.sound_mgr.play_sfx("death")
                        # 70% chance to drop bonus item on kill
                        if random.random() < 0.70:
                            self.powerups.append(PowerUp(tb.x, tb.y))
                    elif res_type == "RESCUE":
                        self.particle_mgr.spawn_sparkles(tb.x, tb.y, count=14)
                        self.particle_mgr.add_floating_text(f"RESCUE +{combo_pts}!", tb.x, tb.y - 14, color=COLOR_GREEN)
                        self.sound_mgr.play_sfx("rescue")
            else:
                # Expired naturally after full lifespan
                if tb.age >= tb.lifespan:
                    tb.is_alive = False
                    tb.trapped_player.free_from_bubble(was_rescued=False)
                    self.particle_mgr.spawn_pop_burst(tb.x, tb.y, count=12)
                    self.sound_mgr.play_sfx("pop")

        # Big banner if massive chain explosion!
        if chain_count >= 3 and popping_player:
            self.particle_mgr.add_floating_text(f"CHAIN COMBO x{chain_count}!", popping_player.x, popping_player.y - 22, color=COLOR_GOLD)
            self.sound_mgr.play_sfx("victory")

        # Filter out all popped bubbles from active lists
        self.bubbles = [b for b in self.bubbles if b not in popped_bubbles]
        self.trapped_bubbles = [tb for tb in self.trapped_bubbles if tb not in popped_trapped]

    def update(self, dt):
        """Updates game state, physics, collisions, and network sync."""
        if self.state == STATE_LAN_ROOM:
            # Synchronize room state and broadcast chat
            if self.is_lan_host and self.lan_server:
                self.room_slots = self.lan_server.lobby_slots
                self.room_chat_history = self.lan_server.chat_history

                # When all 4 players are ready -> auto start the match!
                if self.lan_server.is_all_players_ready():
                    self.set_game_mode(self.lan_server.game_mode_name)
                    self.lan_server.broadcast_match_start()
                    for i in range(4):
                        slot = self.lan_server.lobby_slots[i]
                        is_bot = (slot["type"] == "bot")
                        self.players[i].is_bot = is_bot
                        if is_bot:
                            pers = slot.get("personality", "Standard")
                            self.players[i].personality = pers
                            self.players[i].name = f"{PLAYER_COLORS[i]['name']} [{pers}]"
                    self.state = STATE_PLAYING
                    self.sound_mgr.play_sfx("victory")
                    self.start_match()

            elif self.is_lan_client and self.lan_client:
                if not self.lan_client.is_connected:
                    reason = getattr(self.lan_client, "kick_reason", None) or "Disconnected from server."
                    self.net_status_msg = f"[DISCONNECT] {reason}"
                    self.lan_client = None
                    self.is_lan_client = False
                    self.state = STATE_LOBBY
                    return

                self.room_slots = self.lan_client.get_lobby_slots()
                self.room_chat_history = self.lan_client.get_chat_history()
                if self.lan_client.is_match_started():
                    synced_mode = getattr(self.lan_client, "match_game_mode", MODE_FFA)
                    self.set_game_mode(synced_mode)
                    for i in range(4):
                        slot = self.room_slots.get(i, {})
                        is_bot = (slot.get("type") == "bot")
                        self.players[i].is_bot = is_bot
                        if is_bot:
                            pers = slot.get("personality", "Standard")
                            self.players[i].personality = pers
                            self.players[i].name = f"{PLAYER_COLORS[i]['name']} [{pers}]"
                    self.state = STATE_PLAYING
                    self.sound_mgr.play_sfx("victory")
                    self.start_match()
            return

        if self.state != STATE_PLAYING:
            return

        if self.round_transition_timer > 0:
            self.round_transition_timer = max(0.0, self.round_transition_timer - dt)

        dt = dt * self.game_speed_mult

        platforms = self.level_mgr.platforms

        # 1. LAN Network Input Synchronization
        if self.is_lan_host and self.lan_server:
            client_inputs = self.lan_server.get_client_inputs()
            for p_id, acts in client_inputs.items():
                self.input_handler.set_remote_input(p_id, acts)

        # 2. Player Input & Physics
        spawned_bubbles = []
        for p in self.players:
            if p.is_trapped:
                # Clear bot actions when trapped
                if p.is_bot:
                    p.bot_action = {}
                # Check struggle inputs (cosmetic struggle wobble)
                actions = self.input_handler.poll_inputs(p.id, is_bot=p.is_bot, bot_action=p.bot_action)
                if actions.get("shoot") or actions.get("struggle") or actions.get("jump"):
                    # Find player's trapped bubble
                    for tb in self.trapped_bubbles:
                        if tb.trapped_player.id == p.id:
                            tb.register_struggle()
                            break
            else:
                # Bot AI or Human Input
                if p.is_bot:
                    bot_act = p.update_bot_ai(
                        dt, self.players, self.bubbles, self.trapped_bubbles,
                        flag=self.flag, powerups=self.powerups, game_mode=self.current_mode_name, level_mgr=self.level_mgr
                    )
                    p.handle_input(bot_act, dt, spawned_bubbles, self.sound_mgr, self.particle_mgr)
                else:
                    user_act = self.input_handler.poll_inputs(p.id)
                    p.handle_input(user_act, dt, spawned_bubbles, self.sound_mgr, self.particle_mgr)

                    # If client connected over LAN, transmit input
                    if self.is_lan_client and self.lan_client and p.id == self.lan_client.assigned_player_id:
                        self.lan_client.send_input(user_act)

            p.update(dt, platforms, self.bubbles, self.trapped_bubbles, self.sound_mgr, self.particle_mgr, level_mgr=self.level_mgr)

        self.bubbles.extend(spawned_bubbles)

        # 3. Update Bubbles & Opponent Trapping
        active_bubbles = []
        bubbles_to_pop = []

        for b in list(self.bubbles):
            if not b.update(dt, platforms):
                # Bubble popped from 30s timeout
                bubbles_to_pop.append((b, None))
                continue

            # Empty floating bubbles do NOT pop when jumped on; they serve as bouncy trampolines.

            # Check collision with other players to trap them
            trapped_someone = False
            for target_p in self.players:
                if target_p.id != b.owner_id and target_p.is_alive and not target_p.is_trapped and target_p.invulnerable_timer <= 0:
                    # In team mode, only trap enemies
                    is_enemy = (self.current_mode_name == MODE_FFA) or (target_p.team != b.owner_team)
                    if is_enemy and b.rect.colliderect(target_p.rect):
                        # TRAP THE PLAYER!
                        target_p.bot_action = {}
                        target_p.vx = 0.0
                        target_p.vy = 0.0
                        tb = TrappedBubble(target_p, b.owner_id, b.owner_team)
                        self.trapped_bubbles.append(tb)
                        self.particle_mgr.spawn_sparkles(target_p.x, target_p.y, count=10)
                        self.particle_mgr.add_floating_text("TRAPPED!", target_p.x, target_p.y - 12)
                        self.sound_mgr.play_sfx("trap")
                        trapped_someone = True
                        break

            if not trapped_someone and b not in [bp[0] for bp in bubbles_to_pop]:
                active_bubbles.append(b)

        self.bubbles = active_bubbles

        # Trigger chain pops for empty bubbles
        for b, popper in bubbles_to_pop:
            self.trigger_chain_pop(b, popper)

        # 4. Update Trapped Bubbles & Popping / Rescue Check with Chain Reactions
        active_trapped = []
        trapped_to_pop = []

        for tb in list(self.trapped_bubbles):
            if not tb.update(dt, platforms):
                # Expired naturally after 30s lifespan
                trapped_to_pop.append((tb, None))
                continue

            # Check if any other active player touches this trapped bubble to pop it
            popped_by_player = None
            for p in self.players:
                if p.is_alive and not p.is_trapped and p.id != tb.trapped_player.id and tb.rect.colliderect(p.rect):
                    popped_by_player = p
                    break

            if popped_by_player:
                # If popping player jumped or fell on the trapped bubble from above, bounce them up!
                if popped_by_player.vy >= -40.0 and popped_by_player.rect.bottom <= tb.rect.centery + 6:
                    popped_by_player.vy = BUBBLE_BOUNCE_SPEED
                    popped_by_player.bubble_ride_timer = 0.35
                    self.sound_mgr.play_sfx("bounce")
                trapped_to_pop.append((tb, popped_by_player))
            else:
                active_trapped.append(tb)

        self.trapped_bubbles = active_trapped

        # Trigger chain pops for trapped bubbles
        for tb, popper in trapped_to_pop:
            self.trigger_chain_pop(tb, popper)

        # 5. Power-Up Spawning & Collection
        self.item_spawn_timer -= dt
        if self.item_spawn_timer <= 0.0:
            self.item_spawn_timer = random.uniform(10.0, 18.0)
            rx = random.uniform(50, VIRTUAL_WIDTH - 50)
            ry = random.uniform(60.0, 120.0)
            self.powerups.append(PowerUp(rx, ry))

        active_powerups = []
        for pw in self.powerups:
            if not pw.update(dt, platforms):
                continue
            collected = False
            for p in self.players:
                if p.is_alive and not p.is_trapped and pw.rect.colliderect(p.rect):
                    tag, pts = pw.apply_to_player(p)
                    p.score += pts
                    self.particle_mgr.spawn_sparkles(p.x, p.y, count=8)
                    self.particle_mgr.add_floating_text(tag, p.x, p.y - 12)
                    self.sound_mgr.play_sfx("powerup")
                    collected = True
                    break
            if not collected:
                active_powerups.append(pw)
        self.powerups = active_powerups

        # 6. CTF Flag Update
        if self.flag:
            self.flag.update(dt)
            # Check pickup
            if self.flag.carrier is None:
                for p in self.players:
                    if p.is_alive and not p.is_trapped and self.flag.rect.colliderect(p.rect):
                        if self.flag.pickup(p):
                            self.particle_mgr.add_floating_text("FLAG TAKEN!", p.x, p.y - 14)
                            self.sound_mgr.play_sfx("flag")
                            break

        # 7. Match Mode Rules & Timer Countdown
        self.game_mode.update(dt, self.players, self.flag, self.sound_mgr)
        if self.game_mode.is_match_over:
            if self.current_round < self.total_rounds:
                self.current_round += 1
                self.start_next_round()
            else:
                self.state = STATE_VICTORY
                self.sound_mgr.stop_bgm()

        # 8. Particle System
        self.particle_mgr.update(dt)

    def render(self, dt):
        """Renders the game scene to virtual surface and scales up to window."""
        self.virtual_screen.fill((16, 16, 26))

        if self.state == STATE_MENU:
            self.menu.draw_title_screen(self.virtual_screen, self.sprite_mgr, self.current_mode_name, self.level_mgr.level_name, dt)

        elif self.state == STATE_PLAYER_COUNT:
            self.menu.draw_player_count_select(self.virtual_screen, dt)

        elif self.state == STATE_MODE_SELECT:
            self.menu.draw_mode_select(self.virtual_screen, self.menu.selected_idx, dt)

        elif self.state == STATE_LEVEL_SELECT:
            self.menu.draw_level_select(self.virtual_screen, self.level_mgr, dt)

        elif self.state == STATE_SETTINGS:
            self.menu.draw_settings_screen(
                self.virtual_screen,
                SPEED_OPTIONS[self.speed_idx][0],
                self.total_rounds,
                dt,
                music_vol_name=MUSIC_VOLUME_OPTIONS[self.music_vol_idx][0],
                sfx_vol_name=SFX_VOLUME_OPTIONS[self.sfx_vol_idx][0],
                min_duration_name=MIN_DURATION_OPTIONS[self.min_duration_idx][0],
                round_timer_name=ROUND_TIMER_OPTIONS[self.round_timer_idx][0],
                bot_pref_name=BOT_PREFERENCE_OPTIONS[self.bot_personality_idx][0]
            )

        elif self.state == STATE_CONTROLS:
            self.menu.draw_controls(self.virtual_screen)

        elif self.state == STATE_LOBBY:
            selected_ip = self.net_interfaces[self.selected_iface_idx] if self.net_interfaces else "127.0.0.1"
            self.menu.draw_lan_lobby(
                self.virtual_screen, selected_ip, self.net_interfaces,
                self.selected_iface_idx, self.found_hosts, self.is_lan_host,
                self.is_lan_client, self.net_status_msg,
                target_remote_ip=getattr(self, "target_remote_ip", "127.0.0.1")
            )

        elif self.state == STATE_LAN_ROOM:
            my_id = 0 if self.is_lan_host else (self.lan_client.assigned_player_id if self.lan_client and self.lan_client.assigned_player_id is not None else 1)
            current_mode = self.lan_server.game_mode_name if self.is_lan_host and self.lan_server else (
                self.lan_client.lobby_game_mode if self.is_lan_client and self.lan_client else self.current_mode_name
            )
            self.menu.draw_lan_room_lobby(
                self.virtual_screen,
                self.room_slots,
                self.room_chat_history,
                self.lan_chat_input,
                self.is_chat_active,
                self.is_lan_host,
                my_id,
                self.net_status_msg,
                dt,
                game_mode=current_mode
            )

        elif self.state in (STATE_PLAYING, STATE_PAUSED, STATE_VICTORY):
            # Render Platforms
            for plat in self.level_mgr.platforms:
                plat.draw(self.virtual_screen, self.sprite_mgr)

            # Render CTF Flag
            if self.flag:
                self.flag.draw(self.virtual_screen, self.sprite_mgr)

            # Render Power-Ups
            for pw in self.powerups:
                pw.draw(self.virtual_screen, self.sprite_mgr)

            # Render Bubbles
            for b in self.bubbles:
                b.draw(self.virtual_screen, self.sprite_mgr)

            # Render Players
            for p in self.players:
                p.draw(self.virtual_screen, self.sprite_mgr)

            # Render Trapped Bubbles
            for tb in self.trapped_bubbles:
                tb.draw(self.virtual_screen, self.sprite_mgr)

            # Render Particles & Popups
            self.particle_mgr.draw(self.virtual_screen)

            # Render Top HUD
            self.hud.draw(
                self.virtual_screen, self.players, self.game_mode.match_time_remaining,
                self.current_mode_name, self.level_mgr.level_name, self.flag,
                current_round=self.current_round, total_rounds=self.total_rounds
            )

            # Round Transition Banner
            if self.round_transition_timer > 0:
                banner_surf = pygame.Surface((240, 32), pygame.SRCALPHA)
                banner_surf.fill((12, 16, 32, 220))
                pygame.draw.rect(banner_surf, COLOR_GOLD, (0, 0, 240, 32), 2, border_radius=6)
                r_txt = self.menu.font_title.render(self.round_transition_text, True, (255, 230, 70))
                banner_surf.blit(r_txt, r_txt.get_rect(center=(120, 16)))
                self.virtual_screen.blit(banner_surf, banner_surf.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 25)))

            # Pause Overlay
            if self.state == STATE_PAUSED:
                p_overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
                p_overlay.fill((0, 0, 0, 160))
                self.virtual_screen.blit(p_overlay, (0, 0))
                p_txt = self.menu.font_title.render("PAUSED", True, (255, 220, 50))
                p_sub = self.menu.font_info.render("[ESC] Resume   [Q] Quit to Menu", True, (255, 255, 255))
                self.virtual_screen.blit(p_txt, p_txt.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 12)))
                self.virtual_screen.blit(p_sub, p_sub.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 16)))

            # Victory / Match Over Overlay
            if self.state == STATE_VICTORY:
                self.menu.draw_victory_screen(
                    self.virtual_screen, self.game_mode.winner_info,
                    self.players, self.current_mode_name, dt
                )

        # Scale virtual screen (480x320) to window (960x640)
        scaled = pygame.transform.scale(self.virtual_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.window.blit(scaled, (0, 0))
        pygame.display.flip()
