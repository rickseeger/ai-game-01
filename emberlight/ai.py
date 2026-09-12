"""Monster state machine (DESIGN.md sections 9.2 and 8.4).

WANDER / CHASE / STUNNED, detection by sight (Bresenham line-of-sight, 6
tiles) and hearing (2 tiles), a 1.0s attack windup, and flare repel/stun.
Wander decisions draw from the caller's seeded ``random.Random`` so a seed
reproduces the same monster behaviour given the same player inputs.
"""

import math

from . import config
from .entities import Monster
from .mapgen import line_of_sight


def _dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def _in_safe_zone(x, y, lit_beacons):
    for b in lit_beacons:
        if max(abs(x - b.x), abs(y - b.y)) <= config.SAFE_ZONE_RADIUS:
            return True
    return False


def can_enter(floor, x, y, occupied, lit_beacons):
    """A cell a monster may step into: walkable, unoccupied, not a safe zone."""
    if not floor.walkable(x, y):
        return False
    if (x, y) in occupied:
        return False
    if _in_safe_zone(x, y, lit_beacons):
        return False
    return True


def _step_toward(mon, tx, ty, floor, occupied, lit_beacons):
    """Greedy one-cell step toward (tx, ty), preferring the axis that closes
    most distance, then the other axis, then any open adjacent cell."""
    options = []
    for sx, sy in config.FACINGS:
        if can_enter(floor, mon.x + sx, mon.y + sy, occupied, lit_beacons):
            options.append((_dist(mon.x + sx, mon.y + sy, tx, ty), sx, sy))
    if not options:
        return False
    options.sort(key=lambda o: o[0])
    _, sx, sy = options[0]
    mon.x += sx
    mon.y += sy
    return True


def _step_away(mon, tx, ty, floor, occupied, lit_beacons):
    """Greedy one-cell step maximising distance from (tx, ty)."""
    best = None
    for sx, sy in config.FACINGS:
        if can_enter(floor, mon.x + sx, mon.y + sy, occupied, lit_beacons):
            d = _dist(mon.x + sx, mon.y + sy, tx, ty)
            if best is None or d > best[0]:
                best = (d, sx, sy)
    if best:
        _, sx, sy = best
        mon.x += sx
        mon.y += sy
        return True
    return False


def flee(mon, tx, ty, floor, occupied, lit_beacons, tiles):
    """Repel a monster ``tiles`` cells away from (tx, ty); return True on move."""
    moved = False
    for _ in range(tiles):
        if not _step_away(mon, tx, ty, floor, occupied, lit_beacons):
            break
        moved = True
    return moved


def step_monster(mon, floor, player, dt, rng, lit_beacons, occupied):
    """Advance one monster by ``dt`` seconds.  Returns an event string or None.

    Events: "windup" (a monster begins its 1.0s attack windup), "attack" (the
    windup lands, dealing ``MONSTER_ATTACK_DAMAGE`` to the player).
    """
    px, py = player.x, player.y

    if mon.state == Monster.STUNNED:
        mon.stun_timer -= dt
        if mon.stun_timer <= 0:
            mon.state = Monster.WANDER
            mon.wander_timer = 0.0
        return None

    d = _dist(mon.x, mon.y, px, py)

    if mon.state == Monster.WANDER:
        if (d <= config.MONSTER_DETECT_HEARING
                or (d <= config.MONSTER_DETECT_SIGHT
                    and line_of_sight(floor, mon.x, mon.y, px, py))):
            mon.state = Monster.CHASE
            mon.chase_timer = 0.0
        else:
            mon.wander_timer -= dt
            if mon.wander_timer <= 0:
                mon.wander_timer = config.MONSTER_WANDER_SECONDS
                if rng.random() < config.MONSTER_WANDER_CHANCE:
                    dx, dy = rng.choice(config.FACINGS)
                    if can_enter(floor, mon.x + dx, mon.y + dy,
                                 occupied, lit_beacons):
                        mon.x += dx
                        mon.y += dy
            return None

    # CHASE: only step when not already adjacent; adjacent monsters hold
    # position and attack instead of sidling back and forth.
    adjacent = abs(mon.x - px) + abs(mon.y - py) == 1
    if not adjacent:
        mon.chase_timer -= dt
        if mon.chase_timer <= 0:
            mon.chase_timer = config.MONSTER_CHASE_SECONDS
            _step_toward(mon, px, py, floor, occupied, lit_beacons)
    else:
        mon.chase_timer = 0.0

    if adjacent:
        # Adjacent: 1.0s attack windup then damage, repeating each 1.0s.
        if mon.attack_timer <= 0:
            mon.attack_timer = config.MONSTER_ATTACK_WINDUP
            return "windup"
        mon.attack_timer -= dt
        if mon.attack_timer <= 0:
            player.hearts -= config.MONSTER_ATTACK_DAMAGE
            mon.attack_timer = config.MONSTER_ATTACK_WINDUP
            return "attack"
    else:
        mon.attack_timer = 0.0

    return None
