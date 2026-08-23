"""
ui/menu.py - Title screen, mode select, level select, LAN lobby, controls guide, and victory screen.
"""
import pygame
import math
from constants import (
    VIRTUAL_WIDTH, VIRTUAL_HEIGHT, COLOR_BLACK, COLOR_WHITE, COLOR_GOLD,
    COLOR_YELLOW, COLOR_GREEN, COLOR_BLUE, COLOR_CYAN, COLOR_RED, COLOR_PINK,
    COLOR_GRAY, GAME_MODES, MODE_FFA, MODE_TEAM, MODE_CTF
)

class MenuSystem:
    """Renders and handles navigation for all menu screens."""
    def __init__(self):
        try:
            self.font_title = pygame.font.SysFont("courier,consolas,monospace", 22, bold=True)
            self.font_menu = pygame.font.SysFont("courier,consolas,monospace", 12, bold=True)
            self.font_info = pygame.font.SysFont("courier,consolas,monospace", 10, bold=True)
        except Exception:
            self.font_title = pygame.font.Font(None, 28)
            self.font_menu = pygame.font.Font(None, 16)
            self.font_info = pygame.font.Font(None, 14)

        self.main_options = [
            "START LOCAL MATCH",
            "SELECT GAME MODE",
            "SELECT LEVEL",
            "LAN MULTIPLAYER",
            "HOW TO PLAY / CONTROLS",
            "QUIT"
        ]
        self.selected_idx = 0
        self.anim_timer = 0.0

    def handle_navigation(self, event, option_count):
        """Processes Up/Down/Enter/Escape navigation."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_idx = (self.selected_idx - 1) % option_count
                return "MOVE"
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_idx = (self.selected_idx + 1) % option_count
                return "MOVE"
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_f, pygame.K_k):
                return "SELECT"
            elif event.key == pygame.K_ESCAPE:
                return "BACK"
        return None

    def draw_title_screen(self, surface, sprite_manager, current_mode, current_level_name, dt):
        """Renders the retro arcade title screen with animated logo and dragons."""
        self.anim_timer += dt
        surface.fill(COLOR_BLACK)

        # Starry / bubble background dots
        for i in range(18):
            bx = (i * 27 + int(self.anim_timer * 15)) % VIRTUAL_WIDTH
            by = (i * 19 + int(math.sin(self.anim_timer + i) * 10)) % VIRTUAL_HEIGHT
            pygame.draw.circle(surface, (40, 50, 80), (bx, by), 2)

        # Glowing Title
        title_bob = int(math.sin(self.anim_timer * 3.0) * 3.0)
        title_text = "BUBBLE ARENA"
        sub_text = "4-PLAYER RETRO ARCADE BRAWLER"

        # Shadow & Glow
        t_shadow = self.font_title.render(title_text, True, COLOR_BLUE)
        t_surf = self.font_title.render(title_text, True, COLOR_GOLD)
        t_rect = t_surf.get_rect(center=(VIRTUAL_WIDTH // 2, 45 + title_bob))
        surface.blit(t_shadow, (t_rect.x + 2, t_rect.y + 2))
        surface.blit(t_surf, t_rect)

        s_surf = self.font_info.render(sub_text, True, COLOR_CYAN)
        s_rect = s_surf.get_rect(center=(VIRTUAL_WIDTH // 2, 68 + title_bob))
        surface.blit(s_surf, s_rect)

        # Current match settings banner
        cfg_str = f"MODE: {current_mode}  |  {current_level_name}"
        cfg_surf = self.font_info.render(cfg_str, True, COLOR_GREEN)
        surface.blit(cfg_surf, cfg_surf.get_rect(center=(VIRTUAL_WIDTH // 2, 90)))

        # Menu options list
        start_y = 120
        for i, opt in enumerate(self.main_options):
            is_sel = (i == self.selected_idx)
            color = COLOR_GOLD if is_sel else COLOR_WHITE
            prefix = ">> " if is_sel else "   "
            suffix = " <<" if is_sel else "   "
            text_surf = self.font_menu.render(f"{prefix}{opt}{suffix}", True, color)
            rect = text_surf.get_rect(center=(VIRTUAL_WIDTH // 2, start_y + i * 22))
            if is_sel:
                # Selection box highlight
                box_rect = rect.inflate(12, 4)
                pygame.draw.rect(surface, (40, 40, 70), box_rect, border_radius=4)
                pygame.draw.rect(surface, COLOR_GOLD, box_rect, 1, border_radius=4)
            surface.blit(text_surf, rect)

        # Bottom footer instructions
        footer = self.font_info.render("[UP/DOWN] Navigate   [ENTER/F] Select", True, COLOR_GRAY)
        surface.blit(footer, footer.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 16)))

    def draw_mode_select(self, surface, current_mode_idx, dt):
        """Mode selection screen."""
        self.anim_timer += dt
        surface.fill(COLOR_BLACK)

        title = self.font_title.render("SELECT GAME MODE", True, COLOR_GOLD)
        surface.blit(title, title.get_rect(center=(VIRTUAL_WIDTH // 2, 35)))

        descriptions = {
            MODE_FFA: "4-Player Solo Free-For-All! Trap & Pop every opponent. Highest score wins!",
            MODE_TEAM: "2v2 Team Brawler! Pop enemies to eliminate. Pop allies to RESCUE them!",
            MODE_CTF: "Capture The Flag! Grab the golden flag and hold it for continuous score!"
        }

        modes = [MODE_FFA, MODE_TEAM, MODE_CTF]
        start_y = 80
        for i, mode in enumerate(modes):
            is_sel = (i == self.selected_idx)
            col = COLOR_GOLD if is_sel else COLOR_WHITE
            box_rect = pygame.Rect(40, start_y + i * 55, VIRTUAL_WIDTH - 80, 44)

            pygame.draw.rect(surface, (30, 30, 50) if not is_sel else (50, 50, 90), box_rect, border_radius=4)
            pygame.draw.rect(surface, col, box_rect, 2 if is_sel else 1, border_radius=4)

            m_surf = self.font_menu.render(f"{i+1}. {mode}", True, col)
            surface.blit(m_surf, (box_rect.x + 12, box_rect.y + 8))

            desc_surf = self.font_info.render(descriptions.get(mode, ""), True, COLOR_GRAY if not is_sel else COLOR_CYAN)
            surface.blit(desc_surf, (box_rect.x + 12, box_rect.y + 26))

        footer = self.font_info.render("[ENTER] Confirm   [ESC] Return", True, COLOR_GRAY)
        surface.blit(footer, footer.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 16)))

    def draw_level_select(self, surface, level_manager, dt):
        """Level selection screen browsing all 10 levels."""
        self.anim_timer += dt
        surface.fill(COLOR_BLACK)

        title = self.font_title.render("SELECT ARENA LEVEL", True, COLOR_GOLD)
        surface.blit(title, title.get_rect(center=(VIRTUAL_WIDTH // 2, 30)))

        count = level_manager.get_level_count()
        start_y = 65
        for i in range(count):
            lvl = level_manager.levels[i]
            is_sel = (i == self.selected_idx)
            col = COLOR_GOLD if is_sel else COLOR_WHITE

            # 2 columns of 5 levels
            col_x = 30 if i < 5 else VIRTUAL_WIDTH // 2 + 10
            row_y = start_y + (i % 5) * 36
            card_rect = pygame.Rect(col_x, row_y, VIRTUAL_WIDTH // 2 - 40, 30)

            pygame.draw.rect(surface, (30, 35, 55) if not is_sel else (60, 60, 100), card_rect, border_radius=3)
            pygame.draw.rect(surface, col, card_rect, 2 if is_sel else 1, border_radius=3)

            lvl_surf = self.font_info.render(lvl["name"], True, col)
            surface.blit(lvl_surf, (card_rect.x + 8, card_rect.y + 9))

        footer = self.font_info.render("[UP/DOWN/LEFT/RIGHT] Choose Level   [ENTER] Select   [ESC] Return", True, COLOR_GRAY)
        surface.blit(footer, footer.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 16)))

    def draw_controls(self, surface):
        """Controls & Mechanics guide screen."""
        surface.fill(COLOR_BLACK)
        title = self.font_title.render("HOW TO PLAY & CONTROLS", True, COLOR_GOLD)
        surface.blit(title, title.get_rect(center=(VIRTUAL_WIDTH // 2, 25)))

        players_info = [
            ("P1 (Green)", "WASD = Move/Jump | F = Shoot / Struggle | G = Action"),
            ("P2 (Blue)",  "ARROWS = Move/Jump | K = Shoot / Struggle | L = Action"),
            ("P3 (Yellow)","IJKL = Move/Jump | U = Shoot / Struggle | O = Action"),
            ("P4 (Pink)",  "NUMPAD 4/5/6/8 = Move/Jump | NUM 7 = Shoot | NUM 9 = Action"),
            ("GAMEPADS",   "D-Pad / Left Stick = Move | A = Jump | X/B = Shoot"),
        ]

        start_y = 55
        for idx, (p_name, c_text) in enumerate(players_info):
            p_surf = self.font_info.render(f"{p_name}:", True, COLOR_CYAN)
            c_surf = self.font_info.render(c_text, True, COLOR_WHITE)
            surface.blit(p_surf, (30, start_y + idx * 20))
            surface.blit(c_surf, (115, start_y + idx * 20))

        mechanics = [
            "- BUBBLE SHOOT: Shoots horizontally to trap opponents in floating bubbles.",
            "- BUBBLE RIDING: Jump onto any floating bubble to bounce up to higher tiers!",
            "- POP & KILL: Head-butt or land spikes onto enemy bubbles to score points.",
            "- TEAM RESCUE: Touch trapped teammates to instantly free them with a shield!",
            "- 30s TIMER: Bubbles explode after 30s. Mash buttons to struggle free early!",
            "- POWER-UPS: Collect Shoes (Speed), Candies (Range/Rapid/Giant), and Shields!"
        ]

        m_y = 165
        for m in mechanics:
            m_surf = self.font_info.render(m, True, COLOR_GOLD if "RESCUE" in m or "RIDING" in m else COLOR_GRAY)
            surface.blit(m_surf, (30, m_y))
            m_y += 18

        footer = self.font_info.render("Press [ENTER] or [ESC] to Return to Menu", True, COLOR_CYAN)
        surface.blit(footer, footer.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 16)))

    def draw_lan_lobby(self, surface, host_ip, found_hosts, is_hosting, is_connected, status_msg=""):
        """LAN Multiplayer room screen."""
        surface.fill(COLOR_BLACK)
        title = self.font_title.render("LAN MULTIPLAYER", True, COLOR_GOLD)
        surface.blit(title, title.get_rect(center=(VIRTUAL_WIDTH // 2, 25)))

        opts = [
            f"1. HOST LAN MATCH (Your IP: {host_ip})",
            "2. AUTO-DISCOVER & JOIN LOCAL HOST",
            "3. DIRECT CONNECT TO LOCALHOST (127.0.0.1)",
            "4. RETURN TO MAIN MENU"
        ]

        start_y = 65
        for i, opt in enumerate(opts):
            is_sel = (i == self.selected_idx)
            col = COLOR_GOLD if is_sel else COLOR_WHITE
            prefix = ">> " if is_sel else "   "
            opt_surf = self.font_menu.render(f"{prefix}{opt}", True, col)
            surface.blit(opt_surf, (40, start_y + i * 26))

        # Status readout
        st_box = pygame.Rect(40, 185, VIRTUAL_WIDTH - 80, 80)
        pygame.draw.rect(surface, (25, 30, 45), st_box, border_radius=4)
        pygame.draw.rect(surface, COLOR_CYAN, st_box, 1, border_radius=4)

        st_title = self.font_info.render("NETWORK STATUS / LOBBY:", True, COLOR_CYAN)
        surface.blit(st_title, (50, 192))

        status_text = status_msg or ("Hosting match... Waiting for players." if is_hosting else "Ready to host or join.")
        msg_surf = self.font_info.render(status_text, True, COLOR_GREEN if is_connected or is_hosting else COLOR_WHITE)
        surface.blit(msg_surf, (50, 212))

        if found_hosts:
            h_str = f"Found LAN Host: {found_hosts[0][0]}:{found_hosts[0][1]}"
            h_surf = self.font_info.render(h_str, True, COLOR_YELLOW)
            surface.blit(h_surf, (50, 232))

        footer = self.font_info.render("[ENTER] Execute Action   [ESC] Return", True, COLOR_GRAY)
        surface.blit(footer, footer.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 16)))

    def draw_victory_screen(self, surface, winner_info, players, mode_name, dt):
        """End-of-match celebration and scoreboard."""
        self.anim_timer += dt
        # Darkened overlay
        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        overlay.fill((10, 10, 20))
        surface.blit(overlay, (0, 0))

        # Animated celebration banner
        bob = int(math.sin(self.anim_timer * 4.0) * 3)
        vic_title = self.font_title.render("MATCH FINISHED!", True, COLOR_GOLD)
        surface.blit(vic_title, vic_title.get_rect(center=(VIRTUAL_WIDTH // 2, 35 + bob)))

        # Winner text
        win_str = winner_info.get("text", "GAME OVER") if winner_info else "MATCH COMPLETED"
        win_surf = self.font_menu.render(win_str, True, COLOR_GREEN)
        surface.blit(win_surf, win_surf.get_rect(center=(VIRTUAL_WIDTH // 2, 65)))

        # Scoreboard Table
        table_rect = pygame.Rect(40, 90, VIRTUAL_WIDTH - 80, 150)
        pygame.draw.rect(surface, (20, 24, 40), table_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_GOLD, table_rect, 1, border_radius=4)

        header_str = "PLAYER         SCORE     KILLS    DEATHS   RESCUES"
        head_surf = self.font_info.render(header_str, True, COLOR_CYAN)
        surface.blit(head_surf, (55, 100))
        pygame.draw.line(surface, COLOR_CYAN, (55, 115), (VIRTUAL_WIDTH - 55, 115), 1)

        sorted_players = sorted(players, key=lambda p: p.score, reverse=True)
        for idx, p in enumerate(sorted_players):
            row_y = 125 + idx * 24
            col = COLOR_GOLD if idx == 0 else COLOR_WHITE
            p_line = f"{p.name:<14} {p.score:>7d}   {p.kills:>5d}    {p.deaths:>6d}   {p.rescues:>7d}"
            r_surf = self.font_info.render(p_line, True, col)
            surface.blit(r_surf, (55, row_y))

        footer = self.font_menu.render("Press [ENTER] for Rematch / [ESC] for Main Menu", True, COLOR_YELLOW)
        surface.blit(footer, footer.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 35)))
