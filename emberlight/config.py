"""Canonical constants and tables from DESIGN.md.

This module is the single source of truth for every tunable number in the
game.  Node 3 (engine and mechanics) must read its constants from here rather
than re-typing them.  Section references below point into DESIGN.md.

All values are mirrored exactly from the design document so a later audit can
diff this module against the spec mechanically.
"""

# --- Rendering (DESIGN.md section 3) ---------------------------------------
FOV_DEGREES = 60
MAX_RAY_COLUMNS = 160
MIN_TERM_COLS = 80
MIN_TERM_ROWS = 24

# Shade ramp: (max_distance, shade_glyph, ascii_fallback).  Near = full block,
# far = space.  The ascii fallback column keeps walls readable on any terminal.
SHADE_RAMP = (
    (1.5, "\u2588", "#"),   # full block
    (3.0, "\u2593", "o"),   # dark shade
    (5.0, "\u2592", "+"),   # medium shade
    (8.0, "\u2591", "."),   # light shade
    (float("inf"), " ", " "),  # beyond view
)

# --- Light cone (DESIGN.md section 4) --------------------------------------
DEFAULT_LIGHT_RADIUS = 6
LIGHT_RADIUS_MIN = 2


def light_radius_for_fuel(fuel: float) -> int:
    """L = max(2, round(6 * fuel/100)); vision shrinks as fuel drains."""
    return max(LIGHT_RADIUS_MIN, round(DEFAULT_LIGHT_RADIUS * fuel / MAX_FUEL))


# --- Fuel / health / flare (DESIGN.md sections 6.2, 6.3, 6.5) --------------
MAX_FUEL = 100
MAX_HEARTS = 3

STARTING_FLARES = 2
MAX_FLARES = 5
FLARE_COST_FUEL = 5
FLARE_RADIUS = 4
FLARE_STUN_SECONDS = 2.0

# --- Relight (DESIGN.md section 6.4) ---------------------------------------
RELIGHT_HOLD_SECONDS = 2.0
RELIGHT_COST_FUEL = 10
RELIGHT_ATTRACT_RADIUS = 6

# --- Loot (DESIGN.md section 6.6) ------------------------------------------
OIL_CASK_FUEL = 35
MAP_FRAGMENT_REVEAL = 5  # reveal a 5x5 region

# --- Rings (DESIGN.md section 8.1) -----------------------------------------
RING_SIDES = (20, 24, 28, 32, 36, 40, 40)
RING_COUNT = len(RING_SIDES)

# Entity budget per ring: (monsters, oil, shards, flares, map_fragments)
# (DESIGN.md section 8.2)
ENTITY_BUDGET = (
    (3, 5, 4, 1, 1),
    (5, 4, 6, 1, 1),
    (7, 3, 8, 1, 1),
    (9, 2, 10, 2, 1),
    (11, 2, 12, 2, 1),
    (13, 1, 14, 2, 1),
    (15, 1, 16, 2, 1),
)
MAP_FRAGMENT_CHANCE = 0.5  # 50% chance per ring (section 8.2 note)

# --- Fuel drain rates, ember/second (DESIGN.md section 8.3) ----------------
FUEL_DRAIN_BASE = 1.0
FUEL_DRAIN_RING_MULT = 0.25  # +0.25 * (ring - 1) per second
FUEL_DRAIN_SPRINT = 1.5
FUEL_DRAIN_DREAD = 1.0  # monster adjacent

# --- Monster AI (DESIGN.md sections 8.4 and 9.2) ---------------------------
MONSTER_DETECT_SIGHT = 6   # line-of-sight tiles
MONSTER_DETECT_HEARING = 2  # no line-of-sight needed
MONSTER_CHASE_SECONDS = 0.6
MONSTER_WANDER_SECONDS = 1.0
MONSTER_WANDER_CHANCE = 0.5
MONSTER_ATTACK_WINDUP = 1.0
MONSTER_ATTACK_DAMAGE = 1

# --- Score (DESIGN.md section 8.5) -----------------------------------------
SCORE_BEACON = 100         # times ring
SCORE_SHARD = 25           # times ring
SCORE_ROOT = 5000
SCORE_ROOT_MULTIPLIER = 2
SCORE_RETURN_PER_FUEL = 1

# --- Ascent (DESIGN.md section 8.6) ----------------------------------------
ASCENT_MONSTER_RESPAWN_RATIO = 0.5

# --- Cell types (DESIGN.md section 13.3) -----------------------------------
WALL = "#"
FLOOR = "."
ENTRANCE = "^"
DESCENT = ">"
BEACON = "B"
ROOT_BEACON = "R"
OIL_CASK = "o"
LUMEN_SHARD = "*"
FLARE = "+"
MAP_FRAGMENT = "?"
MONSTER = "M"

# --- Key bindings (DESIGN.md section 13.2) ---------------------------------
# Note: Q is overloaded in the spec (strafe-left in the world, quit in the
# menu); node 3 resolves this by input context.
KEY_FORWARD = ("w", "W")
KEY_BACK = ("s", "S")
KEY_TURN_LEFT = ("a", "A")
KEY_TURN_RIGHT = ("d", "D")
KEY_STRAFE_LEFT = ("q", "Q")
KEY_STRAFE_RIGHT = ("e", "E")
KEY_INTERACT = (" ", "e", "E")
KEY_FLARE = ("f", "F")
KEY_MINIMAP = ("m", "M")
KEY_QUIT = ("q", "Q", "\x1b")


# --- Node 3 additions (engine / mechanics) ---------------------------------
# These tune values are implied by DESIGN.md but not spelled out as named
# constants there; they are captured here so the whole game reads one table.

# Death (DESIGN.md sections 6.2 and 10): fuel=0 fades to black over 2s.
DEATH_FADE_SECONDS = 2.0

# Sprint (DESIGN.md sections 6.1 and 8.3): Shift+W is a single forward cell
# at a higher fuel cost (the "+1.5/s while sprinting" applies to the step).
SPRINT_FUEL_COST = 1.5

# Lit-beacon ambient light and safe zone (DESIGN.md section 6.4).  Because a
# recursive-backtracker maze is one fully connected component, "room" is
# modelled as a small radius around the beacon: monsters neither enter nor
# respawn inside it, and the player's light is boosted while near it.
AMBIENT_RADIUS = 6
SAFE_ZONE_RADIUS = 2

# Flare (DESIGN.md sections 6.5 and 9.2): repel (flee) distance in tiles.
FLARE_FLEE_TILES = 3

# Facing vectors in (dx, dy) order: N, E, S, W (grid y grows downward).
FACINGS = ((0, -1), (1, 0), (0, 1), (-1, 0))
FACING_NAMES = ("N", "E", "S", "W")
