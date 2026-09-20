"""
ui/menu.py - Title screen, mode select, level select, LAN lobby, controls guide, and victory screen.
"""
import pygame
import math
from constants import (
    VIRTUAL_WIDTH, VIRTUAL_HEIGHT, COLOR_BLACK, COLOR_WHITE, COLOR_GOLD,
    COLOR_YELLOW, COLOR_GREEN, COLOR_BLUE, COLOR_CYAN, COLOR_RED, COLOR_PINK,
    COLOR_GRAY, COLOR_DARK_GRAY, GAME_MODES, MODE_FFA, MODE_TEAM, MODE_CTF
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
            "GAME SETTINGS",
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
        """Level selection screen browsing all 14 levels in a balanced 2-column grid."""
        self.anim_timer += dt
        surface.fill(COLOR_BLACK)

        title = self.font_title.render("SELECT ARENA LEVEL", True, COLOR_GOLD)
        surface.blit(title, title.get_rect(center=(VIRTUAL_WIDTH // 2, 22)))

        count = level_manager.get_level_count()
        rows_per_col = (count + 1) // 2
        start_y = 44
        card_w = VIRTUAL_WIDTH // 2 - 32
        card_h = 27

        for i in range(count):
            lvl = level_manager.levels[i]
            is_sel = (i == self.selected_idx)
            col = COLOR_GOLD if is_sel else COLOR_WHITE

            col_idx = 0 if i < rows_per_col else 1
            row_idx = i if col_idx == 0 else (i - rows_per_col)
            col_x = 24 if col_idx == 0 else VIRTUAL_WIDTH // 2 + 8
            row_y = start_y + row_idx * 33
            card_rect = pygame.Rect(col_x, row_y, card_w, card_h)

            pygame.draw.rect(surface, (30, 35, 55) if not is_sel else (60, 60, 100), card_rect, border_radius=3)
            pygame.draw.rect(surface, col, card_rect, 2 if is_sel else 1, border_radius=3)

            lvl_surf = self.font_info.render(lvl["name"], True, col)
            surface.blit(lvl_surf, (card_rect.x + 8, card_rect.y + 7))

        footer = self.font_info.render("[UP/DOWN/LEFT/RIGHT] Choose Level   [ENTER] Select   [ESC] Return", True, COLOR_GRAY)
        surface.blit(footer, footer.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 14)))

    def draw_settings_screen(self, surface, speed_name, rounds_count, dt,
                             music_vol_name="Normal (100%)", sfx_vol_name="Normal (100%)",
                             min_duration_name="45s (Default)", round_timer_name="90s (Normal)",
                             bot_pref_name="Mixed (Random)"):
        """Settings screen configuring audio, speed, round duration, match timer, and bot profiles."""
        self.anim_timer += dt
        surface.fill(COLOR_BLACK)

        # Title & Subtitle
        title = self.font_title.render("GAME SETTINGS", True, COLOR_GOLD)
        surface.blit(title, title.get_rect(center=(VIRTUAL_WIDTH // 2, 16)))

        sub = self.font_info.render("AUDIO, PACING, DURATION & MATCH CUSTOMIZATION", True, COLOR_CYAN)
        surface.blit(sub, sub.get_rect(center=(VIRTUAL_WIDTH // 2, 32)))

        options = [
            ("GAME SPEED", f"< {speed_name} >", "Adjust physics, movement, and projectile pacing"),
            ("MATCH ROUNDS", f"< {rounds_count} Rounds >", "Total rounds played before calculating tournament champion"),
            ("MUSIC VOLUME", f"< {music_vol_name} >", "Turn off music or select low (35%) or normal volume"),
            ("SFX VOLUME", f"< {sfx_vol_name} >", "Adjust sound effects volume for bubble shoots, pops, and jumps"),
            ("MIN STAGE TIME", f"< {min_duration_name} >", "Guaranteed minimum stage time before an early score win"),
            ("ROUND TIME LIMIT", f"< {round_timer_name} >", "Countdown match duration timer for each arena round"),
            ("BOT PERSONALITIES", f"< {bot_pref_name} >", "Configure CPU bot behavior archetypes or keep randomized"),
            ("CONFIRM & RETURN", "", "Save settings and return to the main menu")
        ]

        start_y = 46
        pitch = 25
        card_w = VIRTUAL_WIDTH - 56
        card_h = 22

        for i, (opt_name, opt_val, opt_desc) in enumerate(options):
            is_sel = (i == self.selected_idx)
            card_y = start_y + i * pitch
            card_rect = pygame.Rect(28, card_y, card_w, card_h)

            bg_col = (45, 50, 85) if is_sel else (22, 25, 38)
            border_col = COLOR_GOLD if is_sel else (55, 60, 85)
            pygame.draw.rect(surface, bg_col, card_rect, border_radius=3)
            pygame.draw.rect(surface, border_col, card_rect, 2 if is_sel else 1, border_radius=3)

            # Left Label
            lbl_left = f"{i+1}. {opt_name}"
            col_left = COLOR_GOLD if is_sel else COLOR_WHITE
            surf_left = self.font_info.render(lbl_left, True, col_left)
            surface.blit(surf_left, (card_rect.x + 10, card_rect.y + 4))

            # Right Value (if any)
            if opt_val:
                col_right = COLOR_YELLOW if is_sel else COLOR_CYAN
                surf_right = self.font_info.render(opt_val, True, col_right)
                r_rect = surf_right.get_rect(right=card_rect.right - 10, centery=card_rect.centery)
                surface.blit(surf_right, r_rect)

        # Contextual Description Banner
        cur_desc = options[self.selected_idx][2] if 0 <= self.selected_idx < len(options) else ""
        desc_rect = pygame.Rect(28, 252, card_w, 30)
        pygame.draw.rect(surface, (16, 20, 36), desc_rect, border_radius=4)
        pygame.draw.rect(surface, (60, 75, 110), desc_rect, 1, border_radius=4)

        desc_surf = self.font_info.render(f">> {cur_desc} <<", True, COLOR_GOLD)
        surface.blit(desc_surf, desc_surf.get_rect(center=desc_rect.center))

        # Footer
        footer = self.font_info.render("[UP/DOWN] Select   [LEFT/RIGHT] Change Value   [ENTER/ESC] Return", True, COLOR_GRAY)
        surface.blit(footer, footer.get_rect(center=(VIRTUAL_WIDTH // 2, 304)))

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

    def draw_lan_lobby(self, surface, host_ip, interfaces, iface_idx, found_hosts, is_hosting, is_connected, status_msg="", target_remote_ip="127.0.0.1"):
        """LAN Multiplayer room setup & interface selection screen."""
        surface.fill(COLOR_BLACK)
        title = self.font_title.render("LAN & INTERNET MULTIPLAYER", True, COLOR_GOLD)
        surface.blit(title, title.get_rect(center=(VIRTUAL_WIDTH // 2, 25)))

        current_iface = interfaces[iface_idx] if interfaces and iface_idx < len(interfaces) else host_ip

        opts = [
            f"1. NETWORK INTERFACE: < {current_iface} >",
            f"2. HOST LAN MATCH (Creates 4-Player Lobby)",
            "3. AUTO-DISCOVER & JOIN LOCAL HOST",
            f"4. DIRECT CONNECT TO IP/HOST: < {target_remote_ip} >",
            "5. RETURN TO MAIN MENU"
        ]

        start_y = 60
        for i, opt in enumerate(opts):
            is_sel = (i == self.selected_idx)
            col = COLOR_GOLD if is_sel else COLOR_WHITE
            prefix = ">> " if is_sel else "   "
            if (i == 0 or i == 3) and is_sel:
                opt_str = f"{prefix}{opt} [<- / ->]"
            else:
                opt_str = f"{prefix}{opt}"
            opt_surf = self.font_menu.render(opt_str, True, col)
            surface.blit(opt_surf, (30, start_y + i * 24))

        # Status readout
        st_box = pygame.Rect(30, 185, VIRTUAL_WIDTH - 60, 80)
        pygame.draw.rect(surface, (25, 30, 45), st_box, border_radius=4)
        pygame.draw.rect(surface, COLOR_CYAN, st_box, 1, border_radius=4)

        st_title = self.font_info.render("NETWORK ADAPTER & STATUS:", True, COLOR_CYAN)
        surface.blit(st_title, (40, 192))

        status_text = status_msg or f"Selected Binding: {current_iface} (Detected {len(interfaces)} local interfaces)"
        msg_surf = self.font_info.render(status_text, True, COLOR_GREEN if is_connected or is_hosting else COLOR_WHITE)
        surface.blit(msg_surf, (40, 212))

        if found_hosts:
            h_str = f"Found LAN Host: {found_hosts[0][0]}:{found_hosts[0][1]}"
            h_surf = self.font_info.render(h_str, True, COLOR_YELLOW)
            surface.blit(h_surf, (40, 232))

        footer = self.font_info.render("[UP/DOWN] Select Option   [LEFT/RIGHT] Change IP   [ENTER] Select   [ESC] Return", True, COLOR_GRAY)
        surface.blit(footer, footer.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 14)))

    def draw_player_count_select(self, surface, dt):
        """Player count selection screen: choose how many human players (1 to 4). Remaining are CPU bots."""
        self.anim_timer += dt
        surface.fill(COLOR_BLACK)

        title = self.font_title.render("HOW MANY HUMAN PLAYERS?", True, COLOR_GOLD)
        surface.blit(title, title.get_rect(center=(VIRTUAL_WIDTH // 2, 28)))

        sub = self.font_info.render("Select human count - remaining slots up to 4 will be CPU bots", True, COLOR_CYAN)
        surface.blit(sub, sub.get_rect(center=(VIRTUAL_WIDTH // 2, 46)))

        options = [
            ("1 HUMAN PLAYER",  "P1: Human (WASD / Arrows)   + 3 Random CPU Bots"),
            ("2 HUMAN PLAYERS", "P1: WASD / Space / F        P2: Arrows / Enter   + 2 CPU Bots"),
            ("3 HUMAN PLAYERS", "P1: WASD    P2: Arrows    P3: IJKL / O   + 1 CPU Bot"),
            ("4 HUMAN PLAYERS", "P1: WASD    P2: Arrows    P3: IJKL       P4: Numpad (All Humans)"),
        ]

        start_y = 66
        for i, (opt_title, opt_desc) in enumerate(options):
            is_sel = (i == self.selected_idx)
            col = COLOR_GOLD if is_sel else COLOR_WHITE
            box_rect = pygame.Rect(35, start_y + i * 52, VIRTUAL_WIDTH - 70, 42)

            bg_col = (50, 50, 90) if is_sel else (25, 28, 45)
            pygame.draw.rect(surface, bg_col, box_rect, border_radius=4)
            pygame.draw.rect(surface, col, box_rect, 2 if is_sel else 1, border_radius=4)

            t_surf = self.font_menu.render(f"{i+1}. {opt_title}", True, col)
            surface.blit(t_surf, (box_rect.x + 12, box_rect.y + 6))

            d_surf = self.font_info.render(opt_desc, True, COLOR_GRAY if not is_sel else COLOR_YELLOW)
            surface.blit(d_surf, (box_rect.x + 12, box_rect.y + 24))

        footer = self.font_info.render("[UP/DOWN] Select   [ENTER/SPACE] Start Match   [ESC] Return", True, COLOR_GRAY)
        surface.blit(footer, footer.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 14)))

    def draw_lan_room_lobby(self, surface, slots, chat_history, chat_input, is_chat_active, is_host, my_player_id, status_msg="", dt=0.016, game_mode="ffa"):
        """Dedicated 4-player LAN Room Lobby with Ready check, Game Mode sync, & Broadcast Chat."""
        self.anim_timer += dt
        surface.fill(COLOR_BLACK)

        # Title & Room Info
        title = self.font_title.render("LAN ROOM LOBBY", True, COLOR_GOLD)
        surface.blit(title, title.get_rect(center=(VIRTUAL_WIDTH // 2, 16)))

        # Subtitle & Game Mode
        mode_hint = " (Host [M] to Cycle)" if is_host else ""
        mode_label = f"MODE: [{game_mode.upper()}]{mode_hint}"
        mode_surf = self.font_info.render(mode_label, True, COLOR_YELLOW)
        surface.blit(mode_surf, (20, 32))

        role_str = "ROOM HOST (P1)" if is_host else f"CLIENT (P{my_player_id + 1})"
        sub = self.font_info.render(f"Role: {role_str}", True, COLOR_CYAN)
        surface.blit(sub, (VIRTUAL_WIDTH - 20 - sub.get_width(), 32))

        # Left Column: 4 Player Slots (Cards)
        player_colors = [COLOR_GREEN, COLOR_BLUE, COLOR_YELLOW, COLOR_PINK]
        card_w = 215
        card_h = 34
        start_y = 48

        all_ready = True
        filled_count = 0

        for slot_idx in range(4):
            slot = slots.get(slot_idx, {"name": f"Player {slot_idx + 1}", "type": "open", "ready": False})
            slot_y = start_y + slot_idx * 38
            card_rect = pygame.Rect(20, slot_y, card_w, card_h)

            # Card background
            p_col = player_colors[slot_idx]
            is_me = (slot_idx == my_player_id)
            bg_col = (30, 35, 55) if not is_me else (45, 50, 75)
            pygame.draw.rect(surface, bg_col, card_rect, border_radius=4)
            pygame.draw.rect(surface, p_col if is_me else (70, 75, 95), card_rect, 2 if is_me else 1, border_radius=4)

            # Slot label & Name
            slot_type = slot.get("type", "open")
            if slot_type == "open":
                all_ready = False
                name_text = f"P{slot_idx + 1}: [OPEN SLOT]"
                status_text = "WAITING FOR PLAYER..."
                st_color = COLOR_GRAY
            elif slot_type == "bot":
                filled_count += 1
                pers = slot.get("personality", "Standard")
                name_text = f"P{slot_idx + 1}: {slot.get('name', 'Bot')}"
                status_text = f"[READY (CPU-{pers.upper()})]"
                st_color = COLOR_GREEN
            else:  # human
                filled_count += 1
                name_text = f"P{slot_idx + 1}: {slot.get('name', 'Player')}" + (" (YOU)" if is_me else "")
                is_rdy = slot.get("ready", False)
                if is_rdy:
                    status_text = "[READY!]"
                    st_color = COLOR_GREEN
                else:
                    all_ready = False
                    status_text = "[NOT READY]"
                    st_color = COLOR_RED

            name_surf = self.font_info.render(name_text, True, p_col)
            surface.blit(name_surf, (28, slot_y + 6))

            st_surf = self.font_info.render(status_text, True, st_color)
            surface.blit(st_surf, (28, slot_y + 19))

        # Banner under slots
        banner_rect = pygame.Rect(20, 202, card_w, 44)
        if filled_count == 4 and all_ready:
            pulse = int(math.sin(self.anim_timer * 6.0) * 40 + 200)
            pygame.draw.rect(surface, (20, 80, 40), banner_rect, border_radius=4)
            pygame.draw.rect(surface, (50, pulse, 50), banner_rect, 2, border_radius=4)
            start_banner = self.font_menu.render("ALL 4 PLAYERS READY!", True, COLOR_YELLOW)
            surface.blit(start_banner, start_banner.get_rect(center=(banner_rect.centerx, banner_rect.centery - 7)))
            auto_lbl = self.font_info.render("Starting match automatically...", True, COLOR_WHITE)
            surface.blit(auto_lbl, auto_lbl.get_rect(center=(banner_rect.centerx, banner_rect.centery + 9)))
        else:
            pygame.draw.rect(surface, (20, 25, 40), banner_rect, border_radius=4)
            pygame.draw.rect(surface, COLOR_DARK_GRAY, banner_rect, 1, border_radius=4)
            need_str = f"Slots: {filled_count}/4 Filled & Ready"
            need_surf = self.font_info.render(need_str, True, COLOR_GOLD)
            surface.blit(need_surf, (28, 210))
            act_str = "Press [R] / [SPACE] to Toggle Ready"
            act_surf = self.font_info.render(act_str, True, COLOR_WHITE)
            surface.blit(act_surf, (28, 226))

        # Right Column: Broadcast Chat Box
        chat_x = 245
        chat_w = VIRTUAL_WIDTH - chat_x - 20
        chat_h = 198
        chat_rect = pygame.Rect(chat_x, start_y, chat_w, chat_h)
        pygame.draw.rect(surface, (15, 18, 30), chat_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_CYAN if is_chat_active else (60, 65, 85), chat_rect, 2 if is_chat_active else 1, border_radius=4)

        # Chat Title
        chat_title = self.font_info.render("BROADCAST CHAT (ALL PLAYERS)", True, COLOR_CYAN)
        surface.blit(chat_title, (chat_x + 8, start_y + 6))
        pygame.draw.line(surface, (40, 45, 65), (chat_x + 5, start_y + 20), (chat_x + chat_w - 5, start_y + 20), 1)

        # Messages area (last 7 messages)
        recent_chats = chat_history[-7:]
        msg_y = start_y + 24
        for ch in recent_chats:
            p_id = ch.get("player_id", 0)
            col = player_colors[p_id % 4]
            sender = ch.get("sender", "Player")
            msg = ch.get("message", "")
            prefix_surf = self.font_info.render(f"{sender}: ", True, col)
            surface.blit(prefix_surf, (chat_x + 8, msg_y))
            prefix_w = prefix_surf.get_width()
            text_surf = self.font_info.render(msg[:26], True, COLOR_WHITE)
            surface.blit(text_surf, (chat_x + 8 + prefix_w, msg_y))
            msg_y += 18

        # Chat Input Field (bottom of chat box)
        input_rect = pygame.Rect(chat_x + 6, start_y + chat_h - 26, chat_w - 12, 20)
        pygame.draw.rect(surface, (25, 30, 50) if is_chat_active else (20, 22, 35), input_rect, border_radius=3)
        pygame.draw.rect(surface, COLOR_GOLD if is_chat_active else COLOR_GRAY, input_rect, 1, border_radius=3)

        cursor = "_" if (is_chat_active and int(self.anim_timer * 3) % 2 == 0) else ""
        placeholder = "Press [TAB] or [C] to chat..." if not is_chat_active and not chat_input else f"{chat_input}{cursor}"
        in_col = COLOR_WHITE if (is_chat_active or chat_input) else COLOR_GRAY
        input_surf = self.font_info.render(f"> {placeholder}", True, in_col)
        surface.blit(input_surf, (input_rect.x + 5, input_rect.y + 4))

        # Bottom Controls Footer
        host_controls = "   [B] Fill Bots   [M] Cycle Mode" if is_host else ""
        chat_hint = "[ESC] Unfocus Chat" if is_chat_active else "[TAB/C] Focus Chat"
        footer_str = f"[R/SPACE] Toggle Ready   {chat_hint}{host_controls}   [ESC] Exit"
        footer = self.font_info.render(footer_str, True, COLOR_GRAY)
        surface.blit(footer, footer.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 12)))

    def draw_victory_screen(self, surface, winner_info, players, mode_name, dt):
        """End-of-match celebration and scoreboard with perfectly justified columns."""
        self.anim_timer += dt
        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        overlay.fill((10, 10, 20))
        surface.blit(overlay, (0, 0))

        # Animated celebration banner
        bob = int(math.sin(self.anim_timer * 4.0) * 3)
        vic_title = self.font_title.render("MATCH FINISHED!", True, COLOR_GOLD)
        surface.blit(vic_title, vic_title.get_rect(center=(VIRTUAL_WIDTH // 2, 32 + bob)))

        win_str = winner_info.get("text", "GAME OVER") if winner_info else "MATCH COMPLETED"
        win_surf = self.font_menu.render(win_str, True, COLOR_GREEN)
        surface.blit(win_surf, win_surf.get_rect(center=(VIRTUAL_WIDTH // 2, 60)))

        # Scoreboard Table Card
        table_rect = pygame.Rect(35, 82, VIRTUAL_WIDTH - 70, 155)
        pygame.draw.rect(surface, (20, 24, 40), table_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_GOLD, table_rect, 1, border_radius=4)

        # Fixed Column Anchors
        col_player_x = 48
        col_score_x = 215
        col_kills_x = 280
        col_deaths_x = 345
        col_rescues_x = 410

        # Header Row
        head_y = 92
        h_player = self.font_info.render("PLAYER", True, COLOR_CYAN)
        h_score = self.font_info.render("SCORE", True, COLOR_CYAN)
        h_kills = self.font_info.render("KILLS", True, COLOR_CYAN)
        h_deaths = self.font_info.render("DEATHS", True, COLOR_CYAN)
        h_rescues = self.font_info.render("RESCUES", True, COLOR_CYAN)

        surface.blit(h_player, (col_player_x, head_y))
        surface.blit(h_score, h_score.get_rect(center=(col_score_x, head_y + 5)))
        surface.blit(h_kills, h_kills.get_rect(center=(col_kills_x, head_y + 5)))
        surface.blit(h_deaths, h_deaths.get_rect(center=(col_deaths_x, head_y + 5)))
        surface.blit(h_rescues, h_rescues.get_rect(center=(col_rescues_x, head_y + 5)))

        pygame.draw.line(surface, COLOR_CYAN, (45, 108), (VIRTUAL_WIDTH - 45, 108), 1)

        # Data Rows
        sorted_players = sorted(players, key=lambda p: p.score, reverse=True)
        for idx, p in enumerate(sorted_players):
            row_y = 118 + idx * 26
            col = COLOR_GOLD if idx == 0 else COLOR_WHITE

            # Player name truncated if long to preserve table boundaries
            name_surf = self.font_info.render(p.name[:18], True, col)
            surface.blit(name_surf, (col_player_x, row_y))

            # Numerical metrics centered on their respective column axes
            score_surf = self.font_info.render(f"{p.score}", True, col)
            surface.blit(score_surf, score_surf.get_rect(center=(col_score_x, row_y + 5)))

            kills_surf = self.font_info.render(f"{p.kills}", True, col)
            surface.blit(kills_surf, kills_surf.get_rect(center=(col_kills_x, row_y + 5)))

            deaths_surf = self.font_info.render(f"{p.deaths}", True, col)
            surface.blit(deaths_surf, deaths_surf.get_rect(center=(col_deaths_x, row_y + 5)))

            rescues_surf = self.font_info.render(f"{p.rescues}", True, col)
            surface.blit(rescues_surf, rescues_surf.get_rect(center=(col_rescues_x, row_y + 5)))

        footer = self.font_menu.render("Press [ENTER] for Rematch / [ESC] for Main Menu", True, COLOR_YELLOW)
        surface.blit(footer, footer.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 32)))

