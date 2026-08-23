"""
ui/hud.py - Arcade top HUD, 3-minute timer, player cards, scores, and 'Hurry Up!' alerts.
"""
import pygame
import math
from constants import (
    VIRTUAL_WIDTH, COLOR_WHITE, COLOR_GOLD, COLOR_YELLOW, COLOR_RED,
    COLOR_CYAN, COLOR_GREEN, COLOR_BLUE, COLOR_PINK, COLOR_BLACK,
    PLAYER_COLORS, HURRY_UP_TIME
)

class HUD:
    """Renders the top arcade status banner and match statistics."""
    def __init__(self):
        try:
            self.font_main = pygame.font.SysFont("courier,consolas,monospace", 10, bold=True)
            self.font_timer = pygame.font.SysFont("courier,consolas,monospace", 12, bold=True)
            self.font_banner = pygame.font.SysFont("courier,consolas,monospace", 14, bold=True)
        except Exception:
            self.font_main = pygame.font.Font(None, 14)
            self.font_timer = pygame.font.Font(None, 16)
            self.font_banner = pygame.font.Font(None, 20)

    def draw(self, surface, players, time_remaining, mode_name, level_name, flag=None):
        # 1. Top HUD Background Bar
        hud_bar = pygame.Surface((VIRTUAL_WIDTH, 18))
        hud_bar.fill(COLOR_BLACK)
        surface.blit(hud_bar, (0, 0))
        pygame.draw.line(surface, (60, 60, 80), (0, 18), (VIRTUAL_WIDTH, 18), 1)

        # 2. Player Scores (1UP, 2UP, 3UP, 4UP)
        slot_w = VIRTUAL_WIDTH // 5
        for i, p in enumerate(players):
            col_cfg = PLAYER_COLORS[i]
            col = col_cfg["main"]
            tag = f"{i+1}UP"
            score_text = f"{p.score:05d}"

            # Draw tag & score
            tag_surf = self.font_main.render(tag, True, col)
            val_surf = self.font_main.render(score_text, True, COLOR_WHITE)

            x_pos = 6 + (i if i < 2 else i + 1) * slot_w
            surface.blit(tag_surf, (x_pos, 2))
            surface.blit(val_surf, (x_pos + 22, 2))

            # Status marker (Trapped / Dead)
            if not p.is_alive:
                dead_lbl = self.font_main.render("RESPAWN", True, COLOR_RED)
                surface.blit(dead_lbl, (x_pos, 10))
            elif p.is_trapped:
                trap_lbl = self.font_main.render("TRAPPED!", True, COLOR_YELLOW)
                surface.blit(trap_lbl, (x_pos, 10))
            elif flag and flag.carrier == p:
                flag_lbl = self.font_main.render("FLAG!", True, COLOR_GOLD)
                surface.blit(flag_lbl, (x_pos, 10))

        # 3. Global 3-Minute Countdown Timer (Center of HUD)
        minutes = int(max(0, time_remaining)) // 60
        seconds = int(max(0, time_remaining)) % 60
        timer_str = f"TIME {minutes}:{seconds:02d}"

        # Color timer red/gold when under 30s
        timer_color = COLOR_RED if time_remaining <= HURRY_UP_TIME and (int(time_remaining * 4) % 2 == 0) else COLOR_GOLD
        timer_surf = self.font_timer.render(timer_str, True, timer_color)
        t_rect = timer_surf.get_rect(center=(VIRTUAL_WIDTH // 2, 9))
        surface.blit(timer_surf, t_rect)

        # 4. "HURRY UP!" Center Alert Banner
        if time_remaining <= HURRY_UP_TIME and time_remaining > (HURRY_UP_TIME - 3.5):
            if (int(time_remaining * 6) % 2) == 0:
                banner_surf = self.font_banner.render("!!! HURRY UP !!!", True, COLOR_RED)
                b_rect = banner_surf.get_rect(center=(VIRTUAL_WIDTH // 2, 45))
                # Shadow
                shadow_surf = self.font_banner.render("!!! HURRY UP !!!", True, COLOR_BLACK)
                surface.blit(shadow_surf, (b_rect.x + 1, b_rect.y + 1))
                surface.blit(banner_surf, b_rect)
