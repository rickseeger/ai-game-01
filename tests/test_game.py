"""Game mechanics tests: movement, fuel, relight, flare, AI, ascent, scoring."""

import os
import tempfile
import unittest

from emberlight import config
from emberlight.entities import Loot, Monster
from emberlight.game import Game


def _game(seed=123, **kw):
    kw.setdefault("records_path", os.path.join(tempfile.mkdtemp(), "records.json"))
    return Game(seed, **kw)


def _place_adjacent_to_beacon(game):
    """Put the player on a walkable cell adjacent to the current beacon."""
    b = game.floor.beacon
    for dx, dy in config.FACINGS:
        nx, ny = b.x + dx, b.y + dy
        if game.floor.walkable(nx, ny) and game.floor.monster_at(nx, ny) is None:
            game.player.x, game.player.y = nx, ny
            game.floor.monsters = []  # isolate the relight beat
            return True
    return False


class MovementTest(unittest.TestCase):
    def test_forward_into_floor(self):
        g = _game()
        g.floor.monsters = []
        # stand on the entrance, face inward, ensure front is walkable
        g.player.x, g.player.y = g.floor.entrance
        g._face_inward()
        fx, fy = g.player.front_cell()
        if g.floor.walkable(fx, fy):
            g.press("w")
            self.assertEqual((g.player.x, g.player.y), (fx, fy))

    def test_blocked_by_wall(self):
        g = _game()
        # find a floor cell with a wall directly in front
        for (x, y) in g.floor.floor_cells():
            for facing in range(4):
                g.player.x, g.player.y = x, y
                g.player.facing = facing
                fx, fy = g.player.front_cell()
                if not g.floor.walkable(fx, fy):
                    g.press("w")
                    self.assertEqual((g.player.x, g.player.y), (x, y))
                    return
        self.fail("no wall-facing floor cell found")

    def test_turn_and_strafe(self):
        g = _game()
        g.player.facing = 0
        g.press("d")
        self.assertEqual(g.player.facing, 1)  # N -> E
        g.press("a")
        self.assertEqual(g.player.facing, 0)

    def test_blocked_by_monster(self):
        g = _game()
        g.floor.monsters = []
        g.player.x, g.player.y = g.floor.entrance
        g._face_inward()
        fx, fy = g.player.front_cell()
        if not g.floor.walkable(fx, fy):
            return
        g.floor.monsters.append(Monster(fx, fy))
        g.press("w")
        self.assertEqual((g.player.x, g.player.y), g.floor.entrance)


class FuelTest(unittest.TestCase):
    def test_fuel_drains_over_time(self):
        g = _game()
        g.floor.monsters = []
        before = g.player.fuel
        g.tick(1.0)
        self.assertAlmostEqual(g.player.fuel, before - config.FUEL_DRAIN_BASE,
                               places=5)

    def test_deep_ring_drains_faster(self):
        g = _game()
        g.floor.monsters = []
        g.current_ring = 2  # ring 3: +0.25*2
        before = g.player.fuel
        g.tick(1.0)
        expected = config.FUEL_DRAIN_BASE + config.FUEL_DRAIN_RING_MULT * 2
        self.assertAlmostEqual(g.player.fuel, before - expected, places=5)

    def test_fuel_zero_fades_then_death(self):
        g = _game()
        g.floor.monsters = []
        g.player.fuel = 0.01
        g.tick(0.1)
        self.assertTrue(g.fading)
        self.assertFalse(g.over)
        g.tick(config.DEATH_FADE_SECONDS)
        self.assertTrue(g.over)
        self.assertEqual(g.outcome, "dead")

    def test_light_radius_shrinks_with_fuel(self):
        g = _game()
        g.player.fuel = 100
        self.assertEqual(g.light_radius(), 6)
        g.player.fuel = 50
        self.assertEqual(g.light_radius(), 3)
        g.player.fuel = 0
        self.assertEqual(g.light_radius(), config.LIGHT_RADIUS_MIN)


class RelightTest(unittest.TestCase):
    def test_relight_hold_two_seconds(self):
        g = _game()
        self.assertTrue(_place_adjacent_to_beacon(g))
        fuel0 = g.player.fuel
        g.press(" ")            # begin channel
        self.assertTrue(g.interacting)
        g.tick(1.0)             # not yet
        self.assertFalse(g.floor.beacon.lit)
        g.tick(1.0)             # completes at 2s
        self.assertTrue(g.floor.beacon.lit)
        # -10 relight cost plus ~2s of base drain during the hold
        self.assertAlmostEqual(g.player.fuel,
                                fuel0 - config.RELIGHT_COST_FUEL - 2.0)
        self.assertEqual(g.player.score, config.SCORE_BEACON * 1)
        self.assertEqual(g.floor.cell(*g.floor.descent), config.DESCENT)

    def test_relight_cancelled_by_moving(self):
        g = _game()
        self.assertTrue(_place_adjacent_to_beacon(g))
        g.press(" ")
        g.press("a")            # turn cancels the channel
        self.assertFalse(g.interacting)
        self.assertFalse(g.floor.beacon.lit)


class FlareTest(unittest.TestCase):
    def test_flare_stuns_and_repels(self):
        g = _game()
        g.floor.monsters = []
        g.player.x, g.player.y = g.floor.entrance
        g._face_inward()
        fx, fy = g.player.front_cell()
        if g.floor.walkable(fx, fy):
            m = Monster(fx, fy)
            g.floor.monsters.append(m)
            flares0 = g.player.flares
            fuel0 = g.player.fuel
            g.press("f")
            self.assertEqual(g.player.flares, flares0 - 1)
            self.assertAlmostEqual(g.player.fuel, fuel0 - config.FLARE_COST_FUEL)
            self.assertEqual(m.state, Monster.STUNNED)
            self.assertGreater(abs(m.x - g.player.x) + abs(m.y - g.player.y), 1)


class MonsterAITest(unittest.TestCase):
    def test_monster_chases_and_attacks(self):
        g = _game()
        g.floor.monsters = []
        # place a monster two cells away in open space
        g.player.x, g.player.y = g.floor.entrance
        g._face_inward()
        m = None
        for dx, dy in config.FACINGS:
            fx, fy = g.player.x + dx, g.player.y + dy
            if g.floor.walkable(fx, fy):
                m = Monster(fx, fy)
                g.floor.monsters.append(m)
                break
        self.assertIsNotNone(m)
        hearts0 = g.player.hearts
        # run time forward; the monster is within hearing (adjacent) and will
        # attack after the 1s windup while staying adjacent.
        for _ in range(30):
            g.tick(0.2)
        self.assertLess(g.player.hearts, hearts0)


class ScoreAndPickupTest(unittest.TestCase):
    def test_oil_cask_pickup(self):
        g = _game()
        g.floor.monsters = []
        g.player.x, g.player.y = g.floor.entrance
        g._face_inward()
        fx, fy = g.player.front_cell()
        if not g.floor.walkable(fx, fy):
            return
        g.floor.loot.append(Loot(fx, fy, config.OIL_CASK))
        g.player.fuel = 50.0
        g.press("w")
        self.assertEqual(g.player.fuel, 85.0)  # capped at 100, +35

    def test_shard_scores_by_ring(self):
        g = _game()
        g.floor.monsters = []
        g.current_ring = 2  # ring 3
        g.player.x, g.player.y = g.floor.entrance
        g._face_inward()
        fx, fy = g.player.front_cell()
        if not g.floor.walkable(fx, fy):
            return
        g.floor.loot.append(Loot(fx, fy, config.LUMEN_SHARD))
        g.press("w")
        self.assertEqual(g.player.score, config.SCORE_SHARD * 3)


class AscentAndBankTest(unittest.TestCase):
    def test_descent_and_ascent_state(self):
        g = _game()
        self.assertTrue(_place_adjacent_to_beacon(g))
        g.press(" ")
        g.tick(2.0)              # light ring 1 beacon, reveal stairs
        self.assertTrue(g.floor.beacon.lit)
        dx, dy = g.floor.descent
        g.player.x, g.player.y = dx, dy   # stand on the stairs
        g.press(" ")                     # descend to ring 2
        self.assertEqual(g.current_ring, 1)
        # ascend back to ring 1 via its entrance
        ex, ey = g.floor.entrance
        g.player.x, g.player.y = ex, ey
        g.press(" ")
        self.assertEqual(g.current_ring, 0)
        self.assertEqual(g.phase, "ascend")
        self.assertFalse(g.floor.beacon.lit)  # the dark returned

    def test_surface_banks_score_with_return_bonus(self):
        g = _game()
        g.player.score = 1000
        g.player.fuel = 42
        g.player.x, g.player.y = g.floor.entrance  # ring 1 entrance
        g.press(" ")                              # surface
        self.assertTrue(g.over)
        self.assertEqual(g.outcome, "banked")
        self.assertEqual(g.final_score, 1000 + 42)  # +1 per remaining fuel

    def test_win_doubles_score(self):
        g = _game()
        g.root_lit = True
        g.player.score = 1000
        g.player.fuel = 50
        g.player.x, g.player.y = g.floor.entrance
        g.press(" ")
        self.assertEqual(g.outcome, "won")
        self.assertEqual(g.final_score, (1000 + 50) * 2)

    def test_records_persist_after_bank(self):
        g = _game(seed=999)
        g.player.score = 500
        g.player.x, g.player.y = g.floor.entrance
        g.press(" ")
        self.assertTrue(os.path.exists(g.records_path))
        self.assertEqual(g.records_snapshot["runs"], 1)
        self.assertEqual(g.records_snapshot["total_banked"], 500 + int(g.player.fuel))


if __name__ == "__main__":
    unittest.main()


class SeedDeterminismTest(unittest.TestCase):
    def test_ring_layout_independent_of_gameplay_rng(self):
        # A seed must yield the same maze for everyone (DESIGN.md section 9),
        # so mapgen must not drift with monster-wander randomness.
        a = _game(seed=555)
        b = _game(seed=555)
        a.floor.monsters = []
        for _ in range(100):
            a.tick(0.1)          # consume gameplay rng in `a` only
        a._enter_ring(3)
        b._enter_ring(3)
        self.assertEqual(["".join(r) for r in a.floor.grid],
                         ["".join(r) for r in b.floor.grid])
        self.assertEqual(a.floor.entrance, b.floor.entrance)
        self.assertEqual((a.floor.beacon.x, a.floor.beacon.y),
                         (b.floor.beacon.x, b.floor.beacon.y))
