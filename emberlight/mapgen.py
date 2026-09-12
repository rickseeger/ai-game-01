"""Seeded procedural floor generation (DESIGN.md sections 9 and 9.1).

A recursive-backtracker maze over the odd cells, loop carving, an entrance on
a random border, a beacon at maximum BFS distance, descent stairs adjacent to
it, and the section 8.2 entity budget scattered uniformly -- all driven by a
single caller-supplied ``random.Random`` so a seed reproduces an identical
run.
"""

from collections import deque

from . import config
from .entities import Beacon, Loot, Monster

# Terrain glyphs that a raycast treats as non-occluding (transparent).
_TRANSPARENT = frozenset((config.FLOOR, config.ENTRANCE, config.DESCENT,
                          config.BEACON, config.ROOT_BEACON))


class Floor:
    """One ring's generated level plus its live entity state."""

    def __init__(self, ring_index, side, grid, entrance, beacon, descent,
                 loot, monsters):
        self.ring_index = ring_index  # 0-based (ring 1 == 0)
        self.side = side
        self.grid = grid              # list of list of single-char cells
        self.entrance = entrance      # (x, y) stairs-up / player arrival
        self.beacon = beacon          # Beacon
        self.descent = descent        # (x, y) or None for ring 7
        self.loot = loot              # list[Loot]
        self.monsters = monsters      # list[Monster]
        self.explored = [[False] * side for _ in range(side)]
        self._mark_explored(entrance[0], entrance[1])

    # -- geometry helpers ---------------------------------------------------
    def in_bounds(self, x, y):
        return 0 <= x < self.side and 0 <= y < self.side

    def cell(self, x, y):
        return self.grid[y][x]

    def is_wall(self, x, y):
        return not self.in_bounds(x, y) or self.grid[y][x] == config.WALL

    def is_opaque(self, x, y):
        return self.grid[y][x] == config.WALL

    def walkable(self, x, y):
        """Can a player or monster stand here?  Walls and beacon towers block."""
        if not self.in_bounds(x, y):
            return False
        return self.grid[y][x] not in (config.WALL, config.BEACON,
                                       config.ROOT_BEACON)

    def floor_cells(self):
        """All standable, non-tower floor cells (for entity placement)."""
        out = []
        for y in range(self.side):
            for x in range(self.side):
                if self.grid[y][x] == config.FLOOR:
                    out.append((x, y))
        return out

    def _mark_explored(self, x, y):
        if self.in_bounds(x, y):
            self.explored[y][x] = True

    def reveal_square(self, cx, cy, radius):
        """Reveal a radius-by-radius square region (map fragment, section 6.6)."""
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                self._mark_explored(x, y)

    def reveal_stairs(self):
        """Called when the beacon is lit: reveal the descent stairs."""
        if self.descent is not None:
            x, y = self.descent
            self.grid[y][x] = config.DESCENT

    # -- entity access ------------------------------------------------------
    def loot_at(self, x, y):
        for item in self.loot:
            if item.x == x and item.y == y:
                return item
        return None

    def monster_at(self, x, y):
        for mon in self.monsters:
            if mon.x == x and mon.y == y:
                return mon
        return None


def line_of_sight(floor, x0, y0, x1, y1):
    """Bresenham line of sight: True if no wall cell lies strictly between."""
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while not (x == x1 and y == y1):
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
        if (x == x1 and y == y1):
            break
        if floor.is_opaque(x, y):
            return False
    return True


def _carve_entrance(rng, grid, side):
    """Carve a border entrance and connect it to the interior; return (x, y)."""
    border = rng.randrange(4)
    odd = rng.randrange(1, side - 1, 2)  # align with a maze cell
    if border == 0:      # top
        x, y = odd, 0
        grid[y][x] = config.FLOOR
    elif border == 1:    # bottom
        x, y = odd, side - 1
        grid[y][x] = config.FLOOR
        grid[y - 1][x] = config.FLOOR
    elif border == 2:    # left
        x, y = 0, odd
        grid[y][x] = config.FLOOR
    else:                # right
        x, y = side - 1, odd
        grid[y][x] = config.FLOOR
        grid[y][x - 1] = config.FLOOR
    grid[y][x] = config.ENTRANCE
    return x, y


def _bfs(floor, start):
    """BFS distances over standable cells from ``start``; unreachable -> None."""
    dist = {start: 0}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in config.FACINGS:
            nx, ny = x + dx, y + dy
            if (nx, ny) in dist:
                continue
            if floor.walkable(nx, ny):
                dist[(nx, ny)] = dist[(x, y)] + 1
                q.append((nx, ny))
    return dist


def _neighbors(cell):
    x, y = cell
    return [(x + dx, y + dy) for dx, dy in config.FACINGS]


def generate_floor(rng, ring_index):
    """Build the ``ring_index``-th floor (0-based) deterministically from rng."""
    side = config.RING_SIDES[ring_index]
    grid = [["#"] * side for _ in range(side)]

    # 1 + 2. Recursive-backtracker maze over odd cells.
    cells = [(x, y) for x in range(1, side - 1, 2) for y in range(1, side - 1, 2)]
    for x, y in cells:
        grid[y][x] = config.FLOOR
    start = rng.choice(cells)
    visited = {start}
    stack = [start]
    directions = list(config.FACINGS)
    while stack:
        cx, cy = stack[-1]
        options = []
        for dx, dy in directions:
            nx, ny = cx + 2 * dx, cy + 2 * dy
            if (1 <= nx < side - 1 and 1 <= ny < side - 1
                    and (nx, ny) not in visited):
                options.append((nx, ny, dx, dy))
        if options:
            nx, ny, dx, dy = rng.choice(options)
            grid[cy + dy][cx + dx] = config.FLOOR
            visited.add((nx, ny))
            stack.append((nx, ny))
        else:
            stack.pop()

    # 3. Loops: remove 10% of interior walls.
    interior_walls = [(x, y) for y in range(1, side - 1)
                      for x in range(1, side - 1) if grid[y][x] == config.WALL]
    rng.shuffle(interior_walls)
    for x, y in interior_walls[: max(1, len(interior_walls) // 10)]:
        grid[y][x] = config.FLOOR

    # 4/5. Entrance on a random border, connected inward.
    entrance = _carve_entrance(rng, grid, side)
    floor = Floor(ring_index, side, grid, entrance, None, None, [], [])
    floor.explored[entrance[1]][entrance[0]] = True

    # 4. Connectivity guarantee: reach every floor cell from the entrance.
    dist = _bfs(floor, entrance)
    reachable = set(dist)
    all_floor = set(floor.floor_cells()) | {entrance}
    for cell in all_floor - reachable:
        _carve_corridor_to(grid, cell, reachable)
    dist = _bfs(floor, entrance)  # recompute after any carving

    # 5. Beacon at maximum BFS distance from the entrance.
    max_d = max(dist.values())
    farthest = [c for c, d in dist.items() if d == max_d and c != entrance]
    bx, by = rng.choice(farthest)
    is_root = ring_index == config.RING_COUNT - 1
    beacon = Beacon(bx, by, is_root=is_root)
    grid[by][bx] = beacon.glyph

    # Descent stairs adjacent to the beacon (not on ring 7).
    descent = None
    if ring_index < config.RING_COUNT - 1:
        candidates = [n for n in _neighbors((bx, by))
                      if floor.walkable(n[0], n[1])]
        if candidates:
            dx, dy = rng.choice(candidates)
            descent = (dx, dy)  # kept hidden (grid stays '.') until lit

    # 6. Scatter entities per the ring budget.
    loot, monsters = _scatter_entities(rng, floor, entrance, (bx, by), descent,
                                       config.ENTITY_BUDGET[ring_index])

    floor.beacon = beacon
    floor.descent = descent
    floor.loot = loot
    floor.monsters = monsters
    return floor


def _carve_corridor_to(grid, cell, reachable):
    """Carve a straight corridor from ``cell`` toward the reachable set."""
    x, y = cell
    side = len(grid)
    for dx, dy in config.FACINGS:
        nx, ny = x, y
        while 0 <= nx < side and 0 <= ny < side and (nx, ny) not in reachable:
            if grid[ny][nx] == config.WALL:
                grid[ny][nx] = config.FLOOR
            nx += dx
            ny += dy
        if 0 <= nx < side and 0 <= ny < side:
            return  # connected to the reachable region


def _scatter_entities(rng, floor, entrance, beacon, descent, budget):
    """Place loot and monsters on floor cells, avoiding entrance/beacon areas."""
    excluded = set()
    for anchor in (entrance, beacon, descent):
        if anchor is None:
            continue
        excluded.add(anchor)
        excluded.update(_neighbors(anchor))

    available = [c for c in floor.floor_cells() if c not in excluded]
    rng.shuffle(available)

    monsters_n, oil, shards, flares, map_frags = budget
    loot = []
    monsters = []

    def take():
        return available.pop() if available else None

    for _ in range(oil):
        c = take()
        if c:
            loot.append(Loot(c[0], c[1], config.OIL_CASK))
    for _ in range(shards):
        c = take()
        if c:
            loot.append(Loot(c[0], c[1], config.LUMEN_SHARD))
    for _ in range(flares):
        c = take()
        if c:
            loot.append(Loot(c[0], c[1], config.FLARE))
    if map_frags and rng.random() < config.MAP_FRAGMENT_CHANCE:
        c = take()
        if c:
            loot.append(Loot(c[0], c[1], config.MAP_FRAGMENT))
    for _ in range(monsters_n):
        c = take()
        if c:
            monsters.append(Monster(c[0], c[1]))

    return loot, monsters


def facing_into(floor, x, y):
    """Pick the facing that looks down the longest open corridor from (x, y).

    Used to orient the player inward on arrival so the opening view is a
    corridor rather than a wall one cell away.
    """
    best = 0
    best_len = -1
    for i, (dx, dy) in enumerate(config.FACINGS):
        n = 0
        cx, cy = x, y
        while floor.walkable(cx + dx, cy + dy):
            cx += dx
            cy += dy
            n += 1
            if n > 64:
                break
        if n > best_len:
            best_len = n
            best = i
    return best
