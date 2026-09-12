# EMBERLIGHT on Windows

This is the official Windows install-and-run guide for EMBERLIGHT (the
node 4 Windows port). It takes you from a clean Windows machine to a running
game in a few steps. EMBERLIGHT is pure Python and needs no compilation; on
Windows there is exactly one optional dependency (`windows-curses`) because
Windows does not ship the `curses` module with Python.

## 1. Requirements

- Windows 10 or Windows 11.
- Python 3.10 or newer, from <https://www.python.org/downloads/windows/>.
  During install, tick **"Add python.exe to PATH"**.

## 2. Get the game

Either download and extract the release artifact:

1. Download `emberlight-windows-v0.3.0.zip` (see `release/`).
2. Right-click it and choose **"Extract All..."**, into a folder such as
   `C:\emberlight`.

Or clone the repository:

```
git clone https://github.com/rickseeger/ai-game-01.git
cd ai-game-01
```

## 3. Install the one Windows dependency

Open PowerShell or Command Prompt in the game folder (the folder that
contains `run.bat`), then run:

```
pip install windows-curses
```

If `pip` is not recognised, use `python -m pip install windows-curses` or
`py -m pip install windows-curses`.

## 4. Run

Double-click `run.bat`, or run it from a prompt in the game folder:

```
run.bat
```

`run.bat` locates Python for you (trying `python` first, then the `py`
launcher) and starts the interactive game. Useful variants:

```
run.bat --version                          # print the version and exit
run.bat --demo                             # print a static frame, no terminal needed
python -m unittest discover -s tests       # run the full test suite
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

Run in **Windows Terminal** (recommended) or any UTF-8 capable console. An
80x24 terminal or larger gives the best view.

## 6. Troubleshooting

**`run.bat` says Python is not on PATH.** Install Python from
<https://www.python.org/downloads/windows/> and tick "Add python.exe to
PATH", or run the game explicitly with `py -m emberlight`.

**"Requires curses; on Windows run: pip install windows-curses".** The one
dependency is missing. Run `pip install windows-curses` (step 3).

**Characters look like boxes or question marks (legacy console).** The game
uses unicode block-shade and heart glyphs. On a legacy Windows console on a
Western code page (e.g. cp1252) these can degrade. Two options:

- Run in Windows Terminal (recommended).
- Force the pure-ASCII glyph set (identical gameplay, ASCII shading) by
  setting the environment variable, then restarting:

  ```
  set EMBERLIGHT_ASCII=1
  run.bat
  ```

The game also does this automatically when it detects a code page that cannot
render the glyphs.

## 7. Verify the install

From a clean state, all of the following must succeed:

```
python -m emberlight --version          # prints "emberlight 0.3.0"
python -m emberlight --demo             # prints a rendered frame, exits 0
python -m unittest discover -s tests    # full suite passes
run.bat                                 # opens the interactive game
```

Continuous integration (`.github/workflows/ci.yml`) runs the `--demo`
smoke-run and the full test suite on `windows-latest` for Python 3.10, 3.12
and 3.13 on every push, so the Windows port is verified green on every
commit.
