"""
levels/level_manager.py - Level parsing, platform builder, spawn point setup for Bubble Arena.
"""
import random
import math
from constants import TILE_SIZE, VIRTUAL_WIDTH, VIRTUAL_HEIGHT
from entities.platform import Platform
from levels.level_data import ALL_LEVELS

class LevelManager:
    """Manages level loading, platform geometry generation, and spawn points."""
    def __init__(self):
        self.levels = ALL_LEVELS
        self.current_level_idx = 0
        self.platforms = []
        self.spawn_points = {0: (40, 40), 1: (440, 40), 2: (40, 260), 3: (440, 260)}
        self.flag_spawn = (VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2)
        self.current_theme = 0
        self.level_name = ""

        self.load_level(0)

    def get_level_count(self):
        return len(self.levels)

    def load_level(self, level_idx):
        """Parses the level map layout and instantiates platforms and coordinates."""
        self.current_level_idx = max(0, min(level_idx, len(self.levels) - 1))
        lvl_data = self.levels[self.current_level_idx]
        self.level_name = lvl_data["name"]
        self.current_theme = lvl_data.get("theme_id", 0)

        self.platforms.clear()
        map_grid = lvl_data["map"]

        # First pass: build platforms
        for row_idx, row in enumerate(map_grid):
            for col_idx, char in enumerate(row):
                x = col_idx * TILE_SIZE
                y = row_idx * TILE_SIZE

                if char == '#':
                    # Solid boundary/block
                    self.platforms.append(Platform(x, y, TILE_SIZE, TILE_SIZE, is_oneway=False, theme_id=self.current_theme))
                elif char == '=':
                    # One-way platform
                    self.platforms.append(Platform(x, y, TILE_SIZE, TILE_SIZE, is_oneway=True, theme_id=self.current_theme))

        # Second pass: calculate safe platform-surface spawn points for players and flag
        for row_idx, row in enumerate(map_grid):
            for col_idx, char in enumerate(row):
                x = col_idx * TILE_SIZE
                y = row_idx * TILE_SIZE

                if char in ('1', '2', '3', '4'):
                    p_id = int(char) - 1
                    spawn_x = x + TILE_SIZE // 2
                    # Find the nearest platform below this spawn tile
                    found_plat_y = None
                    for check_row in range(row_idx, len(map_grid)):
                        if map_grid[check_row][col_idx] in ('=', '#'):
                            found_plat_y = check_row * TILE_SIZE - 8
                            break
                    spawn_y = found_plat_y if found_plat_y is not None else (y + TILE_SIZE // 2)
                    self.spawn_points[p_id] = (spawn_x, spawn_y)
                elif char == 'F':
                    self.flag_spawn = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)

    def get_random_platform_spawn(self, avoid_positions=None, min_dist=40.0):
        """Returns a safe (x, y) standing location directly on top of a level platform, optionally avoiding specific locations."""
        walkable = [
            p for p in self.platforms 
            if (p.is_oneway or p.rect.top >= 32) 
            and p.rect.top <= VIRTUAL_HEIGHT - 32
            and p.rect.left >= 16 and p.rect.right <= VIRTUAL_WIDTH - 16
        ]
        if not walkable:
            return (VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2)

        if avoid_positions:
            shuffled = list(walkable)
            random.shuffle(shuffled)
            for plat in shuffled:
                pos = (float(plat.rect.centerx), float(plat.rect.top - 8))
                if all(math.hypot(pos[0] - ax, pos[1] - ay) >= min_dist for ax, ay in avoid_positions):
                    return pos

        plat = random.choice(walkable)
        return (plat.rect.centerx, plat.rect.top - 8)

    def get_distinct_platform_spawns(self, count=4):
        """Returns `count` distinct, well-spaced (x, y) standing locations on platforms for character spawns."""
        walkable = [
            p for p in self.platforms 
            if (p.is_oneway or p.rect.top >= 32) 
            and p.rect.top <= VIRTUAL_HEIGHT - 32
            and p.rect.left >= 16 and p.rect.right <= VIRTUAL_WIDTH - 16
        ]
        if not walkable:
            return [self.spawn_points.get(i, (40 + i * 100, 50)) for i in range(count)]

        candidates = list(walkable)
        random.shuffle(candidates)

        spawns = []
        for plat in candidates:
            pos = (float(plat.rect.centerx), float(plat.rect.top - 8))
            if all(math.hypot(pos[0] - sx, pos[1] - sy) >= 45.0 for sx, sy in spawns):
                spawns.append(pos)
                if len(spawns) >= count:
                    break

        # If not enough well-spaced platforms found, relax spacing or sample random platforms
        while len(spawns) < count:
            plat = random.choice(walkable)
            offset_x = random.choice([-16, 0, 16])
            pos_x = max(24.0, min(float(VIRTUAL_WIDTH - 24), float(plat.rect.centerx + offset_x)))
            spawns.append((pos_x, float(plat.rect.top - 8)))

        return spawns[:count]

    def next_level(self):
        """Advances to the next level."""
        new_idx = (self.current_level_idx + 1) % len(self.levels)
        self.load_level(new_idx)
        return new_idx

    def prev_level(self):
        """Goes to the previous level."""
        new_idx = (self.current_level_idx - 1) % len(self.levels)
        self.load_level(new_idx)
        return new_idx

    def load_random_level(self, exclude_current=True):
        """Picks and loads a random arena level."""
        count = len(self.levels)
        if count <= 1:
            self.load_level(0)
            return 0
        choices = [i for i in range(count) if (not exclude_current or i != self.current_level_idx)]
        picked_idx = random.choice(choices)
        self.load_level(picked_idx)
        return picked_idx
