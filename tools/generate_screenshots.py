"""
tools/generate_screenshots.py - Captures crisp 960x640 gameplay and UI screenshots for Bubble Arena documentation.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import random
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, VIRTUAL_WIDTH, VIRTUAL_HEIGHT,
    STATE_MENU, STATE_LEVEL_SELECT, STATE_PLAYING, STATE_VICTORY,
    STATE_LAN_ROOM, STATE_SETTINGS, SPEED_OPTIONS,
    MODE_FFA, MODE_CTF, MODE_TEAM,
    POWERUP_DIAMOND, POWERUP_GOLDEN_BELL, POWERUP_SHOES, POWERUP_WATERMELON,
    POWERUP_PURPLE_CANDY, COLOR_GOLD, COLOR_RED, COLOR_GREEN
)
from engine.game import GameEngine
from entities.bubble import Bubble
from entities.trapped_bubble import TrappedBubble
from entities.powerup import PowerUp
from entities.flag import Flag

def create_screenshots():
    out_dir = os.path.join("docs", "images")
    os.makedirs(out_dir, exist_ok=True)

    engine = GameEngine(is_bot_match=True)

    def save_frame(filename):
        scaled = pygame.transform.scale(engine.virtual_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        path = os.path.join(out_dir, filename)
        pygame.image.save(scaled, path)
        print(f"Saved: {path} ({scaled.get_width()}x{scaled.get_height()})")

    # 1. Title Screen
    engine.state = STATE_MENU
    engine.menu.anim_timer = 2.0
    engine.render(0.016)
    save_frame("title_screen.png")

    # 2. 14-Level Select Grid
    engine.state = STATE_LEVEL_SELECT
    engine.level_mgr.load_level(0)
    engine.render(0.016)
    save_frame("level_select_grid.png")

    # 3. Free-For-All Gameplay Action (Emerald Meadow)
    engine.set_game_mode(MODE_FFA)
    engine.level_mgr.load_level(0)  # Stage 1: Emerald Meadow
    engine.state = STATE_PLAYING
    engine.current_round = 2
    engine.total_rounds = 4
    engine.round_transition_timer = 0.0
    engine.game_mode.match_time_remaining = 68.4
    engine.game_mode.is_hurry_up = False

    for p in engine.players:
        p.is_alive = True
        p.invulnerable_timer = 0.0
        p.respawn_timer = 0.0

    p0 = engine.players[0]  # Green Bub
    p1 = engine.players[1]  # Blue Bob
    p2 = engine.players[2]  # Yellow Yan
    p3 = engine.players[3]  # Pink Pop

    # Green Bub shooting right
    p0.x, p0.y = 110.0, 216.0
    p0.facing = 1
    p0.anim_state = "shoot"
    p0.score = 5400
    p0.kills = 3
    p0.is_grounded = True
    p0._update_rect()

    # Blue Bob trapped in bubble
    p1.x, p1.y = 240.0, 140.0
    p1.is_trapped = True
    p1.score = 3800
    p1.kills = 2
    p1._update_rect()

    tb = TrappedBubble(trapped_player=p1, captor_id=0, captor_team=0)
    tb.x, tb.y = 240.0, 140.0
    tb._update_rect()
    engine.trapped_bubbles = [tb]

    # Yellow Yan jumping
    p2.x, p2.y = 350.0, 160.0
    p2.facing = -1
    p2.anim_state = "jump"
    p2.score = 4200
    p2.kills = 2
    p2.vy = -120.0
    p2._update_rect()

    # Pink Pop running
    p3.x, p3.y = 290.0, 260.0
    p3.facing = -1
    p3.anim_state = "walk"
    p3.score = 2900
    p3.kills = 1
    p3.is_grounded = True
    p3._update_rect()

    # Bubbles
    b1 = Bubble(160, 216, direction=1, owner_id=0, owner_team=0)
    b2 = Bubble(185, 216, direction=1, owner_id=0, owner_team=0)
    b3 = Bubble(210, 180, direction=1, owner_id=2, owner_team=1)
    b3.is_floating = True
    b4 = Bubble(310, 120, direction=-1, owner_id=0, owner_team=0)
    b4.is_floating = True
    b5 = Bubble(140, 110, direction=1, owner_id=3, owner_team=1)
    b5.is_floating = True
    bg = Bubble(260, 85, direction=1, owner_id=0, owner_team=0, is_giant=True)
    bg.is_floating = True
    engine.bubbles = [b1, b2, b3, b4, b5, bg]

    # Powerups
    pu1 = PowerUp(70, 264, item_type=POWERUP_DIAMOND)
    pu2 = PowerUp(390, 216, item_type=POWERUP_GOLDEN_BELL)
    pu3 = PowerUp(180, 104, item_type=POWERUP_PURPLE_CANDY)
    pu4 = PowerUp(320, 264, item_type=POWERUP_WATERMELON)
    engine.powerups = [pu1, pu2, pu3, pu4]

    # Floating Text & Particles
    engine.particle_mgr.add_floating_text("+1000 POP!", 240, 122, color=COLOR_RED)
    engine.particle_mgr.add_floating_text("+2500 DIAMOND!", 70, 248, color=COLOR_GOLD)
    engine.particle_mgr.spawn_pop_burst(240, 140, count=16)
    engine.particle_mgr.spawn_sparkles(70, 264, COLOR_GOLD, count=10)

    engine.render(0.016)
    save_frame("gameplay_ffa_battle.png")

    # 4. Capture The Flag Clash (Grand Champion Arena)
    engine.set_game_mode(MODE_CTF)
    engine.level_mgr.load_level(9)  # Stage 10: Grand Champion Arena
    engine.state = STATE_PLAYING
    engine.current_round = 3
    engine.total_rounds = 4
    engine.round_transition_timer = 0.0
    engine.game_mode.match_time_remaining = 44.2
    engine.game_mode.is_hurry_up = False

    engine.bubbles.clear()
    engine.trapped_bubbles.clear()
    engine.powerups.clear()
    engine.particle_mgr.particles.clear()
    engine.particle_mgr.floating_texts.clear()

    for p in engine.players:
        p.is_alive = True
        p.is_trapped = False
        p.invulnerable_timer = 0.0
        p.respawn_timer = 0.0

    # P0 (Green) escorting carrier
    p0.x, p0.y = 200.0, 140.0
    p0.facing = 1
    p0.anim_state = "shoot"
    p0.score = 6800
    p0.is_grounded = True
    p0._update_rect()

    # P2 (Yellow) holding golden flag
    p2.x, p2.y = 270.0, 140.0
    p2.facing = -1
    p2.anim_state = "walk"
    p2.score = 9200
    p2.is_grounded = True
    p2._update_rect()

    engine.flag = Flag(p2.x, p2.y)
    engine.flag.pickup(p2)
    engine.flag.update(0.016)

    # P1 (Blue) chasing carrier
    p1.x, p1.y = 350.0, 140.0
    p1.facing = -1
    p1.anim_state = "walk"
    p1.score = 7100
    p1.is_grounded = True
    p1._update_rect()

    # P3 (Pink) leaping down to intercept
    p3.x, p3.y = 240.0, 80.0
    p3.facing = 1
    p3.anim_state = "jump"
    p3.score = 5600
    p3.vy = 80.0
    p3._update_rect()

    # Bubbles
    b_ctf1 = Bubble(310, 140, direction=-1, owner_id=1, owner_team=1)
    b_ctf2 = Bubble(230, 140, direction=1, owner_id=0, owner_team=0)
    b_ctf3 = Bubble(380, 80, direction=-1, owner_id=3, owner_team=1)
    b_ctf3.is_floating = True
    engine.bubbles = [b_ctf1, b_ctf2, b_ctf3]

    engine.powerups = [PowerUp(240, 260, item_type=POWERUP_SHOES)]
    engine.particle_mgr.add_floating_text("FLAG CARRIER!", p2.x, p2.y - 20, color=COLOR_GOLD)
    engine.particle_mgr.spawn_sparkles(p2.x, p2.y, COLOR_GOLD, count=8)

    engine.render(0.016)
    save_frame("gameplay_ctf_match.png")

    # 5. LAN Room Lobby with Chat & Ready Slots
    engine.state = STATE_LAN_ROOM
    engine.is_lan_host = True
    engine.room_slots = {
        0: {"name": "Green Bub (Host)", "type": "human", "ready": True},
        1: {"name": "Blue Bob", "type": "human", "ready": True},
        2: {"name": "Yellow Yan [Standard]", "type": "bot", "ready": True},
        3: {"name": "Pink Pop", "type": "human", "ready": True},
    }
    engine.room_chat_history = [
        {"player_id": 0, "sender": "Host", "message": "Welcome to Bubble Arena!"},
        {"player_id": 1, "sender": "Blue Bob", "message": "Ready for 2v2 Team Brawler!"},
        {"player_id": 3, "sender": "Pink Pop", "message": "Let's pop some bubbles!"},
        {"player_id": 0, "sender": "Host", "message": "All ready! Launching match..."}
    ]
    engine.lan_chat_input = "Good luck everyone!"
    engine.is_chat_active = True
    engine.render(0.016)
    save_frame("lan_lobby.png")

    # 6. Tournament Victory Scoreboard
    engine.state = STATE_VICTORY
    engine.game_mode.winner_info = {
        "text": "Green Bub WINS CHAMPIONSHIP!",
        "player_id": 0,
        "score": 18400,
        "kills": 9,
        "team": None
    }
    p0.score = 18400
    p0.kills = 9
    p0.deaths = 2
    p0.rescues = 4

    p1.score = 14200
    p1.kills = 6
    p1.deaths = 5
    p1.rescues = 3

    p2.score = 11800
    p2.kills = 4
    p2.deaths = 6
    p2.rescues = 2

    p3.score = 9500
    p3.kills = 3
    p3.deaths = 7
    p3.rescues = 1

    engine.render(0.016)
    save_frame("victory_scoreboard.png")

    # 7. Game Settings Screen
    engine.state = STATE_SETTINGS
    engine.speed_idx = 1
    engine.total_rounds = 4
    engine.render(0.016)
    save_frame("game_settings.png")

    print("\nAll 7 gameplay and UI screenshots generated successfully!")

if __name__ == "__main__":
    create_screenshots()
