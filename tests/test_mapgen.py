"""Procedural generation tests (DESIGN.md sections 9 and 9.1)."""

import random
import unittest

from emberlight import config, mapgen
from emberlight.entities import Loot, Monster


def _floor(seed, ring):
    return mapgen.generate_floor(random.Random(seed), ring)


class DeterminismTest(unittest.TestCase):
    def test_same_seed_same_floor(self):
        a = _floor(12345, 0)
        b = _floor(12345, 0)
        self.assertEqual(["".join(r) for r in a.grid],
                         ["".join(r) for r in b.grid])
        self.assertEqual(a.entrance, b.entrance)
        self.assertEqual((a.beacon.x, a.beacon.y), (b.beacon.x, b.beacon.y))
        self.assertEqual([(l.x, l.y, l.kind) for l in a.loot],
                         [(l.x, l.y, l.kind) for l in b.loot])

    def test_different_seed_different_floor(self):
        a = _floor(1, 2)
        b = _floor(2, 2)
        self.assertNotEqual(["".join(r) for r in a.grid],
                            ["".join(r) for r in b.grid])


class ConnectivityTest(unittest.TestCase):
    def test_all_rings_fully_connected(self):
        for seed in range(8):
            for ring in range(config.RING_COUNT):
                f = _floor(seed, ring)
                dist = mapgen._bfs(f, f.entrance)
                reachable = set(dist)
                all_floor = set(f.floor_cells()) | {f.entrance}
                self.assertEqual(all_floor - reachable, set(),
                                 f"unreachable floor cells seed={seed} ring={ring}")

    def test_beacon_reachable_via_neighbor(self):
        for seed in range(8):
            for ring in range(config.RING_COUNT):
                f = _floor(seed, ring)
                dist = mapgen._bfs(f, f.entrance)
                neighbors = mapgen._neighbors((f.beacon.x, f.beacon.y))
                reachable_neighbors = [n for n in neighbors if n in dist]
                self.assertTrue(reachable_neighbors,
                                f"beacon has no reachable neighbor seed={seed} ring={ring}")


class PlacementTest(unittest.TestCase):
    def test_entrance_is_on_border(self):
        for seed in range(5):
            f = _floor(seed, 0)
            x, y = f.entrance
            self.assertTrue(x in (0, f.side - 1) or y in (0, f.side - 1))
            self.assertEqual(f.cell(x, y), config.ENTRANCE)

    def test_beacon_is_marked_and_root_on_ring7(self):
        for ring in range(config.RING_COUNT):
            f = _floor(1, ring)
            self.assertEqual(f.cell(f.beacon.x, f.beacon.y), f.beacon.glyph)
            self.assertEqual(f.beacon.is_root, ring == config.RING_COUNT - 1)

    def test_descent_adjacent_to_beacon(self):
        for ring in range(config.RING_COUNT - 1):
            f = _floor(1, ring)
            self.assertIsNotNone(f.descent)
            dx, dy = f.descent
            self.assertEqual(abs(dx - f.beacon.x) + abs(dy - f.beacon.y), 1)
            # hidden until lit
            self.assertEqual(f.cell(dx, dy), config.FLOOR)

    def test_ring7_has_no_descent(self):
        f = _floor(1, config.RING_COUNT - 1)
        self.assertIsNone(f.descent)


class BudgetTest(unittest.TestCase):
    def test_entity_budgets_per_ring(self):
        for ring in range(config.RING_COUNT):
            f = _floor(3, ring)
            budget = config.ENTITY_BUDGET[ring]
            self.assertEqual(len(f.monsters), budget[0])
            kinds = {}
            for item in f.loot:
                kinds[item.kind] = kinds.get(item.kind, 0) + 1
            self.assertEqual(kinds.get(config.OIL_CASK, 0), budget[1])
            self.assertEqual(kinds.get(config.LUMEN_SHARD, 0), budget[2])
            self.assertEqual(kinds.get(config.FLARE, 0), budget[3])
            # map fragment is a 50% chance, so 0 or 1
            self.assertIn(kinds.get(config.MAP_FRAGMENT, 0), (0, 1))

    def test_entities_not_adjacent_to_entrance_or_beacon(self):
        for ring in range(config.RING_COUNT):
            f = _floor(5, ring)
            blocked = set()
            for anchor in (f.entrance, (f.beacon.x, f.beacon.y)):
                blocked.add(anchor)
                blocked.update(mapgen._neighbors(anchor))
            for mon in f.monsters:
                self.assertNotIn((mon.x, mon.y), blocked)
            for item in f.loot:
                self.assertNotIn((item.x, item.y), blocked)


if __name__ == "__main__":
    unittest.main()
