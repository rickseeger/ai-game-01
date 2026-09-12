"""Terminal setup / teardown and input handling.

curses is imported lazily so that ``import emberlight`` (and the headless
``--demo`` and unittest paths) never require a terminal or the Windows curses
wheel.  Node 3 adds :func:`translate_key` so the game loop can talk to the
terminal-agnostic ``Game.press``.
"""

import os
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


def prefer_ascii() -> bool:
    """True when the interactive view should use the pure-ASCII glyph set.

    The unicode shade ramp (block elements U+2588..U+2593) and the heart
    indicators (U+2665/U+2661) render on UTF-8 terminals and on the DOS code
    pages (cp437/cp850/cp866), but a legacy Windows console running a Western
    code page (cp1252/latin-1) cannot show them and prints replacement boxes
    instead.  Fall back to the monochrome-safe ASCII glyphs in that case so
    the game stays playable identically everywhere.

    Set ``EMBERLIGHT_ASCII=1`` to force ASCII on any terminal.
    """
    if os.environ.get("EMBERLIGHT_ASCII", "").strip().lower() in (
        "1", "true", "yes", "on",
    ):
        return True
    enc = (getattr(sys.stdout, "encoding", None) or "").lower()
    enc = enc.replace("-", "").replace("_", "")
    # Western single-byte code pages that lack the block/heart glyphs.
    western = {
        "ascii", "usascii", "latin1", "iso88591",
        "cp1252", "cp1250", "cp1251", "cp1253", "cp1254", "cp1257",
    }
    return enc in western


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
