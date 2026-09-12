"""Terminal setup / teardown and input handling.

curses is imported lazily so that ``import emberlight`` (and the headless
``--demo`` and unittest paths) never require a terminal or the Windows curses
wheel.  Node 3 adds :func:`translate_key` so the game loop can talk to the
terminal-agnostic ``Game.press``.
"""

import sys


class TerminalUnavailableError(RuntimeError):
    """Raised when the interactive view cannot start (no curses / no TTY)."""


def _curses():
    try:
        import curses
    except ImportError as exc:  # pragma: no cover - platform dependent
        raise TerminalUnavailableError(
            "Requires curses; on Windows run: pip install windows-curses"
        ) from exc
    return curses


def curses_available() -> bool:
    """True if the interactive terminal view can be started."""
    if not sys.stdout.isatty():
        return False
    try:
        _curses()
    except TerminalUnavailableError:
        return False
    return True


def init_terminal():
    """Initialise curses and return ``(stdscr, curses)``.

    Caller must restore the terminal with :func:`shutdown_terminal`.
    """
    curses = _curses()
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    try:
        curses.curs_set(0)
    except curses.error:  # pragma: no cover - some terminals refuse
        pass
    return stdscr, curses


def shutdown_terminal(curses) -> None:
    """Restore the terminal to a sane state."""
    try:
        curses.echo()
        curses.nocbreak()
        curses.curs_set(1)
    finally:
        curses.endwin()


def translate_key(key, curses):
    """Map a raw curses key code to a semantic token for ``Game.press``.

    Returns None for key codes the game does not understand (including -1,
    the "no key pending" sentinel used with ``nodelay``).
    """
    if key == -1:
        return None
    if key == curses.KEY_UP:
        return "up"
    if key == curses.KEY_DOWN:
        return "down"
    if key == curses.KEY_LEFT:
        return "left"
    if key == curses.KEY_RIGHT:
        return "right"
    if key == 27:  # Esc
        return "esc"
    if 0 <= key < 256:
        return chr(key)
    return None
