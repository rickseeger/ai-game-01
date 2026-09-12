"""Player, monster, loot, and beacon data models (DESIGN.md section 6).

These classes are plain data holders plus a little convenience behaviour.
The simulation rules (movement, fuel, AI, scoring) live in ``game.py``,
``ai.py`` and ``mapgen.py`` so the models stay small and testable.
"""

from . import config


class Player:
    """The Lamplighter: position, facing, fuel, hearts, flares, score."""

    def __init__(self, x, y, facing=0):
        self.x = x
        self.y = y
        self.facing = facing  # index into config.FACINGS
        self.fuel = float(config.MAX_FUEL)
        self.hearts = config.MAX_HEARTS
        self.flares = config.STARTING_FLARES
        self.score = 0

    @property
    def dx(self):
        return config.FACINGS[self.facing][0]

    @property
    def dy(self):
        return config.FACINGS[self.facing][1]

    @property
    def facing_name(self):
        return config.FACING_NAMES[self.facing]

    def turn(self, steps):
        self.facing = (self.facing + steps) % 4

    def front_cell(self):
        return self.x + self.dx, self.y + self.dy

    def back_cell(self):
        return self.x - self.dx, self.y - self.dy


class Loot:
    """A pick-up: one of oil cask, lumen shard, flare, or map fragment."""

    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.kind = kind  # config.OIL_CASK / LUMEN_SHARD / FLARE / MAP_FRAGMENT

    @property
    def glyph(self):
        return self.kind


class Monster:
    """A Guttered shadow-creature.  State is mutated by ``ai.step_monster``."""

    WANDER = "WANDER"
    CHASE = "CHASE"
    STUNNED = "STUNNED"

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.state = self.WANDER
        self.wander_timer = 0.0
        self.chase_timer = 0.0
        self.attack_timer = 0.0
        self.stun_timer = 0.0
        self.flee_remaining = 0


class Beacon:
    """A ring's beacon (or the Root on ring 7)."""

    def __init__(self, x, y, is_root=False):
        self.x = x
        self.y = y
        self.is_root = is_root
        self.lit = False

    @property
    def glyph(self):
        return config.ROOT_BEACON if self.is_root else config.BEACON
