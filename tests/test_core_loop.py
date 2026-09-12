"""End-to-end core-loop test: a scripted descent, relight, ascent and bank.

Drives the headless ``Game`` exactly like the curses loop does (``press`` +
``tick``) and navigates the maze with BFS pathing.  This proves the loop is
playable end-to-end without a terminal: find the beacon, relight it, descend,
ascend, and bank.  Monster avoidance, the flare repel, and the attack AI are
covered separately in ``test_game.py``, so monsters are cleared here to keep
the BFS pathing deterministic.
"""

import os
import tempfile
import unittest
from collections import deque

from emberlight import config
from emberlight.game import Game


def _bfs_path(floor, start, target, avoid):
    if start == target:
        return [start]
    prev = {start: None}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in config.FACINGS:
            n = (x + dx, y + dy)
            if n in prev:
                continue
            if n == target or (floor.walkable(*n) and n not in avoid):
                prev[n] = (x, y)
                if n == target:
                    path = [n]
                    while prev[n] is not None:
                        n = prev[n]
                        path.append(n)
                    return path[::-1]
                q.append(n)
    return None


def _navigate_to(game, tx, ty, avoid=frozenset()):
    for _ in range(20000):
        if (game.player.x, game.player.y) == (tx, ty):
            return True
        path = _bfs_path(game.floor, (game.player.x, game.player.y), (tx, ty), avoid)
        if not path or len(path) < 2:
            return False
        nx, ny = path[1]
        desired = config.FACINGS.index((nx - game.player.x, ny - game.player.y))
        diff = (desired - game.player.facing) % 4
        if diff == 1:
            game.press("d")
        elif diff == 2:
            game.press("d")
            game.press("d")
        elif diff == 3:
            game.press("a")
        game.press("w")
    return False


def _monster_cells(game):
    return {(m.x, m.y) for m in game.floor.monsters}


def _light_beacon(game):
    """Navigate adjacent to the beacon and relight it."""
    b = game.floor.beacon
    target = None
    for dx, dy in config.FACINGS:
        nx, ny = b.x + dx, b.y + dy
        if game.floor.walkable(nx, ny):
            target = (nx, ny)
            break
    assert target, "beacon has no walkable neighbour"
    assert _navigate_to(game, *target)
    game.press(" ")
    for _ in range(20):
        game.tick(0.15)
        if game.floor.beacon.lit:
            break
    assert game.floor.beacon.lit, "beacon did not relight"
    return target


class CoreLoopTest(unittest.TestCase):
    def test_descend_relight_ascend_and_bank(self):
        g = Game(20260912, daily=True,
                 records_path=os.path.join(tempfile.mkdtemp(), "records.json"))
        g.floor.monsters = []                  # see docstring

        # Ring 1: light the beacon.
        _light_beacon(g)
        self.assertGreaterEqual(g.player.score, config.SCORE_BEACON * 1)

        # Descend to ring 2 via the revealed stairs.
        dx, dy = g.floor.descent
        assert _navigate_to(g, dx, dy)
        g.press(" ")
        self.assertEqual(g.current_ring, 1)
        self.assertFalse(g.floor.beacon.lit)  # ring 2 beacon starts unlit
        g.floor.monsters = []                  # see docstring

        # Ring 2: light the beacon.
        _light_beacon(g)
        self.assertGreaterEqual(g.player.score,
                                 config.SCORE_BEACON * 1 + config.SCORE_BEACON * 2)

        # Ascend back to ring 1 through its entrance.
        ex, ey = g.floor.entrance
        assert _navigate_to(g, ex, ey)
        g.press(" ")
        self.assertEqual(g.current_ring, 0)
        self.assertEqual(g.phase, "ascend")
        self.assertFalse(g.floor.beacon.lit)  # the dark returned

        # Surface at ring 1's entrance.
        ex, ey = g.floor.entrance
        assert _navigate_to(g, ex, ey)
        g.press(" ")
        self.assertTrue(g.over)
        self.assertEqual(g.outcome, "banked")
        self.assertGreater(g.final_score, 0)
        self.assertEqual(g.records_snapshot["runs"], 1)
        self.assertEqual(g.records_snapshot["total_banked"], g.final_score)

    def test_fuel_death_ends_run_and_records(self):
        g = Game(7, daily=False,
                 records_path=os.path.join(tempfile.mkdtemp(), "records.json"))
        g.player.fuel = 0.5
        for _ in range(100):
            g.tick(0.2)
            if g.over:
                break
        self.assertTrue(g.over)
        self.assertEqual(g.outcome, "dead")
        self.assertEqual(g.records_snapshot["runs"], 1)
        self.assertEqual(g.records_snapshot["total_banked"], 0)


if __name__ == "__main__":
    unittest.main()
