# EMBERLIGHT

A first-person ASCII raycast dungeon descent for the terminal. Descend into
the Buried City of Verrenn, relight the dead beacons, and race your dying
lantern back to the surface before the dark takes you.

Canonical game design lives in [DESIGN.md](DESIGN.md) - read that first.
This repository is the G7 mission tree for building the game one node at a
time; the current state is the **node 4 Windows port** of the node 3 engine and playable core loop.

## What is here (node 3)

The full playable game, implemented directly from DESIGN.md:

- A DDA **raycast renderer** (`emberlight/engine.py`) that draws the world as
  a 60-degree first-person ASCII view with a 5-step distance shade ramp,
  per-column z-buffer, and billboard sprites for beacons, stairs, loot and
  monsters. Monochrome-safe (pure-ASCII fallback).
- The **light cone** mechanic: your lantern projects a wedge whose radius
  shrinks with your remaining fuel - the screen literally closes in as the
  ember drains.
- Seeded **procedural generation** (`emberlight/mapgen.py`): a
  recursive-backtracker maze with loop carving, a border entrance, a beacon
  at maximum BFS distance, and the section-8.2 entity budgets. A daily seed
  produces the *same* maze for everyone; a free seed is replayable.
- The **playable loop** (`emberlight/game.py`): grid movement with
  90-degree turns, strafe and sprint; fuel drain with ring scaling, dread and
  sprint costs; beacon relighting (2s hold, attracts monsters); flare repel
  and stun; automatic loot pickup; the seven-ring descent; the ascent
  gauntlet (beacons go dark, monsters respawn); and win / lose / bank states.
- Deterministic **monster AI** (`emberlight/ai.py`): WANDER / CHASE / STUNNED,
  sight + hearing detection, and a 1.0s attack windup.
- Persistent **records** (`emberlight/records.py`) at
  `~/.emberlight/records.json`, plus a Records screen and Today's Descent /
  Free Descent title menu.

## Requirements

- Python 3.10 or newer.
- Linux / macOS: standard library only - no installs required.
- Windows: install the single optional dependency (`python` does not ship
  curses on Windows):

  ```
  pip install windows-curses
  ```

## Windows

The Windows port is first-class. For the full install-and-run guide see
[WINDOWS.md](WINDOWS.md), and grab the ready-to-run release artifact
[`release/emberlight-windows-v0.3.0.zip`](release/emberlight-windows-v0.3.0.zip):
extract it, `pip install windows-curses`, then double-click `run.bat`
(`run.bat` locates Python for you, trying `python` then the `py` launcher).
On a legacy console that cannot display the unicode block-shade / heart
glyphs the game falls back to the pure-ASCII glyph set automatically; set
`EMBERLIGHT_ASCII=1` to force ASCII anywhere.

## Run

```
python -m emberlight          # interactive terminal game
python -m emberlight --demo   # render a static seeded frame to stdout
python -m emberlight --version
```

Convenience launchers: `./run.sh` (Linux/macOS) or `run.bat` (Windows).

The interactive game needs a curses-capable terminal. With no terminal (CI,
pipes) it falls back to the demo render and still exits cleanly. If curses is
unavailable it prints a one-line message and exits cleanly, never crashing.

## Controls

| Key(s)        | Action                                  |
|---------------|-----------------------------------------|
| W / Up        | Step forward                            |
| S / Down      | Step backward                           |
| A / Left      | Turn left 90 degrees                    |
| D / Right     | Turn right 90 degrees                   |
| Q / E         | Strafe left / right                     |
| Shift + W     | Sprint forward (costs extra fuel)       |
| Space         | Interact (relight beacon / use stairs)  |
| F             | Flare (repels and stuns nearby monsters)|
| M             | Toggle the minimap                      |
| Esc           | Abort the run (returns to the menu)     |

Note: DESIGN.md lists E as both strafe-right and interact. Node 3 resolves
this by binding E to strafe-right and Space to interact, so the two actions
never collide.

## Test

The harness is the standard library `unittest` - zero dependencies, so the
exact same command works on Linux and Windows:

```
python -m unittest discover -s tests -v
```

The suite covers procedural generation (determinism, connectivity, budgets),
the raycaster (DDA, shade ramp, light cone, sprite occlusion), and the full
game loop headlessly (movement, fuel, relight, flare, monster AI, ascent,
scoring, records, and a scripted end-to-end descent + relight + ascent +
bank).

## Install / build

There is no compile step (Python is interpreted). To install the package and
the `emberlight` console script into a virtualenv:

```
python -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
emberlight --demo
```

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs the demo
smoke-run and the test suite on `ubuntu-latest` and `windows-latest` for
Python 3.10, 3.12, and 3.13 on every push to `main` and every pull request.

## Project layout

```
ai-game-01/
  README.md            this file
  DESIGN.md            canonical game design spec (from node 1)
  pyproject.toml       packaging / build metadata
  requirements.txt     (empty on Linux; windows-curses noted for Windows)
  run.sh / run.bat     convenience launchers
  WINDOWS.md           Windows install & run guide (node 4)
  .github/workflows/   CI (Linux + Windows matrix)
  release/             ready-to-run Windows zip artifact
  tools/               package_windows.py (builds the release zip)
  emberlight/
    __init__.py        package + __version__
    __main__.py        enables `python -m emberlight`
    main.py            entry point / curses game loop / menu dispatch
    config.py          constants and tables (single source of truth)
    mapgen.py          seeded floor generation (maze, beacon, entities)
    engine.py          DDA raycaster, z-buffer, sprite projection
    entities.py        player, monster, loot, beacon data models
    ai.py              monster state machine (WANDER / CHASE / STUNNED)
    render.py          HUD, frame compositor, minimap, demo frame
    game.py            the headless Game simulation (press + tick)
    input.py           curses terminal setup / teardown / key mapping
    records.py         records.json load / save / update
    ui.py              title menu, records screen, summary screen
  tests/
    test_smoke.py      trivial smoke tests
    test_mapgen.py     procedural generation
    test_engine.py     raycaster / light cone / sprites
    test_game.py       game mechanics
    test_records.py    records persistence
    test_core_loop.py  end-to-end scripted run
```

## License

To be decided by the repository owner.
