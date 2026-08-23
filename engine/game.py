"""
engine/game.py - Core game loop, state machine, physics accumulator, and rendering orchestrator for Bubble Arena.
"""
import pygame
import sys
import random
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, VIRTUAL_WIDTH, VIRTUAL_HEIGHT, FPS, TITLE,
    STATE_MENU, STATE_MODE_SELECT, STATE_LEVEL_SELECT, STATE_LOBBY,
    STATE_PLAYING, STATE_PAUSED, STATE_GAMEOVER, STATE_VICTORY, STATE_CONTROLS,
    MODE_FFA, MODE_TEAM, MODE_CTF, GAME_MODES, PLAYER_COLORS
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
from network.lan_server import LANServer
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

        # Systems
        self.sound_mgr = SoundManager()
        self.sprite_mgr = SpriteManager()
        self.particle_mgr = ParticleManager()
        self.input_handler = InputHandler()
        self.level_mgr = LevelManager()
        self.hud = HUD()
        self.menu = MenuSystem()

        # Network
        self.lan_server = None
        self.lan_client = None
        self.is_lan_host = False
        self.is_lan_client = False
        self.found_hosts = []
        self.net_status_msg = ""

        # Match setup
        self.state = STATE_MENU
        self.current_mode_name = MODE_FFA
        self.game_mode = FFAMode()
        self.is_bot_match = is_bot_match

        # Entities
        self.players = []
        self.bubbles = []
        self.trapped_bubbles = []
        self.powerups = []
        self.flag = None
        self.item_spawn_timer = 8.0

        self._init_players()

    def _init_players(self):
        """Creates 4 player instances (Team 0: Green/Yellow, Team 1: Blue/Pink)."""
        self.players.clear()
        for i in range(4):
            sp = self.level_mgr.spawn_points.get(i, (40 + i * 100, 50))
            # In local mode: Player 0 is Human, Players 1-3 are AI bots if is_bot_match, or local human keys
            # By default Player 0 is Human, other players can be controlled or AI
            is_bot = (i > 0) if self.is_bot_match else False
            team = 0 if i in (0, 2) else 1
            p = Player(player_id=i, spawn_x=sp[0], spawn_y=sp[1], team=team, is_bot=is_bot)
            self.players.append(p)

    def set_game_mode(self, mode_name):
        """Switches the active game mode rules."""
        self.current_mode_name = mode_name
        if mode_name == MODE_FFA:
            self.game_mode = FFAMode()
            for p in self.players:
                p.team = p.id
        elif mode_name == MODE_TEAM:
            self.game_mode = TeamMode()
            for p in self.players:
                p.team = 0 if p.id in (0, 2) else 1
        elif mode_name == MODE_CTF:
            self.game_mode = CTFMode()
            for p in self.players:
                p.team = 0 if p.id in (0, 2) else 1

    def start_match(self):
        """Starts a fresh match on the currently selected level and mode."""
        self.bubbles.clear()
        self.trapped_bubbles.clear()
        self.powerups.clear()
        self.item_spawn_timer = random.uniform(8.0, 14.0)

        # Reposition players to level spawn points
        for i, p in enumerate(self.players):
            sp = self.level_mgr.spawn_points.get(i, (40 + i * 100, 50))
            p.reset_for_round(sp[0], sp[1])

        # Flag setup for CTF
        if self.current_mode_name == MODE_CTF:
            fx, fy = self.level_mgr.flag_spawn
            self.flag = Flag(fx, fy)
        else:
            self.flag = None

        self.game_mode.start_round(self.players)
        self.sound_mgr.start_bgm(fast=False)
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
                    if idx == 0:  # Start Local Match
                        self.start_match()
                    elif idx == 1:  # Select Mode
                        self.menu.selected_idx = GAME_MODES.index(self.current_mode_name) if self.current_mode_name in GAME_MODES else 0
                        self.state = STATE_MODE_SELECT
                    elif idx == 2:  # Select Level
                        self.menu.selected_idx = self.level_mgr.current_level_idx
                        self.state = STATE_LEVEL_SELECT
                    elif idx == 3:  # LAN Multiplayer
                        self.menu.selected_idx = 0
                        self.state = STATE_LOBBY
                    elif idx == 4:  # Controls
                        self.state = STATE_CONTROLS
                    elif idx == 5:  # Quit
                        self.running = False

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
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.menu.selected_idx = (self.menu.selected_idx - 1) % self.level_mgr.get_level_count()
                        self.sound_mgr.play_sfx("select")
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.menu.selected_idx = (self.menu.selected_idx + 1) % self.level_mgr.get_level_count()
                        self.sound_mgr.play_sfx("select")
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.menu.selected_idx = max(0, self.menu.selected_idx - 5)
                        self.sound_mgr.play_sfx("select")
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.menu.selected_idx = min(self.level_mgr.get_level_count() - 1, self.menu.selected_idx + 5)
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
                action = self.menu.handle_navigation(event, 4)
                if action == "MOVE":
                    self.sound_mgr.play_sfx("select")
                elif action == "SELECT":
                    idx = self.menu.selected_idx
                    if idx == 0:  # Host Match
                        if not self.lan_server:
                            self.lan_server = LANServer()
                            self.lan_server.start()
                            self.is_lan_host = True
                            self.net_status_msg = f"Hosting on {self.lan_server.get_local_ip()}! Starting match..."
                            self.start_match()
                    elif idx == 1:  # Auto-Discover
                        self.net_status_msg = "Scanning LAN for hosts..."
                        self.found_hosts = LANClient.discover_hosts(timeout=1.5)
                        if self.found_hosts:
                            host_ip, host_port = self.found_hosts[0]
                            self.lan_client = LANClient()
                            if self.lan_client.connect(host_ip, host_port):
                                self.is_lan_client = True
                                self.net_status_msg = f"Connected to {host_ip}:{host_port}!"
                                self.start_match()
                            else:
                                self.net_status_msg = "Connection failed."
                        else:
                            self.net_status_msg = "No LAN hosts found."
                    elif idx == 2:  # Direct Connect 127.0.0.1
                        self.lan_client = LANClient()
                        if self.lan_client.connect("127.0.0.1"):
                            self.is_lan_client = True
                            self.net_status_msg = "Connected to local server!"
                            self.start_match()
                        else:
                            self.net_status_msg = "Could not connect to 127.0.0.1"
                    elif idx == 3:  # Return
                        self.state = STATE_MENU
                elif action == "BACK":
                    self.state = STATE_MENU

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

    def update(self, dt):
        """Updates game state, physics, collisions, and network sync."""
        if self.state != STATE_PLAYING:
            return

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
                # Check struggle inputs
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
                    bot_act = p.update_bot_ai(dt, self.players, self.bubbles, self.trapped_bubbles, self.flag)
                    p.handle_input(bot_act, dt, spawned_bubbles, self.sound_mgr, self.particle_mgr)
                else:
                    user_act = self.input_handler.poll_inputs(p.id)
                    p.handle_input(user_act, dt, spawned_bubbles, self.sound_mgr, self.particle_mgr)

                    # If client connected over LAN, transmit input
                    if self.is_lan_client and self.lan_client and p.id == self.lan_client.assigned_player_id:
                        self.lan_client.send_input(user_act)

            p.update(dt, platforms, self.bubbles, self.trapped_bubbles, self.sound_mgr, self.particle_mgr)

        self.bubbles.extend(spawned_bubbles)

        # 3. Update Bubbles & Opponent Trapping Check
        active_bubbles = []
        for b in self.bubbles:
            if not b.update(dt, platforms):
                # Bubble popped from 30s timeout or wall
                self.particle_mgr.spawn_pop_burst(b.x, b.y, count=8)
                self.sound_mgr.play_sfx("pop")
                continue

            # Check collision with other players to trap them
            trapped_someone = False
            for target_p in self.players:
                if target_p.id != b.owner_id and target_p.is_alive and not target_p.is_trapped and target_p.invulnerable_timer <= 0:
                    # In team mode, only trap enemies
                    is_enemy = (self.current_mode_name == MODE_FFA) or (target_p.team != b.owner_team)
                    if is_enemy and b.rect.colliderect(target_p.rect):
                        # TRAP THE PLAYER!
                        tb = TrappedBubble(target_p, b.owner_id, b.owner_team)
                        self.trapped_bubbles.append(tb)
                        self.particle_mgr.spawn_sparkles(target_p.x, target_p.y, count=10)
                        self.particle_mgr.add_floating_text("TRAPPED!", target_p.x, target_p.y - 12)
                        self.sound_mgr.play_sfx("trap")
                        trapped_someone = True
                        break

            if not trapped_someone:
                active_bubbles.append(b)

        self.bubbles = active_bubbles

        # 4. Update Trapped Bubbles & Popping / Rescue Check
        active_trapped = []
        for tb in self.trapped_bubbles:
            if not tb.update(dt, platforms):
                # Expired or struggle escaped
                self.particle_mgr.spawn_pop_burst(tb.x, tb.y, count=12)
                self.particle_mgr.add_floating_text("FREED!", tb.x, tb.y - 12)
                self.sound_mgr.play_sfx("pop")
                continue

            # Check if any active player touches this trapped bubble to pop it
            is_team_mode = (self.current_mode_name != MODE_FFA)
            popped = False

            for p in self.players:
                if p.is_alive and not p.is_trapped:
                    result = tb.check_pop_by_player(p, is_team_mode=is_team_mode)
                    if result:
                        res_type, points = result
                        popped = True
                        self.game_mode.on_player_popped(p, tb, res_type, points)

                        if res_type == "KILL":
                            self.particle_mgr.spawn_pop_burst(tb.x, tb.y, count=18)
                            self.particle_mgr.add_floating_text(f"+{points} POP!", tb.x, tb.y - 14)
                            self.sound_mgr.play_sfx("pop")
                            self.sound_mgr.play_sfx("death")

                            # 50% chance to drop powerup item on kill
                            if random.random() < 0.6:
                                self.powerups.append(PowerUp(tb.x, tb.y))

                        elif res_type == "RESCUE":
                            self.particle_mgr.spawn_sparkles(tb.x, tb.y, count=14)
                            self.particle_mgr.add_floating_text(f"RESCUE +{points}!", tb.x, tb.y - 14)
                            self.sound_mgr.play_sfx("rescue")
                        break

            if not popped:
                active_trapped.append(tb)

        self.trapped_bubbles = active_trapped

        # 5. Power-Up Spawning & Collection
        self.item_spawn_timer -= dt
        if self.item_spawn_timer <= 0.0:
            self.item_spawn_timer = random.uniform(10.0, 18.0)
            rx = random.uniform(50, VIRTUAL_WIDTH - 50)
            ry = 40
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
            self.state = STATE_VICTORY
            self.sound_mgr.stop_bgm()

        # 8. Particle System
        self.particle_mgr.update(dt)

    def render(self, dt):
        """Renders the game scene to virtual surface and scales up to window."""
        self.virtual_screen.fill((16, 16, 26))

        if self.state == STATE_MENU:
            self.menu.draw_title_screen(self.virtual_screen, self.sprite_mgr, self.current_mode_name, self.level_mgr.level_name, dt)

        elif self.state == STATE_MODE_SELECT:
            self.menu.draw_mode_select(self.virtual_screen, self.menu.selected_idx, dt)

        elif self.state == STATE_LEVEL_SELECT:
            self.menu.draw_level_select(self.virtual_screen, self.level_mgr, dt)

        elif self.state == STATE_CONTROLS:
            self.menu.draw_controls(self.virtual_screen)

        elif self.state == STATE_LOBBY:
            h_ip = self.lan_server.get_local_ip() if self.lan_server else "127.0.0.1"
            self.menu.draw_lan_lobby(
                self.virtual_screen, h_ip, self.found_hosts,
                self.is_lan_host, self.is_lan_client, self.net_status_msg
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
                self.current_mode_name, self.level_mgr.level_name, self.flag
            )

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
