"""EMBERLIGHT - a first-person ASCII raycast dungeon descent for the terminal.

Descend into the Buried City of Verrenn, relight the dead beacons, and race
your dying lantern back to the surface before the dark takes you.

Node 3 ships the full engine and playable loop, implemented directly from
DESIGN.md: the DDA raycast renderer with the light-cone mechanic, seeded
procedural generation, monster AI, beacons/loot/flares, the ascent gauntlet,
persistent records, and the interactive curses loop.  The whole simulation is
driven headlessly through ``Game`` so it is unit-tested without a terminal.
"""

__version__ = "0.2.0"
