"""Title menu, records screen, and run-summary screens (DESIGN.md section 10).

All screens are curses-based and take the already-initialised ``stdscr``; the
game loop itself lives in ``main.py``.  Every screen returns the next mode or
waits for a key press, and never raises.
"""

from . import config, render


def _draw(stdscr, lines, max_cols):
    stdscr.erase()
    for row, line in enumerate(lines):
        try:
            stdscr.addstr(row, 0, line[:max_cols])
        except Exception:
            pass
    stdscr.refresh()


def title_menu(stdscr, curses):
    """Show the title menu; return "daily", "free", "records", or None."""
    lines = list(render.TITLE)
    lines += [
        "",
        "  1 / T   Today's Descent  (the shared daily seed)",
        "  2 / F   Free Descent     (a fresh random seed)",
        "  3 / R   Records",
        "",
        "  Q / Esc Quit",
    ]
    while True:
        rows, cols = stdscr.getmaxyx()
        _draw(stdscr, lines, cols)
        key = stdscr.getch()
        if key == -1:
            continue
        ch = _key_char(key, curses)
        if ch in ("1", "t", "T"):
            return "daily"
        if ch in ("2", "f", "F"):
            return "free"
        if ch in ("3", "r", "R"):
            return "records"
        if ch in ("q", "Q", "esc"):
            return None


def records_screen(stdscr, curses, records):
    """Show the records screen; wait for any key."""
    lines = [
        "  R E C O R D S",
        "",
        f"  Best depth    : {records.get('best_depth', 0)}",
        f"  Best score    : {records.get('best_score', 0)}",
        f"  Total banked  : {records.get('total_banked', 0)}",
        f"  Runs          : {records.get('runs', 0)}",
        f"  Root lit      : {'yes' if records.get('root_lit') else 'no'}",
        "",
    ]
    daily = records.get("daily", {})
    if daily:
        lines.append("  Today's Descent history:")
        for day in sorted(daily)[-6:]:
            d = daily[day]
            lines.append(f"    {day}: depth {d.get('best_depth', 0)}, "
                         f"score {d.get('best_score', 0)}")
    lines += ["", "  Press any key to return."]
    while True:
        rows, cols = stdscr.getmaxyx()
        _draw(stdscr, lines, cols)
        if stdscr.getch() != -1:
            return


def summary_screen(stdscr, curses, game):
    """Show the end-of-run summary; wait for any key."""
    if game.outcome == "dead":
        result = "You died in the dark."
    elif game.outcome == "banked":
        result = "You surfaced safely and banked your haul."
    elif game.outcome == "won":
        result = "YOU RELIT THE ROOT AND ESCAPED. A true win!"
    else:
        result = "The run ended."

    lines = [
        "  D E S C E N T   O V E R",
        "",
        f"  {result}",
        "",
        f"  Seed      : {game.seed_str}"
        + ("  (Today's Descent)" if game.daily else "  (Free Descent)"),
        f"  Depth     : ring {game.max_ring} of {config.RING_COUNT}",
        f"  Score     : {game.final_score}",
        f"  Root lit  : {'yes' if game.root_lit else 'no'}",
        f"  Fuel left : {int(game.player.fuel)}",
        "",
        "  Press any key to return to the menu.",
    ]
    while True:
        rows, cols = stdscr.getmaxyx()
        _draw(stdscr, lines, cols)
        if stdscr.getch() != -1:
            return


def _key_char(key, curses):
    if key == -1:
        return None
    if key == 27:
        return "esc"
    if key in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT):
        return None
    if 0 <= key < 256:
        return chr(key)
    return None
