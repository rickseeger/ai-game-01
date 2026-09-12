"""EMBERLIGHT entry point and curses game loop.

Modes
-----
``python -m emberlight``             interactive terminal view (curses)
``python -m emberlight --demo``      render a static frame to stdout, exit 0
``python -m emberlight --version``   print the version, exit 0

The interactive view opens a title menu (Today's Descent / Free Descent /
Records), then runs the real-time raycast game loop.  Everything is built on
the headless ``Game`` object so the same simulation drives the tests.
"""

import argparse
import datetime
import random
import sys
import time

from . import __version__
from . import config
from . import input as input_mod
from . import records, render, ui
from .game import Game


def run_interactive() -> int:
    """Start the interactive terminal view.  Exits cleanly everywhere."""
    if not sys.stdout.isatty():
        print("No interactive terminal detected; showing demo frame.", file=sys.stderr)
        return run_demo()

    try:
        stdscr, curses = input_mod.init_terminal()
    except input_mod.TerminalUnavailableError as exc:
        print(str(exc), file=sys.stderr)
        return 0
    except Exception as exc:
        print(f"Could not start the interactive view: {exc}", file=sys.stderr)
        return 0

    try:
        while True:
            mode = ui.title_menu(stdscr, curses)
            if mode is None:
                return 0
            if mode == "records":
                ui.records_screen(stdscr, curses, records.load_records())
                continue
            game = _new_game(mode)
            run_game(stdscr, curses, game)
            ui.summary_screen(stdscr, curses, game)
    finally:
        input_mod.shutdown_terminal(curses)


def _new_game(mode):
    if mode == "daily":
        seed = int(datetime.date.today().strftime("%Y%m%d"))
        return Game(seed, daily=True)
    seed = random.randint(1, 10**9)
    return Game(seed, daily=False)


def run_game(stdscr, curses, game):
    """The real-time curses loop for one run."""
    stdscr.nodelay(True)
    last = time.monotonic()
    while not game.over:
        now = time.monotonic()
        dt = min(now - last, 0.1)
        last = now

        while True:
            key = stdscr.getch()
            if key == -1:
                break
            ch = input_mod.translate_key(key, curses)
            if ch is None:
                continue
            if ch == "esc":
                game.press(" ")  # no-op; Esc quits via the menu only
                # Esc during play returns to the menu (quit the run).
                game._finish("dead", 0)
                return
            game.press(ch)
            if game.over:
                break

        game.tick(dt)

        rows, cols = stdscr.getmaxyx()
        frame = render.render_frame(game, cols, rows,
                                    ascii_fallback=input_mod.prefer_ascii())
        stdscr.erase()
        for r, line in enumerate(frame):
            if r >= rows:
                break
            try:
                stdscr.addstr(r, 0, line[:cols])
            except Exception:
                pass
        stdscr.refresh()
        time.sleep(0.03)


def run_demo() -> int:
    """Render a static demo frame to stdout and exit 0."""
    for line in render.demo_frame():
        print(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="emberlight",
        description="EMBERLIGHT - a first-person ASCII raycast dungeon descent.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="render a static demo frame to stdout and exit",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="print the version and exit",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        print(f"emberlight {__version__}")
        return 0
    if args.demo:
        return run_demo()
    return run_interactive()


if __name__ == "__main__":
    raise SystemExit(main())
