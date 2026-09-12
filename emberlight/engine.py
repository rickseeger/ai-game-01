"""Raycasting / DDA renderer (DESIGN.md section 3).

Per-column DDA raycasting across a 60-degree FOV, a per-column z-buffer for
sprite occlusion, and billboard sprite projection.  All math is pure stdlib
and produces a plain ``View`` (a 2-D char buffer) so it is trivially testable
without a terminal.
"""

import math

from . import config

_TWO_PI = 2.0 * math.pi


class View:
    """A rendered first-person frame: char buffer plus per-column z-buffer."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.buffer = [[" "] * width for _ in range(height)]
        self.zbuffer = [float("inf")] * width

    def lines(self):
        return ["".join(row).rstrip() for row in self.buffer]

    def put(self, x, y, ch):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = ch


def _dda(floor, px, py, dirx, diry, max_dist):
    """Return the euclidean distance to the first wall, or None beyond max_dist.

    ``px, py`` is the ray origin (player centre) in fractional cell coords.
    """
    map_x, map_y = int(px), int(py)
    delta_x = abs(1.0 / dirx) if dirx != 0 else float("inf")
    delta_y = abs(1.0 / diry) if diry != 0 else float("inf")
    step_x = 1 if dirx > 0 else -1
    step_y = 1 if diry > 0 else -1
    if dirx > 0:
        side_x = (map_x + 1 - px) * delta_x
    else:
        side_x = (px - map_x) * delta_x
    if diry > 0:
        side_y = (map_y + 1 - py) * delta_y
    else:
        side_y = (py - map_y) * delta_y

    for _ in range(4096):
        if side_x < side_y:
            side_x += delta_x
            map_x += step_x
            t = side_x - delta_x
        else:
            side_y += delta_y
            map_y += step_y
            t = side_y - delta_y
        if t > max_dist:
            return None
        if floor.is_wall(map_x, map_y):
            return t
    return None


def render_view(floor, player, width, height, light_radius,
                ascii_fallback=False):
    """Render the first-person view of ``floor`` from the player's position.

    ``light_radius`` is the effective light-cone radius in tiles (already
    incorporating fuel and any lit-beacon ambient boost).  Columns whose ray
    hits nothing within the cone are left blank (the dark).
    """
    view = View(width, height)
    if width <= 0 or height <= 0:
        return view

    fov = math.radians(config.FOV_DEGREES)
    facing = math.atan2(player.dy, player.dx)
    horizon = height // 2

    px = player.x + 0.5
    py = player.y + 0.5

    for col in range(width):
        angle = facing - fov / 2.0 + fov * col / (width - 1)
        dirx, diry = math.cos(angle), math.sin(angle)
        t = _dda(floor, px, py, dirx, diry, light_radius)
        if t is None:
            continue
        # Fisheye correction: perpendicular distance for height/shading.
        perp = t * math.cos(angle - facing)
        perp = max(perp, 1e-3)
        view.zbuffer[col] = perp
        wall_h = int(height / perp)
        wall_h = max(1, min(wall_h, height))
        shade = _shade_for(perp, ascii_fallback)
        top = horizon - wall_h // 2
        bottom = top + wall_h
        for row in range(max(0, top), min(height, bottom)):
            view.put(col, row, shade)
        # Floor baseline: a single period row just below the wall columns.
        view.put(col, bottom, config.FLOOR)

    _project_sprites(view, floor, player, width, height, light_radius, horizon,
                     facing, fov)
    return view


def _shade_for(distance, ascii_fallback):
    for max_d, shade_glyph, ascii_glyph in config.SHADE_RAMP:
        if distance <= max_d:
            return ascii_glyph if ascii_fallback else shade_glyph
    return " "


def _project_sprites(view, floor, player, width, height, light_radius,
                     horizon, facing, fov):
    """Project entities (beacon, stairs, entrance, loot, monsters) as sprites."""
    if width <= 0:
        return
    px = player.x + 0.5
    py = player.y + 0.5
    sprites = []

    for item in floor.loot:
        sprites.append((item.x, item.y, item.glyph))
    for mon in floor.monsters:
        sprites.append((mon.x, mon.y, config.MONSTER))
    # Terrain sprites: entrance, revealed descent stairs, and the beacon.
    ex, ey = floor.entrance
    sprites.append((ex, ey, config.ENTRANCE))
    if floor.descent is not None and floor.cell(*floor.descent) == config.DESCENT:
        dx, dy = floor.descent
        sprites.append((dx, dy, config.DESCENT))
    sprites.append((floor.beacon.x, floor.beacon.y, floor.beacon.glyph))

    # Far-to-near so nearer sprites overwrite farther ones.
    projected = []
    for sx, sy, glyph in sprites:
        rel_x = sx + 0.5 - px
        rel_y = sy + 0.5 - py
        dist = math.hypot(rel_x, rel_y)
        if dist > light_radius or dist < 1e-6:
            continue
        angle = math.atan2(rel_y, rel_x)
        bearing = angle - facing
        # Normalise to (-pi, pi].
        bearing = (bearing + math.pi) % _TWO_PI - math.pi
        if abs(bearing) > fov / 2.0 + 1e-3:
            continue
        cam_x = math.tan(bearing) / math.tan(fov / 2.0)
        screen_col = int(width / 2.0 * (1.0 + cam_x))
        if screen_col < 0 or screen_col >= width:
            continue
        if dist >= view.zbuffer[screen_col]:
            continue  # occluded behind a wall
        size = int(height / dist)
        size = max(1, min(size, height))
        projected.append((dist, screen_col, size, glyph))

    projected.sort(key=lambda s: -s[0])
    for dist, col, size, glyph in projected:
        top = horizon - size // 2
        for row in range(top, top + size):
            if 0 <= row < height:
                view.put(col, row, glyph)
