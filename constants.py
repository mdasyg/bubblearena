"""
constants.py - Global constants, physics settings, colors, and key mappings for Bubble Arena.
"""
import pygame

# --- Screen & Display ---
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
VIRTUAL_WIDTH = 480
VIRTUAL_HEIGHT = 320
FPS = 60
TITLE = "BUBBLE ARENA - 4P Retro Arcade Brawler"

# --- Physics Constants ---
GRAVITY = 720.0             # pixels/sec^2
MAX_FALL_SPEED = 400.0      # pixels/sec
PLAYER_SPEED = 140.0        # base horizontal speed (pixels/sec)
PLAYER_JUMP_SPEED = -280.0  # jump impulse (pixels/sec)
BUBBLE_BOUNCE_SPEED = -310.0# jump impulse when bouncing off a bubble
ACCELERATION = 1200.0       # ground acceleration
FRICTION = 900.0            # ground deceleration
AIR_ACCEL = 700.0           # air acceleration
AIR_FRICTION = 300.0        # air drag

# --- Bubble Mechanics ---
BUBBLE_INITIAL_SPEED = 280.0   # initial horizontal burst speed
BUBBLE_SHOT_DISTANCE = 110.0   # base horizontal travel before float
BUBBLE_FLOAT_SPEED = -35.0     # buoyant upward drift speed
BUBBLE_SWAY_AMPLITUDE = 18.0   # left-right sine wave sway amplitude
BUBBLE_SWAY_FREQUENCY = 2.0    # sway frequency (Hz)
BUBBLE_LIFESPAN = 30.0         # 30 seconds lifetime before pop / explosion
BUBBLE_FLASH_TIME = 24.0       # time when bubble starts warning flash
BUBBLE_RADIUS = 12             # standard bubble visual radius
GIANT_BUBBLE_RADIUS = 24       # 2x size giant candy bubble radius (twice the size)
GIANT_CANDY_DURATION = 30.0    # 30 seconds temporary giant bubble bonus
BUBBLE_FIRE_COOLDOWN = 0.35    # seconds between bubble shots
RAPID_FIRE_COOLDOWN = 0.16     # rapid candy fire cooldown

# --- Match & Mode Constants ---
GLOBAL_MATCH_TIME = 180.0      # 3 minutes in seconds
HURRY_UP_TIME = 30.0           # trigger "HURRY UP!" warning at 30s remaining
RESPAWN_DELAY = 3.5            # seconds before dead player respawns
INVULNERABLE_DURATION = 2.0    # seconds of flash shield upon respawn / rescue
STRUGGLE_ESCAPE_PRESSES = 16   # button presses needed to struggle out of bubble early

# --- Color Palette (16-color Retro Arcade Palette) ---
COLOR_BLACK = (16, 16, 26)
COLOR_DARK_BLUE = (24, 34, 64)
COLOR_NAVY = (38, 50, 92)
COLOR_PURPLE = (128, 52, 144)
COLOR_RED = (220, 52, 60)
COLOR_ORANGE = (244, 120, 36)
COLOR_YELLOW = (252, 212, 64)
COLOR_GREEN = (56, 196, 68)
COLOR_CYAN = (68, 204, 236)
COLOR_BLUE = (48, 120, 240)
COLOR_PINK = (248, 136, 184)
COLOR_WHITE = (248, 248, 252)
COLOR_GRAY = (140, 144, 160)
COLOR_DARK_GRAY = (70, 74, 90)
COLOR_LIME = (164, 236, 76)
COLOR_GOLD = (255, 188, 24)

# --- Player Configurations ---
PLAYER_COLORS = [
    {"name": "Green Bub", "main": (56, 196, 68), "accent": (164, 236, 76), "belly": (252, 212, 64), "team": 0},
    {"name": "Blue Bob",  "main": (48, 120, 240), "accent": (68, 204, 236), "belly": (248, 248, 252), "team": 1},
    {"name": "Yellow Yan","main": (252, 190, 32), "accent": (252, 228, 100), "belly": (244, 120, 36), "team": 0},
    {"name": "Pink Pop",  "main": (248, 96, 160), "accent": (248, 176, 212), "belly": (248, 248, 252), "team": 1},
]

# --- Key Bindings for 4 Local Players on 1 Keyboard ---
LOCAL_KEY_MAPPINGS = {
    0: {  # Player 1: WASD + F (Shoot) + G (Jump / Bounce / Action) + E (Struggle)
        "left": pygame.K_a,
        "right": pygame.K_d,
        "up": pygame.K_w,
        "down": pygame.K_s,
        "jump": pygame.K_w,
        "shoot": pygame.K_f,
        "action": pygame.K_g,
        "struggle": pygame.K_f,
    },
    1: {  # Player 2: Arrow Keys + K (Shoot) + L (Jump) + J (Action)
        "left": pygame.K_LEFT,
        "right": pygame.K_RIGHT,
        "up": pygame.K_UP,
        "down": pygame.K_DOWN,
        "jump": pygame.K_UP,
        "shoot": pygame.K_k,
        "action": pygame.K_l,
        "struggle": pygame.K_k,
    },
    2: {  # Player 3: IJKL + U (Shoot) + O (Jump) + Y (Action)
        "left": pygame.K_j,
        "right": pygame.K_l,
        "up": pygame.K_i,
        "down": pygame.K_k,
        "jump": pygame.K_i,
        "shoot": pygame.K_u,
        "action": pygame.K_o,
        "struggle": pygame.K_u,
    },
    3: {  # Player 4: Numpad 4/5/6/8 + Numpad 7 (Shoot) + Numpad 9 (Jump)
        "left": pygame.K_KP4,
        "right": pygame.K_KP6,
        "up": pygame.K_KP8,
        "down": pygame.K_KP5,
        "jump": pygame.K_KP8,
        "shoot": pygame.K_KP7,
        "action": pygame.K_KP9,
        "struggle": pygame.K_KP7,
    },
}

# --- Game Modes ---
MODE_FFA = "Free For All"
MODE_TEAM = "2v2 Team Brawler"
MODE_CTF = "Capture The Flag"
MODE_SURVIVAL = "Arcade Survival"

GAME_MODES = [MODE_FFA, MODE_TEAM, MODE_CTF, MODE_SURVIVAL]

# --- Game States ---
STATE_MENU = 0
STATE_MODE_SELECT = 1
STATE_LEVEL_SELECT = 2
STATE_LOBBY = 3
STATE_PLAYING = 4
STATE_PAUSED = 5
STATE_GAMEOVER = 6
STATE_VICTORY = 7
STATE_CONTROLS = 8

# --- Network Configuration ---
DEFAULT_PORT = 28888
BROADCAST_PORT = 28889
DISCOVERY_MAGIC = "BUBBLE_ARENA_DISCOVER"
DISCOVERY_RESPONSE = "BUBBLE_ARENA_HOST"

# --- PowerUp Types ---
POWERUP_SHOES = "shoes"              # Fast movement speed (12s)
POWERUP_BLUE_CANDY = "candy_blue"    # Long distance bubble shot (15s)
POWERUP_YELLOW_CANDY = "candy_yellow"# Rapid fire bubbles (15s)
POWERUP_PURPLE_CANDY = "candy_purple"# Giant 2x bubble candy (30s)
POWERUP_SHIELD = "shield"            # Temporary invulnerability (6s)

# Bonus Score Collectibles
POWERUP_DIAMOND = "diamond"          # Sparkling Diamond (+2500 pts)
POWERUP_RUBY = "ruby"                # Precious Ruby Gem (+1500 pts)
POWERUP_APPLE = "apple"              # Crisp Red Apple (+500 pts)
POWERUP_CARROT = "carrot"            # Fresh Crunchy Carrot (+400 pts)
POWERUP_WATERMELON = "watermelon"    # Juicy Watermelon Slice (+800 pts)
POWERUP_GRAPES = "grapes"            # Sweet Purple Grapes (+600 pts)
POWERUP_GOLDEN_BELL = "golden_bell"  # Rare Golden Bell (+2000 pts)
POWERUP_BANANA = "banana"            # Tropical Banana (+700 pts)
POWERUP_FRUIT = "fruit"              # Classic Bonus (+800 pts)

# --- Tile Dimension ---
TILE_SIZE = 16
GRID_COLS = VIRTUAL_WIDTH // TILE_SIZE  # 30 cols
GRID_ROWS = VIRTUAL_HEIGHT // TILE_SIZE # 20 rows
