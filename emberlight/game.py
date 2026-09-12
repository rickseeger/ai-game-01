"""The Game: one EMBERLIGHT run, headless and curses-free.

Owns the world state (player, cached rings, monsters, loot), the discrete
movement/interact/flare actions, the real-time ``tick`` (fuel drain, monster
AI, relight channel, death fade), scoring, the ascent gauntlet, and the
win/lose/bank states.  Everything is driven through ``press`` + ``tick`` so
the same object powers the curses loop and the automated tests.
"""

import math
import random

from . import ai, config, mapgen, records
from .entities import Monster, Player


def _manhattan(ax, ay, bx, by):
    return abs(ax - bx) + abs(ay - by)


def _neighbors(x, y):
    return [(x + dx, y + dy) for dx, dy in config.FACINGS]


class Game:
    def __init__(self, seed, daily=False, records_path=None, rng=None):
        self.seed = int(seed)
        self.seed_str = str(self.seed)
        self.daily = bool(daily)
        self.rng = rng if rng is not None else random.Random(self.seed)
        self.records_path = records_path or records.records_path()

        self.player = Player(0, 0)
        self.rings = {}          # ring_index -> mapgen.Floor (cached)
        self.current_ring = 0
        self.floor = None
        self.phase = "descend"   # descend | ascend
        self.over = False
        self.outcome = None      # dead | banked | won
        self.final_score = 0     # banked score (0 if dead)
        self.root_lit = False
        self.max_ring = 1        # deepest ring reached (1-based)
        self.message = ""
        self.minimap_on = False
        self.interacting = False
        self.interact_timer = 0.0
        self.fading = False
        self.death_timer = 0.0
        self.records_snapshot = None

        self._enter_ring(0)

    # -- level transitions --------------------------------------------------
    def _enter_ring(self, ring_index, arrival="entrance"):
        if ring_index not in self.rings:
            # Each ring's maze derives from (seed, ring) independently of any
            # gameplay randomness, so a daily seed yields the *same* maze for
            # everyone regardless of how the monsters happened to wander.
            # (DESIGN.md section 9: "same maze for everyone that day".)
            ring_rng = random.Random(self.seed * 1000 + ring_index)
            self.rings[ring_index] = mapgen.generate_floor(ring_rng, ring_index)
        self.floor = self.rings[ring_index]
        self.current_ring = ring_index
        if arrival == "descent":
            x, y = self.floor.descent
        else:
            x, y = self.floor.entrance
        self.player.x, self.player.y = x, y
        self._face_inward()
        self.max_ring = max(self.max_ring, ring_index + 1)
        self._mark_explored()

    def _face_inward(self):
        self.player.facing = mapgen.facing_into(self.floor,
                                                self.player.x, self.player.y)

    def _ascend_one(self):
        self.phase = "ascend"
        prev = self.current_ring - 1
        self._enter_ring(prev, arrival="descent")
        self._apply_ascent_darkening(prev)
        self.message = "You climb back toward the surface. The dark returns."

    def _apply_ascent_darkening(self, ring_index):
        """Beacons go dark again and monsters respawn at 50% (section 8.6)."""
        floor = self.rings[ring_index]
        if getattr(floor, "darkened", False):
            return
        floor.darkened = True
        floor.beacon.lit = False
        count = int(config.ENTITY_BUDGET[ring_index][0]
                    * config.ASCENT_MONSTER_RESPAWN_RATIO)
        floor.monsters = self._fresh_monsters(floor, count)

    def _fresh_monsters(self, floor, count):
        excluded = set()
        ex, ey = floor.entrance
        excluded.add((ex, ey))
        excluded.update(_neighbors(ex, ey))
        b = floor.beacon
        excluded.add((b.x, b.y))
        excluded.update(_neighbors(b.x, b.y))
        px, py = self.player.x, self.player.y
        excluded.add((px, py))
        excluded.update(_neighbors(px, py))
        available = [c for c in floor.floor_cells() if c not in excluded]
        self.rng.shuffle(available)
        out = []
        for _ in range(count):
            if not available:
                break
            x, y = available.pop()
            out.append(Monster(x, y))
        return out

    # -- movement / actions -------------------------------------------------
    def _try_move(self, dx, dy):
        nx, ny = self.player.x + dx, self.player.y + dy
        if not self.floor.walkable(nx, ny):
            return False
        if self.floor.monster_at(nx, ny) is not None:
            return False
        self.player.x, self.player.y = nx, ny
        self._pickup_at(nx, ny)
        return True

    def _strafe(self, direction):
        idx = (self.player.facing + direction) % 4
        dx, dy = config.FACINGS[idx]
        self._try_move(dx, dy)

    def _pickup_at(self, x, y):
        item = self.floor.loot_at(x, y)
        if item is None:
            return
        ring = self.current_ring + 1
        if item.kind == config.OIL_CASK:
            self.player.fuel = min(config.MAX_FUEL,
                                   self.player.fuel + config.OIL_CASK_FUEL)
            self.message = "You drink deep of the oil cask (+35 ember)."
        elif item.kind == config.LUMEN_SHARD:
            gain = config.SCORE_SHARD * ring
            self.player.score += gain
            self.message = f"A lumen shard (+{gain} score)."
        elif item.kind == config.FLARE:
            self.message = "You find a flare."
            if self.player.flares < config.MAX_FLARES:
                self.player.flares += 1
            else:
                self.message = "You cannot carry any more flares."
        elif item.kind == config.MAP_FRAGMENT:
            self.floor.reveal_square(x, y, config.MAP_FRAGMENT_REVEAL)
            self.message = "A map fragment reveals the nearby passages."
        self.floor.loot.remove(item)

    def _interact(self):
        px, py = self.player.x, self.player.y
        cell = self.floor.cell(px, py)

        if cell == config.DESCENT and self.current_ring < config.RING_COUNT - 1:
            self._enter_ring(self.current_ring + 1, arrival="entrance")
            self.interacting = False
            self.message = f"You descend to ring {self.current_ring + 1}."
            return

        if cell == config.ENTRANCE:
            if self.current_ring == 0:
                self._surface()
            else:
                self._ascend_one()
            return

        b = self.floor.beacon
        if not b.lit and _manhattan(px, py, b.x, b.y) == 1:
            if self.interacting:
                self.interacting = False
                self.message = "You release the beacon."
            else:
                self.interacting = True
                self.interact_timer = 0.0
                self.message = "You begin to relight the beacon..."
            return

        self.interacting = False

    def _relight(self, beacon):
        self.player.fuel = max(0.0, self.player.fuel - config.RELIGHT_COST_FUEL)
        beacon.lit = True
        self.floor.reveal_stairs()
        ring = self.current_ring + 1
        if beacon.is_root:
            self.player.score += config.SCORE_ROOT
            self.root_lit = True
            self.message = "The Root blazes alight! The dark recoils."
        else:
            gain = config.SCORE_BEACON * ring
            self.player.score += gain
            self.message = f"Ring {ring} beacon relit (+{gain} score)."

    def _flare(self):
        p = self.player
        if p.flares <= 0:
            self.message = "You have no flares left."
            return
        if p.fuel < config.FLARE_COST_FUEL:
            self.message = "Not enough ember to strike a flare."
            return
        p.flares -= 1
        p.fuel = max(0.0, p.fuel - config.FLARE_COST_FUEL)
        occupied = {(m.x, m.y) for m in self.floor.monsters}
        lit = [self.floor.beacon] if self.floor.beacon.lit else []
        for mon in self.floor.monsters:
            if self._dist(mon.x, mon.y, p.x, p.y) <= config.FLARE_RADIUS:
                mon.state = mon.STUNNED
                mon.stun_timer = config.FLARE_STUN_SECONDS
                mon.flee_remaining = config.FLARE_FLEE_TILES
                ai.flee(mon, p.x, p.y, self.floor, occupied, lit,
                        config.FLARE_FLEE_TILES)
                occupied.add((mon.x, mon.y))
        self.message = "Flare! The dark shrieks and recoils."
        if p.fuel <= 0:
            self.fading = True
            self.death_timer = 0.0

    def _surface(self):
        self.player.score += int(self.player.fuel) * config.SCORE_RETURN_PER_FUEL
        score = self.player.score
        if self.root_lit:
            score *= config.SCORE_ROOT_MULTIPLIER
        self._finish("won" if self.root_lit else "banked", score)

    def _finish(self, outcome, final_score=0):
        if self.over:
            return
        self.over = True
        self.outcome = outcome
        self.final_score = final_score
        survived = outcome in ("banked", "won")
        rec = records.load_records(self.records_path)
        records.record_run(rec, seed_str=self.seed_str, daily=self.daily,
                           banked_score=final_score, depth=self.max_ring,
                           root_lit=self.root_lit, survived=survived)
        records.save_records(rec, self.records_path)
        self.records_snapshot = rec

    # -- real-time simulation ----------------------------------------------
    def tick(self, dt):
        if self.over:
            return
        if self.fading:
            self.death_timer += dt
            if self.death_timer >= config.DEATH_FADE_SECONDS:
                self._finish("dead")
            return

        p = self.player
        ring = self.current_ring + 1
        drain = config.FUEL_DRAIN_BASE + config.FUEL_DRAIN_RING_MULT * (ring - 1)
        if self._any_adjacent_monster():
            drain += config.FUEL_DRAIN_DREAD
        p.fuel -= drain * dt
        if p.fuel <= 0:
            p.fuel = 0.0
            self.fading = True
            self.death_timer = 0.0
            self.message = "Your lantern gutters out..."
            return

        if self.interacting:
            b = self.floor.beacon
            for mon in self.floor.monsters:
                if self._dist(mon.x, mon.y, p.x, p.y) <= config.RELIGHT_ATTRACT_RADIUS:
                    mon.state = mon.CHASE
            self.interact_timer += dt
            if b.lit or _manhattan(p.x, p.y, b.x, b.y) != 1:
                self.interacting = False
            elif self.interact_timer >= config.RELIGHT_HOLD_SECONDS:
                self._relight(b)
                self.interacting = False

        self._step_monsters(dt)
        if p.hearts <= 0:
            self._finish("dead")
            return
        self._mark_explored()

    def _step_monsters(self, dt):
        p = self.player
        occupied = {(m.x, m.y) for m in self.floor.monsters}
        occupied.add((p.x, p.y))
        lit = [self.floor.beacon] if self.floor.beacon.lit else []
        for mon in self.floor.monsters:
            ev = ai.step_monster(mon, self.floor, p, dt, self.rng, lit, occupied)
            if ev == "windup":
                self.message = "A Guttered draws close, ready to strike..."
            elif ev == "attack":
                self.message = "The dark claws you!"

    def _any_adjacent_monster(self):
        p = self.player
        for m in self.floor.monsters:
            if _manhattan(m.x, m.y, p.x, p.y) == 1:
                return True
        return False

    # -- vision / rendering support ----------------------------------------
    def light_radius(self):
        L = config.light_radius_for_fuel(self.player.fuel)
        b = self.floor.beacon
        if b.lit:
            d = max(abs(self.player.x - b.x), abs(self.player.y - b.y))
            if d <= config.AMBIENT_RADIUS:
                L = max(L, config.AMBIENT_RADIUS - d + 1)
        return L

    def _mark_explored(self):
        floor = self.floor
        L = self.light_radius()
        if L <= 0:
            return
        facing = math.atan2(self.player.dy, self.player.dx)
        half = math.radians(config.FOV_DEGREES) / 2.0 + 0.01
        px, py = self.player.x, self.player.y
        for y in range(max(0, py - L), min(floor.side, py + L + 1)):
            for x in range(max(0, px - L), min(floor.side, px + L + 1)):
                dx, dy = x - px, y - py
                d = math.hypot(dx, dy)
                if d > L:
                    continue
                ang = (math.atan2(dy, dx) - facing + math.pi) % (2 * math.pi) - math.pi
                if abs(ang) <= half:
                    floor.explored[y][x] = True

    @staticmethod
    def _dist(ax, ay, bx, by):
        return math.hypot(ax - bx, ay - by)

    # -- discrete input -----------------------------------------------------
    def press(self, key):
        if self.over or self.fading:
            return
        p = self.player
        if key in ("w", "up"):
            self.interacting = False
            self._try_move(p.dx, p.dy)
        elif key == "W":  # sprint: forward at extra fuel cost
            self.interacting = False
            if self._try_move(p.dx, p.dy):
                p.fuel = max(0.0, p.fuel - config.SPRINT_FUEL_COST)
                if p.fuel <= 0:
                    p.fuel = 0.0
                    self.fading = True
                    self.death_timer = 0.0
                    self.message = "Your lantern gutters out..."
        elif key in ("s", "down"):
            self.interacting = False
            self._try_move(-p.dx, -p.dy)
        elif key in ("a", "left"):
            self.interacting = False
            p.turn(-1)
        elif key in ("d", "right"):
            self.interacting = False
            p.turn(1)
        elif key == "q":
            self.interacting = False
            self._strafe(-1)
        elif key == "e":
            self.interacting = False
            self._strafe(1)
        elif key == "f":
            self.interacting = False
            self._flare()
        elif key == " ":
            self._interact()
        elif key == "m":
            self.minimap_on = not self.minimap_on
        self._mark_explored()
