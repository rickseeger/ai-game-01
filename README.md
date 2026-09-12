# EMBERLIGHT

A first-person ASCII raycast dungeon descent for the terminal. Descend into the buried city of Verrenn, relight the dead beacons, and race your dying lantern back to the surface before the dark takes you.

This repository currently contains the canonical game design. The engine is implemented in a later node, directly from DESIGN.md.

## Documents

- DESIGN.md - the canonical, implementable game design specification (setting, perspective and rendering, core loop, mechanics, difficulty and progression, scoring, replayability rationale, procedural generation, and technical spec). Read this first.

## Run (once the engine lands)

```
python3 -m emberlight
```

Linux/macOS: standard library only. Windows: `pip install windows-curses` first (Python does not ship curses on Windows).
