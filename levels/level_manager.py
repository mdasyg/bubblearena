"""
levels/level_manager.py - Level parsing, platform builder, spawn point setup for Bubble Arena.
"""
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
                elif char == '1':
                    self.spawn_points[0] = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)
                elif char == '2':
                    self.spawn_points[1] = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)
                elif char == '3':
                    self.spawn_points[2] = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)
                elif char == '4':
                    self.spawn_points[3] = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)
                elif char == 'F':
                    self.flag_spawn = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)

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
