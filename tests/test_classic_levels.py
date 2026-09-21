"""
tests/test_classic_levels.py - Verification suite for all 28 arena levels.
Validates arcade geometry, spawn safety, anti-trapping reachability,
dynamic respawn headroom guarantees, and level selection pagination.
"""
import unittest
from collections import deque
from constants import VIRTUAL_WIDTH, VIRTUAL_HEIGHT
from levels.level_data import ALL_LEVELS
from levels.level_manager import LevelManager
from network.server_core import BaseBubbleServer


class TestClassicLevels(unittest.TestCase):
    def setUp(self):
        self.level_mgr = LevelManager()

    def test_total_level_count(self):
        """LevelManager loads all 28 levels."""
        self.assertEqual(len(ALL_LEVELS), 28)
        self.assertEqual(self.level_mgr.get_level_count(), 28)

    def test_level_dimensions_and_tokens(self):
        """Every level map has exactly 20 rows of 30 columns with valid tokens."""
        valid_chars = set("#=.1234F")
        for idx, lvl in enumerate(ALL_LEVELS):
            m = lvl["map"]
            self.assertEqual(len(m), 20, f"Level {idx+1} must have 20 rows")
            for r_idx, row in enumerate(m):
                self.assertEqual(len(row), 30, f"Level {idx+1} row {r_idx} must have 30 cols")
                for c_idx, ch in enumerate(row):
                    self.assertIn(ch, valid_chars, f"Level {idx+1} ({r_idx},{c_idx}) invalid char '{ch}'")

    def test_spawn_integrity_and_headroom(self):
        """Every level map has spawns 1, 2, 3, 4, F with vertical headroom and support."""
        for idx, lvl in enumerate(ALL_LEVELS):
            m = lvl["map"]
            spawns = {}
            for r in range(20):
                for c in range(30):
                    ch = m[r][c]
                    if ch in "1234F":
                        self.assertNotIn(ch, spawns, f"Level {idx+1} has duplicate spawn '{ch}'")
                        spawns[ch] = (r, c)

            for ch in "1234F":
                self.assertIn(ch, spawns, f"Level {idx+1} is missing spawn '{ch}'")
                r, c = spawns[ch]
                # Headroom check: players 1-4 must have empty air '.'; flag 'F' must never have an internal solid block
                if ch in "1234":
                    self.assertEqual(m[r-1][c], ".", f"Level {idx+1} player spawn '{ch}' at ({r},{c}) lacks headroom: '{m[r-1][c]}'")
                elif r > 1:
                    self.assertNotEqual(m[r-1][c], "#", f"Level {idx+1} flag spawn 'F' at ({r},{c}) has solid overhead block")
                # Support: players 1-4 must have platform support within 2 tiles below
                if ch in "1234":
                    has_support = any(m[check_r][c] in "=#" for check_r in range(r+1, min(20, r+3)))
                    self.assertTrue(has_support, f"Level {idx+1} player spawn '{ch}' at ({r},{c}) lacks platform support below")

    def test_anti_trapping_reachability(self):
        """All players and flag are mutually reachable via flood-fill without enclosed cages."""
        for idx, lvl in enumerate(ALL_LEVELS):
            m = lvl["map"]
            spawns = {}
            for r in range(20):
                for c in range(30):
                    if m[r][c] in "1234F":
                        spawns[m[r][c]] = (r, c)

            start = spawns["1"]
            visited = set([start])
            q = deque([start])
            while q:
                cr, cc = q.popleft()
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < 20 and 0 <= nc < 30 and m[nr][nc] != "#":
                        if (nr, nc) not in visited:
                            visited.add((nr, nc))
                            q.append((nr, nc))

            for ch in "234F":
                target = spawns[ch]
                self.assertIn(
                    target, visited,
                    f"Level {idx+1} ({lvl['name']}): spawn '{ch}' is trapped and unreachable from spawn '1'!"
                )

    def test_walkable_platforms_headroom_guarantee(self):
        """LevelManager._get_walkable_platforms() returns platforms with clear headroom."""
        for idx in range(28):
            self.level_mgr.load_level(idx)
            walkable = self.level_mgr._get_walkable_platforms()
            self.assertGreater(len(walkable), 0, f"Level {idx+1} has no walkable platforms!")

            # Verify no solid platform is directly overhead
            for plat in walkable:
                for check_y in (8, 16, 24):
                    has_solid = any(
                        not other.is_oneway and other.rect.collidepoint(plat.rect.centerx, plat.rect.top - check_y)
                        for other in self.level_mgr.platforms
                    )
                    self.assertFalse(has_solid, f"Level {idx+1} platform at {plat.rect} has solid overhead block at -{check_y}px!")

    def test_distinct_platform_spawns(self):
        """LevelManager.get_distinct_platform_spawns() returns 4 valid coordinates."""
        for idx in range(28):
            self.level_mgr.load_level(idx)
            spawns = self.level_mgr.get_distinct_platform_spawns(count=4)
            self.assertEqual(len(spawns), 4)
            for x, y in spawns:
                self.assertGreaterEqual(x, 16)
                self.assertLessEqual(x, VIRTUAL_WIDTH - 16)
                self.assertGreaterEqual(y, 20)
                self.assertLessEqual(y, VIRTUAL_HEIGHT - 20)

    def test_dedicated_server_level_limits(self):
        """BaseBubbleServer accepts level indices 1..28 and rejects others."""
        server = BaseBubbleServer(
            host="127.0.0.1",
            port=29110,
            is_dedicated=True,
            enable_beacon=False,
            auto_start=False
        )
        try:
            # Valid levels 1 to 28
            for lvl in (1, 14, 15, 28):
                ok, msg = server.set_level(lvl)
                self.assertTrue(ok)
                self.assertEqual(server.level_idx, lvl)

            # Invalid levels
            ok, msg = server.set_level(0)
            self.assertFalse(ok)
            ok, msg = server.set_level(29)
            self.assertFalse(ok)
            ok, msg = server.set_level("abc")
            self.assertFalse(ok)
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
