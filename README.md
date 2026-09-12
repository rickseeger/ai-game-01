# EMBERLIGHT

A first-person ASCII raycast dungeon descent for the terminal. Descend into
the Buried City of Verrenn, relight the dead beacons, and race your dying
lantern back to the surface before the dark takes you.

Canonical game design lives in [DESIGN.md](DESIGN.md) - read that first.
This repository is the G7 mission tree for building the game one node at a
time; the current state is the **node 2 project skeleton**.

## What is here (node 2)

- `emberlight/` - the Python package (Python 3.10+, standard library only).
- A minimal but real entry point that renders something and exits cleanly.
- The canonical constants table (`emberlight/config.py`), mirrored from
  DESIGN.md so later engine work has a single source of truth.
- A trivial, dependency-free test harness (`unittest` from the stdlib).
- Cross-platform (Linux + Windows) CI via GitHub Actions.
- Packaging metadata (`pyproject.toml`) with an `emberlight` console script.

The engine and mechanics land in node 3, implemented directly from
DESIGN.md.

## Requirements

- Python 3.10 or newer.
- Linux / macOS: standard library only - no installs required.
- Windows: install the single optional dependency (`python` does not ship
  curses on Windows):

  ```
  pip install windows-curses
  ```

## Run

```
python -m emberlight          # interactive terminal view (title screen)
python -m emberlight --demo   # render a static demo frame to stdout
python -m emberlight --version
```

Convenience launchers: `./run.sh` (Linux/macOS) or `run.bat` (Windows).

The interactive view needs a curses-capable terminal. With no terminal (CI,
pipes) it falls back to the demo render and still exits cleanly. If curses is
unavailable it prints a one-line message and exits cleanly, never crashing.

## Test

The test harness is the standard library `unittest` - zero dependencies, so
the exact same command works on Linux and Windows:

```
python -m unittest discover -s tests -v
```

## Install / build

There is no compile step (Python is interpreted). To install the package and
the `emberlight` console script into a virtualenv:

```
python -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
emberlight --demo
```

`pyproject.toml` declares the build backend (setuptools) and metadata, and
reads the version from `emberlight.__version__`.

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
  .github/workflows/   CI (Linux + Windows matrix)
  emberlight/
    __init__.py        package + __version__
    __main__.py        enables `python -m emberlight`
    main.py            entry point / mode dispatch
    config.py          constants and tables (single source of truth)
    render.py          shade ramp, title banner, demo frame
    input.py           curses terminal setup / teardown
    engine.py          (stub) DDA raycaster  -> node 3
    mapgen.py          (stub) seeded floors   -> node 3
    entities.py        (stub) game objects    -> node 3
    ai.py              (stub) monster AI      -> node 3
    records.py         (stub) local records   -> node 3
    ui.py              (stub) menus/screens   -> node 3
  tests/
    test_smoke.py      trivial smoke tests
```

## License

To be decided by the repository owner.
