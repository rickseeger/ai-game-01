"""ASCII rendering helpers for EMBERLIGHT.

Node 2 ships only the pieces needed to prove the pipeline works end to end:

* a shade ramp lookup (DESIGN.md section 3),
* an ASCII title banner,
* a self-contained `demo_frame()` that renders a first-person-looking
  corridor without any curses or interactive terminal.

Node 3 replaces/extends this module with the real per-column DDA raycaster,
the z-buffer, and sprite projection.
"""

from . import config


def shade_for(distance: float, ascii_fallback: bool = False) -> str:
    """Return the shade glyph for a wall at ``distance``.

    Uses the 5-step ramp from DESIGN.md section 3.  When ``ascii_fallback``
    is true, return the ASCII column instead so walls stay readable on any
    terminal.
    """
    for max_distance, shade_glyph, ascii_glyph in config.SHADE_RAMP:
        if distance <= max_distance:
            return ascii_glyph if ascii_fallback else shade_glyph
    return " "


TITLE = [
    "  E M B E R L I G H T",
    "",
    "  EMBERLIGHT - a first-person ASCII raycast dungeon descent",
]


def demo_frame(columns: int = 48, rows: int = 14, ascii_fallback: bool = False):
    """Render one static corridor frame as a list of text lines.

    A fake first-person view: a corridor whose walls are far in the centre
    and near at the edges, drawn with the shade ramp, plus a HUD line and a
    floor baseline.  Curses-free on purpose so it runs on any terminal and
    on CI.
    """
    half = columns // 2
    distances = [1.0 + abs(col - half) * 0.7 for col in range(columns)]

    wall_heights = []
    for d in distances:
        # near walls are taller; clamp to the frame height
        wall_heights.append(max(1, min(rows - 2, int(rows * 1.6 / d))))

    lines = []
    # HUD (top status line) per DESIGN.md section 7
    lines.append("[R1/7] [EMBER ########## 100] [hhh] [Flares 2] [Score 0] [N]")

    for row in range(rows):
        line = []
        for col in range(columns):
            height = wall_heights[col]
            top_edge = (rows - height) // 2
            bottom_edge = top_edge + height
            if row < top_edge:
                line.append(" ")  # ceiling
            elif row < bottom_edge:
                line.append(shade_for(distances[col], ascii_fallback))
            else:
                line.append(".")  # floor
        lines.append("".join(line).rstrip())

    lines.append("")
    lines.append("EMBERLIGHT skeleton (node 2) - `python -m emberlight` for the interactive view.")
    return lines
