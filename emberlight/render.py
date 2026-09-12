"""ASCII rendering: HUD, full-frame compositor, minimap, and demo frame.

The heavy lifting (DDA walls, sprites, z-buffer) lives in ``engine.py``; this
module turns a ``Game`` into terminal text.  ``render_frame`` is curses-free
so it is testable headlessly, and every glyph degrades to plain ASCII when
``ascii_fallback`` is true.
"""

import math

from . import config
from . import engine


def shade_for(distance: float, ascii_fallback: bool = False) -> str:
    """Return the shade glyph for a wall at ``distance`` (DESIGN.md section 3)."""
    for max_distance, shade_glyph, ascii_glyph in config.SHADE_RAMP:
        if distance <= max_distance:
            return ascii_glyph if ascii_fallback else shade_glyph
    return " "


TITLE = [
    "  E M B E R L I G H T",
    "",
    "  EMBERLIGHT - a first-person ASCII raycast dungeon descent",
]


def _fuel_bar(fuel):
    segs = max(0, min(10, int(round(fuel / 10.0))))
    return "#" * segs + "-" * (10 - segs)


def hud_line(game, ascii_fallback=False):
    """Top status line (DESIGN.md section 7)."""
    p = game.player
    hearts = p.hearts
    filled = "h" if ascii_fallback else "\u2665"
    empty = "o" if ascii_fallback else "\u2661"
    heart_str = filled * hearts + empty * (config.MAX_HEARTS - hearts)
    ring = game.current_ring + 1
    return (
        f"[R{ring}/{config.RING_COUNT}] "
        f"[EMBER {_fuel_bar(p.fuel)} {int(p.fuel)}] "
        f"[{heart_str}] [Flares {p.flares}] [Score {p.score}] [{p.facing_name}]"
    )


def _minimap(game, ascii_fallback=False):
    """Top-right 2D map with fog-of-war, centred on the player."""
    floor = game.floor
    if floor is None:
        return []
    side = floor.side
    w = min(side, 21)
    h = min(side, 15)
    px, py = game.player.x, game.player.y
    left = max(0, min(px - w // 2, side - w))
    top = max(0, min(py - h // 2, side - h))
    facing_caret = ("^", ">", "v", "<")[game.player.facing]

    lines = []
    for y in range(top, top + h):
        row = []
        for x in range(left, left + w):
            if x == px and y == py:
                row.append(facing_caret)
            elif not floor.explored[y][x]:
                row.append(" ")
            else:
                cell = floor.cell(x, y)
                loot = floor.loot_at(x, y)
                if loot is not None:
                    row.append(loot.glyph)
                elif floor.monster_at(x, y) is not None:
                    row.append(config.MONSTER)
                elif cell == config.BEACON:
                    row.append("B" if not floor.beacon.lit else "b")
                elif cell == config.ROOT_BEACON:
                    row.append("R" if not floor.beacon.lit else "r")
                elif cell == config.WALL:
                    row.append("#")
                elif cell == config.ENTRANCE:
                    row.append("^")
                elif cell == config.DESCENT:
                    row.append(">")
                else:
                    row.append(".")
        lines.append("".join(row))
    return lines, w


def render_frame(game, width, height, ascii_fallback=False):
    """Compose one full terminal frame (HUD + view + minimap + message)."""
    width = max(1, width)
    height = max(3, height)

    lines = []
    hud = hud_line(game, ascii_fallback)
    lines.append(hud[:width])

    view_height = height - 2
    if view_height <= 0:
        view_height = 1
    ray_width = min(width, config.MAX_RAY_COLUMNS)
    view = engine.render_view(game.floor, game.player, ray_width, view_height,
                              game.light_radius(), ascii_fallback=ascii_fallback)
    view_lines = view.lines()

    # Build the full-frame grid for the view area so we can overlay the map.
    grid = [[" "] * width for _ in range(view_height)]
    left_pad = (width - ray_width) // 2
    for row in range(view_height):
        for col in range(ray_width):
            grid[row][left_pad + col] = view_lines[row][col] if col < len(view_lines[row]) else " "

    if game.minimap_on and game.floor is not None:
        map_lines, mw = _minimap(game, ascii_fallback)
        for r, mline in enumerate(map_lines):
            row = r + 1
            if 0 <= row < view_height:
                start = width - mw
                for c, ch in enumerate(mline):
                    if start + c < width:
                        grid[row][start + c] = ch

    for row in grid:
        lines.append("".join(row).rstrip())

    message = game.message
    lines.append(message[:width] if message else "")
    return lines


def demo_frame(columns=80, rows=24, ascii_fallback=True, seed=1):
    """Render a real raycast frame of a seeded ring-1 floor to stdout lines.

    Curses-free on purpose so ``--demo`` and CI can exercise the actual
    engine headlessly.
    """
    import random

    from . import entities, mapgen

    floor = mapgen.generate_floor(random.Random(seed), 0)
    player = entities.Player(floor.entrance[0], floor.entrance[1])
    # Face inward, away from the border.
    player.facing = mapgen.facing_into(floor, player.x, player.y)

    view_height = rows - 2
    ray_width = min(columns, config.MAX_RAY_COLUMNS)
    view = engine.render_view(floor, player, ray_width, view_height,
                              config.light_radius_for_fuel(player.fuel),
                              ascii_fallback=ascii_fallback)
    lines = [hud_line(_DemoGame(player, floor), ascii_fallback=ascii_fallback)[:columns]]
    lines.extend(view.lines())
    lines.append("EMBERLIGHT (node 3) - seeded ring-1 raycast; `python -m emberlight` to play.")
    return lines


class _DemoGame:
    """Minimal stand-in exposing the bits hud_line needs."""

    def __init__(self, player, floor):
        self.player = player
        self.floor = floor
        self.current_ring = 0
        self.minimap_on = False
        self.message = ""
