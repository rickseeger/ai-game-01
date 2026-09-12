"""Raycaster tests (DESIGN.md section 3)."""

import unittest

from emberlight import config, engine, entities


class _FakeFloor:
    """A minimal floor with a hollow border-walled room for raycast tests."""

    def __init__(self, grid):
        self.grid = grid
        self.side = len(grid)
        self.loot = []
        self.monsters = []

        class _Beacon:
            def __init__(self, x, y):
                self.x, self.y, self.lit, self.is_root = x, y, False, False

            @property
            def glyph(self):
                return "B"

        self.beacon = _Beacon(0, 0)
        self.entrance = (0, 0)
        self.descent = None

    def is_wall(self, x, y):
        return not (0 <= x < self.side and 0 <= y < self.side) or \
            self.grid[y][x] == config.WALL

    def is_opaque(self, x, y):
        return self.is_wall(x, y)

    def walkable(self, x, y):
        return 0 <= x < self.side and 0 <= y < self.side and \
            self.grid[y][x] != config.WALL

    def cell(self, x, y):
        return self.grid[y][x]

    def loot_at(self, x, y):
        return None

    def monster_at(self, x, y):
        return None


def _room(side):
    grid = [[config.WALL] * side for _ in range(side)]
    for y in range(1, side - 1):
        for x in range(1, side - 1):
            grid[y][x] = config.FLOOR
    return _FakeFloor(grid)


def _cell_set(view):
    return {(x, y) for y in range(view.height) for x in range(view.width)
            if view.buffer[y][x] != " "}


class DDATest(unittest.TestCase):
    def test_dda_distance_to_wall(self):
        floor = _room(21)
        # Player centre (5.5, 5.5) facing east: wall at x=20 is 14.5 away.
        t = engine._dda(floor, 5.5, 5.5, 1.0, 0.0, 100.0)
        self.assertAlmostEqual(t, 14.5, places=6)

    def test_dda_stops_at_light_radius(self):
        floor = _room(21)
        self.assertIsNone(engine._dda(floor, 5.5, 5.5, 1.0, 0.0, 3.0))


class LightConeTest(unittest.TestCase):
    def test_wall_within_cone_is_drawn(self):
        floor = _room(21)
        p = entities.Player(5, 5, facing=1)
        view = engine.render_view(floor, p, 40, 20, 20, ascii_fallback=True)
        # The wall is 14.5 tiles away, within the cone: the DDA must record a
        # finite z-depth for the centre column (it fades to space via the
        # shade ramp, which is correct -- far walls disappear into the dark).
        self.assertLess(view.zbuffer[view.width // 2], float("inf"))

    def test_near_wall_renders_shade_at_horizon(self):
        floor = _room(9)   # wall at x=8, ~2.5 tiles from x=5.5
        p = entities.Player(5, 5, facing=1)
        view = engine.render_view(floor, p, 40, 20, 20, ascii_fallback=False)
        self.assertEqual(view.buffer[view.height // 2][view.width // 2],
                         "\u2593")

    def test_wall_beyond_cone_is_blank(self):
        floor = _room(21)
        p = entities.Player(5, 5, facing=1)
        view = engine.render_view(floor, p, 40, 20, 3, ascii_fallback=True)
        self.assertEqual(_cell_set(view), set(),
                         "no wall should render beyond the light radius")


class SpriteTest(unittest.TestCase):
    def test_sprite_within_cone_drawn(self):
        floor = _room(21)
        from emberlight.entities import Loot
        floor.loot.append(Loot(9, 5, config.LUMEN_SHARD))  # east, 4 tiles
        p = entities.Player(5, 5, facing=1)
        view = engine.render_view(floor, p, 40, 20, 6, ascii_fallback=False)
        self.assertIn(config.LUMEN_SHARD, "".join(view.lines()))

    def test_sprite_beyond_cone_not_drawn(self):
        floor = _room(21)
        from emberlight.entities import Loot
        floor.loot.append(Loot(15, 5, config.LUMEN_SHARD))  # 10 tiles east
        p = entities.Player(5, 5, facing=1)
        view = engine.render_view(floor, p, 40, 20, 6, ascii_fallback=False)
        self.assertNotIn(config.LUMEN_SHARD, "".join(view.lines()))

    def test_sprite_occluded_by_wall(self):
        # A wall column directly ahead occludes a sprite behind it.
        grid = [[config.WALL] * 21 for _ in range(21)]
        for y in range(1, 20):
            for x in range(1, 20):
                grid[y][x] = config.FLOOR
        for y in range(5, 16):       # wall at x=10 (distance ~4.5)
            grid[y][10] = config.WALL
        floor = _FakeFloor(grid)
        from emberlight.entities import Loot
        floor.loot.append(Loot(15, 10, config.LUMEN_SHARD))  # behind the wall
        p = entities.Player(5, 10, facing=1)
        view = engine.render_view(floor, p, 40, 20, 10, ascii_fallback=False)
        self.assertNotIn(config.LUMEN_SHARD, "".join(view.lines()))


class ShadeTest(unittest.TestCase):
    def test_shade_ramp_boundaries(self):
        self.assertEqual(engine._shade_for(1.0, False), "\u2588")
        self.assertEqual(engine._shade_for(2.0, False), "\u2593")
        self.assertEqual(engine._shade_for(4.0, False), "\u2592")
        self.assertEqual(engine._shade_for(6.0, False), "\u2591")
        self.assertEqual(engine._shade_for(9.0, False), " ")


if __name__ == "__main__":
    unittest.main()
