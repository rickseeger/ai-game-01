# EMBERLIGHT on Linux

This is the official Linux install-and-run guide for EMBERLIGHT (the node 5
verification pass of the node 3 engine and node 4 Windows port). It takes you
from a clean Linux machine to a running game in a few steps.

On Linux and macOS EMBERLIGHT is **pure standard library** — there is nothing
to install to play. The instructions below use a virtual environment so a
clean checkout runs reproducibly with zero system-wide changes, but you can
skip straight to *Run* if you prefer.

## 1. Requirements

- Python 3.10 or newer. Check with `python3 --version`.
- Any curses-capable terminal: GNOME Terminal, Konsole, xterm, iTerm2 (macOS),
  tmux, or a plain TTY. This is every default terminal on Linux/macOS.
- A terminal of 80 columns x 24 rows or larger for the best view.

## 2. Get the game

Clone the repository:

```sh
git clone https://github.com/rickseeger/ai-game-01.git
cd ai-game-01
```

(Or download the repository zip from GitHub and extract it.)

## 3. Install (optional but recommended)

EMBERLIGHT has no third-party dependencies on Linux. To install it into an
isolated virtual environment (so nothing touches your system Python):

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

This installs an `emberlight` console command. Verify the install:

```sh
emberlight --version    # prints "emberlight 0.3.0"
```

## 4. Run

Start the interactive game:

```sh
python3 -m emberlight    # from the repo root; no install required
emberlight              # or, after `pip install -e .`
```

Convenience launcher (no install required):

```sh
./run.sh
```

Diagnostics / smoke runs (no terminal needed):

```sh
python3 -m emberlight --demo      # render a static seeded frame to stdout
python3 -m emberlight --version   # print the version and exit
```

## 5. Controls

| Key(s)     | Action                                   |
|------------|------------------------------------------|
| W / Up     | Step forward                             |
| S / Down   | Step backward                            |
| A / Left   | Turn left 90 degrees                     |
| D / Right  | Turn right 90 degrees                    |
| Q / E      | Strafe left / right                      |
| Shift + W  | Sprint forward (costs extra fuel)        |
| Space      | Interact (relight beacon / use stairs)   |
| F          | Flare (repels and stuns nearby monsters) |
| M          | Toggle the minimap                       |
| Esc        | Abort the run (returns to the menu)      |

On the title menu: `1`/`T` Today's Descent (the shared daily seed),
`2`/`F` Free Descent (a fresh random seed), `3`/`R` Records, `Q`/`Esc` Quit.

## 6. Run the tests

```sh
python3 -m unittest discover -s tests -v
```

The suite is the standard-library `unittest` (63 tests, zero dependencies) and
covers generation determinism and connectivity, the raycaster and light cone,
the full headless game loop (movement, fuel, relight, flare, monster AI,
ascent, scoring, records), and the Windows ASCII-fallback detection.

## 7. Troubleshooting

**"Requires curses; ...".** Rare on Linux. Confirm `TERM` is set
(`export TERM=xterm-256color`) and that you are in a real terminal, not a
pipe. With no terminal the game falls back to the demo render and still exits
cleanly.

**Terminal too small.** The game needs roughly 80x24; a larger terminal gives
a wider view. The view clamps rather than crashing.

**Glyphs look odd.** On a UTF-8 terminal the game uses unicode block-shade
walls and heart indicators. To force the monochrome-safe ASCII glyph set
(identical gameplay), set `EMBERLIGHT_ASCII=1` before launching:

```sh
export EMBERLIGHT_ASCII=1
./run.sh
```

## 8. Verify from a clean state

All of the following must succeed from a fresh checkout:

```sh
python3 -m emberlight --version          # prints "emberlight 0.3.0"
python3 -m emberlight --demo             # prints a rendered frame, exits 0
python3 -m unittest discover -s tests    # 63 tests pass
./run.sh                                 # opens the interactive game
```

Continuous integration (`.github/workflows/ci.yml`) runs the `--demo` smoke
run and the full test suite on `ubuntu-latest` for Python 3.10, 3.12 and 3.13
on every push, so the Linux port is verified green on every commit.
