"""EMBERLIGHT entry point.

Modes
-----
``python -m emberlight``             interactive terminal view (curses)
``python -m emberlight --demo``      render a static frame to stdout, exit 0
``python -m emberlight --version``   print the version, exit 0

The interactive view is intentionally minimal for node 2 (a title screen that
waits for Q/Esc).  Node 3 replaces ``run_interactive`` with the real menu and
game loop.
"""

import argparse
import sys

from . import __version__
from . import input as input_mod
from . import render


def run_interactive() -> int:
    """Start the interactive terminal view.  Exits cleanly everywhere."""
    if not sys.stdout.isatty():
        # No TTY (CI, pipes): fall back to the demo render so the entry point
        # still renders something and exits cleanly in any environment.
        print("No interactive terminal detected; showing demo frame.", file=sys.stderr)
        return run_demo()

    try:
        stdscr, curses = input_mod.init_terminal()
    except input_mod.TerminalUnavailableError as exc:
        # DESIGN.md section 13.1: print a one-line message and exit cleanly.
        print(str(exc), file=sys.stderr)
        return 0
    except Exception as exc:  # curses.error on odd terminals, etc.
        print(f"Could not start the interactive view: {exc}", file=sys.stderr)
        return 0

    try:
        max_rows, max_cols = stdscr.getmaxyx()
        stdscr.clear()
        start_row = 2
        for i, line in enumerate(render.TITLE):
            stdscr.addstr(start_row + i, 2, line[: max_cols - 4])
        prompt = "EMBERLIGHT - press Q (or Esc) to quit."
        stdscr.addstr(start_row + len(render.TITLE) + 2, 2, prompt[: max_cols - 4])
        stdscr.refresh()
        while True:
            key = stdscr.getch()
            if key in (ord("q"), ord("Q"), 27):  # 27 = Esc
                break
        return 0
    finally:
        input_mod.shutdown_terminal(curses)


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
