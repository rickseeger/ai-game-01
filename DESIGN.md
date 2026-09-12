# EMBERLIGHT - Game Design Document

A first-person ASCII raycast dungeon descent for the terminal.
Descend into the buried city, relight the dead beacons, and get out before your lantern dies and the dark takes you.

Status: Canonical design spec for G7 node 1. Implement directly from this document (node 3, engine and mechanics). No unresolved strategic decisions remain below.

---

## 0. One-line pitch

"You are the last Lamplighter. Descend the Seven Rings of a sunken city, relight its beacons one by one, and race your dying lantern back to the surface, because the light is your life, your map, and your only weapon."

---

## 1. Design pillars (constraints every mechanic must serve)

1. Light is life. Fuel is a constantly draining countdown. Darkness literally shrinks what you can see. Everything else serves this tension.
2. Push your luck. Every ring offers a choice: grab more, or go deeper for a bigger score. Deeper means more risk and more reward. You may bank by returning to the surface at any time.
3. Tiny scope, deep replay. A run is 5 to 15 minutes. Procedural floors, a daily shared seed, and a depth and score record make "one more run" the default reaction.
4. Grid purity. A 90-degree-turn grid crawler rendered as a first-person raycast. Nothing diagonal, no physics, no aiming. Navigation, resource tension, and nerve are the whole game.

---

## 2. Setting

The Buried City of Verrenn. A subterranean metropolis sunk by an ancient catastrophe (the Sinking). It is built in seven concentric rings descending into the earth; the deepest is simply called the Root.

The player is a Lamplighter, one of a dwindling order sworn to keep the city's beacon-towers lit, for the beacons are what hold the Guttered (shadow-creatures) at bay. Each beacon that goes dark lets the dark press a little closer.

A descent is a single expedition: enter the Well at the surface, light beacons ring by ring, and either return to the surface with your haul or die in the dark. The true goal is to light the Root, the unlit beacon at the center of the seventh ring, and live to tell of it.

Tone: quiet, cold, and tense. Not gory. The horror is economic - fuel, distance, and the knowledge that the way back is now dark again.

---

## 3. Perspective and rendering approach

First-person raycasting (Wolfenstein and "3D Monster Maze" style) rendered entirely as ASCII in a full-screen curses terminal. This is the "ASCII 3D world walkthrough" feel: you move through a 3D-looking world on a 2D grid, one 90-degree turn at a time.

Concrete spec:

- Grid: the world is a 2D array of cells (see section 8). Each cell is one of a small set of types.
- Raycasting: DDA (digital differential analysis) per screen column. For each column, cast one ray across a 60-degree field of view, find the first wall hit, and compute distance d. Column height on screen = screen_height / d. Shade the column by distance using a 5-step ramp.
- Shade ramp (near to far), chosen for monochrome-terminal safety and warmth:
  ```
  distance d      shade glyph      ascii fallback
  d <= 1.5        full block        "#"
  d <= 3.0        dark shade        "o"
  d <= 5.0        medium shade      "+"
  d <= 8.0        light shade       "."
  d >  8.0        space             " "
  ```
  The five shade glyphs are, in order: full block (U+2588), dark shade (U+2593), medium shade (U+2592), light shade (U+2591), space. If the terminal font cannot render the Unicode shades, fall back to the ascii column above so walls remain readable on any terminal.
  Optional colour (if the terminal supports it, else fall back to monochrome): ember-orange for near walls, fading to a dim blue-gray for far walls. Colour must degrade gracefully, never a hard requirement.
- Floor and ceiling: ceiling = spaces; floor = a single baseline row of period characters just below the wall columns; everything below the baseline is blank. This gives the walkthrough horizon look with minimal complexity.
- Sprites (entities): monsters, beacons, and loot are projected the same way. Compute relative bearing and distance, draw the glyph at its column(s), sized by 1/d, and clipped behind walls using a per-column z-buffer. Only draw a sprite if it is within the player's light cone (section 4) and not occluded.
- Minimap (optional, toggle m): top-right 2D char map, fog-of-war (only explored cells shown), player drawn as a caret oriented by facing. The map fragment loot reveals a region.
- HUD: single status line across the top, always visible (section 7).
- Resolution: adaptive to terminal size; minimum playable 80x24. Default FOV 60 degrees, target render width = terminal width, cap ray count at 160 columns for performance.

---

## 4. The light cone (central mechanic)

Your lantern projects a light cone: a 60-degree wedge, the same as your FOV, with a radius L tiles. You can only see (and monsters are only rendered for) what is inside the cone and within radius L.

- Default L = 6 tiles.
- L scales with remaining fuel: L = max(2, round(6 * fuel/100)). As fuel drains, your vision physically closes in. At fuel <= 30, you are effectively stumbling.
- The cone is drawn as the rendered world itself (the raycast is the cone). No separate overlay needed.

This makes fuel a sensory resource, not just a number. The screen getting darker and tighter is the core feeling of the game.

---

## 5. Core loop

The run loop (5 to 15 minutes):

1. Enter the Well at the surface (ring 1's entrance).
2. On the current ring, navigate the procedurally-generated maze to find the ring's Beacon.
3. Relight the Beacon (stand adjacent, hold interact for 2 seconds). Relighting costs 10 fuel and, during the 2 seconds, monsters within hearing range are drawn toward you (a deliberate risk beat).
4. Loot the ring (optional): oil casks (fuel), lumen shards (score), flares, map fragments. The longer you loot, the more fuel you spend.
5. Descend to the next ring via the stairs that the lit beacon reveals. Each ring is harder (section 8).
6. Decide to bank or push. At any lit beacon you may instead return to the surface, a final gauntlet retracing your path upward through floors that have gone dark again (section 8.6). Reaching the surface banks your score. Going deeper risks losing it all.
7. Light the Root (ring 7) for a times-2 multiplier (the win condition), then survive the ascent.

The per-run micro-loop (30 seconds): every 15 to 30 seconds you face one small decision - burn fuel to explore that side passage for shards or oil, or beeline to the beacon? Fuel is always draining; the passage might be empty. This is the moment-to-moment hook.

---

## 6. Primary mechanics

### 6.1 Movement (grid, 90-degree turns)
- W / Up: step forward one cell.
- S / Down: step backward one cell.
- A / Left: turn left 90 degrees.
- D / Right: turn right 90 degrees.
- Q / E: strafe left / strafe right one cell (without turning).
- Shift plus W: sprint (move forward, drains extra fuel; see section 8.3). Sprint is a single-cell forward move at higher fuel cost, not a continuous run.
- Movement is cell-by-cell (discrete), no diagonal, no collision with monsters (monsters occupy cells; walking into one is prevented, forcing a dodge around).

### 6.2 Lantern fuel ("ember")
- Max fuel = 100. Drains over time (see section 8.3). Refill via oil casks (+35 each, capped at 100).
- fuel = 0 means the screen fades to black over 2 seconds, then death (the dark takes you).

### 6.3 Monsters - "the Guttered"
Shadow-creatures with simple, deterministic AI (see section 9.2). Primary interaction is avoidance, not combat.
- Health: the player has 3 hearts. A monster hit removes 1 heart. 0 hearts means death.
- Monsters have no health bar - you cannot fight them directly. The only defensive tool is the flare (section 6.5).
- Monsters are only visible (rendered) when inside your light cone and within radius L.

### 6.4 Beacons (the objective)
- A ring has exactly one beacon. Stand adjacent and hold interact (Space or E) for 2 seconds to relight it.
- Relighting costs 10 fuel and attracts monsters within 6 tiles (they path toward you during the 2 seconds).
- A lit beacon: permanently illuminates its room (ambient light there even outside your cone, so draw the room fully), awards score (section 7), and reveals the descent stairs.
- Lit-beacon rooms are safe zones: monsters do not enter or respawn in a lit room.

### 6.5 Flare (limited defensive tool)
- F: expend one flare. Effect: for one moment the entire current room lights up; monsters within radius 4 are repelled (flee 3 tiles) and stunned (do not act) for 2 seconds.
- Cost: 5 fuel plus one flare. Start with 2 flares; find more as loot.

### 6.6 Loot
| Glyph | Item         | Effect                              |
|-------|--------------|-------------------------------------|
| o     | Oil cask     | +35 fuel (cap 100)                  |
| *     | Lumen shard  | +score (see section 7)              |
| +     | Flare        | +1 flare (cap 5)                    |
| ?     | Map fragment | Reveal a 5x5 region of the minimap  |

Pick-up is automatic on stepping onto the cell (no separate key), with a brief on-screen confirmation.

### 6.7 Minimap
- M toggles. Fog-of-war: only explored cells drawn. Player = caret oriented by facing, explored floor = period, walls = hash, beacon = B, stairs = greater-than, loot = its glyph, monsters shown only when currently visible in the light cone.

---

## 7. HUD (single top status line)

```
[R3/7] [EMBER ########-- 43] [hhh] [Flares 2] [Score 1280] [N]
```
- [R3/7]: current ring / total (7).
- [EMBER ########-- 43]: a 10-segment fuel bar plus numeric percent.
- [hhh]: hearts remaining (drawn as filled or empty heart glyphs, or h/o letters for monochrome).
- [Flares 2]: flares remaining.
- [Score 1280]: current run score.
- [N]: facing (N/E/S/W).

A second, bottom line shows transient messages (for example: "A beacon hums nearby", "You hear skittering in the dark.", "The Root awaits.").

---

## 8. Difficulty and progression - the Seven Rings

### 8.1 Ring dimensions (grid side length, square)
| Ring | Side |
|------|------|
| 1    | 20   |
| 2    | 24   |
| 3    | 28   |
| 4    | 32   |
| 5    | 36   |
| 6    | 40   |
| 7    | 40 (denser maze) |

### 8.2 Entity budget per ring (exact counts)
| Ring | Monsters | Oil casks | Lumen shards | Flares | Map fragments |
|------|----------|-----------|--------------|--------|---------------|
| 1    | 3        | 5         | 4            | 1      | 1 (50% chance)|
| 2    | 5        | 4         | 6            | 1      | 1 (50% chance)|
| 3    | 7        | 3         | 8            | 1      | 1 (50% chance)|
| 4    | 9        | 2         | 10           | 2      | 1 (50% chance)|
| 5    | 11       | 2         | 12           | 2      | 1 (50% chance)|
| 6    | 13       | 1         | 14           | 2      | 1 (50% chance)|
| 7    | 15       | 1         | 16           | 2      | 1 (50% chance)|

### 8.3 Fuel drain rates (ember per second)
- Base: 1.0/s.
- Ambient deep-ring drain: +0.25 times (ring - 1) per second (ring 7 = +1.5/s).
- Sprint: +1.5/s while sprinting (on top of base).
- Dread (monster adjacent): +1.0/s.
- Relighting a beacon: -10 instantly.
- Flare: -5 instantly.
- Oil cask: +35.

### 8.4 Monster AI parameters (full rules in section 9.2)
- Detection range: 6 tiles line-of-sight, or 2 tiles by hearing (no line-of-sight needed).
- Chase speed: move 1 step every 0.6s toward the player.
- Wander speed: 1 step every 1.0s, 50% chance.
- Attack: when adjacent, 1.0s windup then 1 damage; then re-windup 1.0s per subsequent hit.

### 8.5 Score values
- Beacon lit: +100 times ring.
- Lumen shard: +25 times ring.
- Root lit (ring 7): +5000, and doubles the entire run score.
- Return bonus: +1 per remaining fuel (banking rewards efficiency).

### 8.6 The Ascent (return gauntlet)
When you choose to return to the surface, you walk back up through each ring in reverse order. Consequences:
- Previously lit beacons have gone dark again (the dark always returns), so rooms are no longer safe zones.
- Monsters respawn at 50% of the original count (rounded down), placed in random floor cells.
- Your fuel keeps draining, so the ascent is a sprint.
- Reach ring 1's entrance (stairs-up) and interact to surface and bank the run's score.

---

## 9. Procedural generation spec (deterministic per seed)

Seed sources:
- Today's Descent: seed = YYYYMMDD (fixed daily seed, same maze for everyone that day).
- Free Descent: seed = random (chosen fresh each run, shown on the summary screen so it can be replayed).

All randomness must derive from seed via a single seeded PRNG (Python random.Random(seed)), so a seed reproduces an identical run. Replay-by-seed is a deliberate feature.

### 9.1 Floor generation algorithm
1. Build a side-by-side grid of wall cells (hash).
2. Recursive-backtracker maze on the odd cells (carve floor period cells connected by carved corridors). This yields a perfect maze.
3. Add loops: remove 10% of interior walls at random (so the maze has cycles, meaning navigation choices and fewer dead ends).
4. Guarantee connectivity with a BFS from the entrance; if any carved cell is unreachable, carve a corridor to it.
5. Place entrance (stairs-up) on a random border cell (player start). Place the beacon at the carved cell of maximum BFS distance from the entrance. Place descent stairs adjacent to the beacon (revealed only when the beacon is lit).
6. Scatter entities per the section 8.2 budget, uniformly on floor cells, excluding cells adjacent to entrance and beacon.

### 9.2 Monster AI (deterministic)
States: WANDER, CHASE, STUNNED.
- WANDER: every 1.0s, 50% chance to step to a random adjacent open cell.
- Detection: transition to CHASE if (a) clear line-of-sight (Bresenham) to the player and distance <= 6, or (b) distance <= 2 (hearing).
- CHASE: every 0.6s, step one cell toward the player (greedy: prefer the axis-aligned step that reduces distance; fall back to the other axis or a wall-avoiding alternative).
- Attack: if adjacent to the player, begin a 1.0s windup (message cue), then deal 1 damage; repeat every 1.0s while still adjacent.
- STUNNED (from flare): do not act for 2.0s, then flee 3 tiles and return to WANDER.
- Monsters never enter a lit-beacon room (safe zone) and never spawn in one.

---

## 10. Win, lose, and bank states

- Death (fuel = 0, or hearts = 0): run ends. The run's unbanked score is lost. Best-depth and best-score records update if applicable. Summary screen shows the seed, depth reached, and score.
- Return to surface (reach ring-1 stairs-up and interact): run ends as a successful return; the run's score is banked (added to lifetime total).
- Light the Root and return: a win - score times 2, and a permanent flag set in records.

---

## 11. Replayability - "what makes a human want to play again"

This is the explicit, non-negotiable answer, in priority order:

1. Push-your-luck banking. The choice to bank a safe score versus risk it for a times-2 Root win is the classic compulsion loop (Spelunky, Jetpack Joyride, Deep Rock Galactic). The unbanked score is real and visible on the HUD; losing it hurts; banking early feels safe but small. This single mechanic is the primary replay driver.
2. The light cone as a sensory clock. Because fuel directly shrinks your vision, every run feels different. Tension ratchets as the screen closes in. A run is a gradually deepening panic that is fun to re-experience precisely because it is felt, not just calculated.
3. Daily seeded run (Today's Descent). Everyone gets the same maze each day; comparing depth reached on today's seed with a friend (or the local records screen) is a daily ritual with a natural cadence.
4. Seed replayability. Any run is reproducible from its seed. "Beat my friend's depth on seed X" is a concrete, shareable goal with zero server infrastructure.
5. Short runs plus clear records. A 5 to 15 minute run length plus a persistent depth and score record (section 12) makes "one more run" cheap and "beat my best depth" the standing goal.
6. Emergent variety. Procedural maze layout, loot placement, and monster count mean no two runs play the same, even on a fixed ring budget.

---

## 12. Records (persistent, local file)

Path (platform-appropriate): ~/.emberlight/records.json on Linux/macOS, or the equivalent user-profile directory on Windows.

Schema:
```json
{
  "best_depth": 5,
  "best_score": 12840,
  "total_banked": 91000,
  "runs": 137,
  "root_lit": true,
  "daily": {
    "20260912": { "best_score": 4280, "best_depth": 4 }
  }
}
```
- best_depth, best_score, root_lit, runs update on every run end.
- total_banked increments only on successful returns.
- daily[YYYYMMDD] records the best score and depth for that day's seed (used by the Records screen).

---

## 13. Technical implementation spec

### 13.1 Language and dependencies
- Python 3.10 or newer, standard library only on Linux/macOS (curses, math, random, json, os).
- Windows: Python does not ship curses; add the precompiled windows-curses wheel as the only optional dependency (pure stdlib everywhere else). Do not introduce numpy or any native or GPU dependency.
- Fallback: if curses is unavailable, the game must print a one-line message ("Requires curses; on Windows run: pip install windows-curses") and exit cleanly, never crash.

### 13.2 Key bindings (canonical)
| Key(s)              | Action                          |
|---------------------|---------------------------------|
| W / Up              | Step forward                    |
| S / Down            | Step backward                   |
| A / Left            | Turn left 90 degrees            |
| D / Right           | Turn right 90 degrees           |
| Q / E               | Strafe left / right             |
| Shift + W           | Sprint (forward)                |
| Space / E           | Interact (relight / stairs)     |
| F                   | Flare                           |
| M                   | Toggle minimap                  |
| Esc / Q (menu)      | Quit to menu                    |

### 13.3 Cell types (canonical single-character map encoding)
| Char | Meaning                          |
|------|----------------------------------|
| #    | Wall                             |
| .    | Floor                            |
| ^    | Entrance (stairs-up, player start)|
| >    | Descent stairs (down)            |
| B    | Beacon (unlit becomes lit)       |
| R    | Root beacon (ring 7)             |
| o    | Oil cask                         |
| *    | Lumen shard                      |
| +    | Flare                            |
| ?    | Map fragment                     |
| M    | Monster spawn                    |

### 13.4 Project file structure (suggested for node 3)
```
ai-game-01/
  README.md
  DESIGN.md               (this document, canonical)
  emberlight/
    __init__.py
    main.py               (entrypoint, game loop, menu dispatch)
    config.py             (all constants and tables from this doc, single source of truth)
    mapgen.py             (seeded floor generation, section 9.1)
    engine.py             (raycasting / DDA renderer, section 3)
    entities.py           (player, monster, loot, beacon data model)
    ai.py                 (monster state machine, section 9.2)
    render.py             (ASCII rendering, shade ramp, sprites, HUD)
    input.py              (key handling, terminal setup and teardown)
    records.py            (records.json load and save, section 12)
    ui.py                 (title menu, records screen, summary screens)
  requirements.txt        (empty on Linux/macOS; note windows-curses for Windows)
```

### 13.5 Performance budget
Worst case ring 7 = 40x40 grid, 160 ray columns, roughly 40 DDA steps each = about 6400 steps per frame, plus 15 monsters. This is trivially fast in pure Python at a 15 to 30 FPS curses refresh. No optimization beyond a per-column z-buffer is required.

---

## 14. Non-goals (do NOT build these in node 3)

- No combat or weapons beyond the flare. No aiming, no projectiles.
- No inventory beyond the four loot types.
- No audio (optionally a single terminal beep on damage or death; optional, not required).
- No online or network features, no server leaderboard (local file only; a shared leaderboard is a later node).
- No metaprogression or unlocks between runs (score and depth records only; keeps scope tight and the push-your-luck loop pure).
- No save or resume mid-run (runs are short by design).

---

## 15. Acceptance criteria for the engine node (node 3)

A working build that:
1. Renders a first-person raycast view of a 20x20 ring-1 maze in curses, monochrome-safe.
2. Implements 90-degree-turn plus strafe plus forward and back movement with correct collision.
3. Drains fuel, shrinks the light cone with fuel, and kills the player at fuel 0 (2 second fade).
4. Places a beacon, allows 2 second relight (attracting monsters, -10 fuel), reveals descent stairs.
5. Implements the monster WANDER / CHASE / attack AI and the flare repel and stun exactly per sections 9.2 and 6.5.
6. Generates all 7 rings deterministically from a seed, with the section 8.2 budgets and section 8.3 drain rates.
7. Implements score (section 8.5), the ascent gauntlet (section 8.6), and the bank / win / lose states (section 10).
8. Persists records.json per section 12 and shows a Records screen.
9. Offers "Today's Descent" (seed = YYYYMMDD) and "Free Descent" from a title menu.
10. Runs on Linux/macOS with stdlib curses and on Windows with windows-curses, with a clean fallback message otherwise.

---

End of design document. Any implementation decision not specified above is deliberately left to the implementer's taste, provided it does not contradict a stated rule in this document.
