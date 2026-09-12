# EMBERLIGHT — Playtest (staged for human approval)

> STATUS: **READY FOR HUMAN PLAYTEST** — staged by G (node 5), awaiting
> Rick's sign-off before the game is declared complete (the node-0 gate).

This is the playtest candidate for **EMBERLIGHT v0.3.0**, a first-person
ASCII raycast terminal dungeon-descent into the Buried City of Verrenn. It has
been verified from a clean state on both platforms:

- **Linux** — fresh clone, `pip install -e .`, 63/63 tests green, `--demo`
  and `--version` clean, and the interactive core loop exercised end-to-end
  in a real terminal (title menu -> descend -> move -> toggle minimap ->
  HUD renders -> summary -> clean quit, exit code 0).
- **Windows** — GitHub Actions CI green on `windows-latest` for Python
  3.10/3.12/3.13 (demo smoke + full test suite) on the current HEAD, and the
  `run.bat` launcher path documented and shipped in the release zip.

## What you are playtesting

The core loop. You are not looking for balance or polish — just that it
**installs cleanly, runs, and the loop is playable without crashes**:

1. Launch the game and reach the title menu.
2. Start a descent (Today's or Free).
3. Move, turn, and strafe through the dungeon.
4. Toggle the minimap (`M`); watch your ember (fuel) drain and the light cone
   shrink as it does.
5. Relight a beacon (stand next to it and hold `Space` for ~2 s).
6. Confirm the HUD renders throughout (ring, ember bar, hearts, flares,
   score, facing).
7. Quit cleanly (`Esc` aborts the run; `Q`/`Esc` quits from the menu).

## How to install and run

### Linux / macOS

```sh
git clone https://github.com/rickseeger/ai-game-01.git
cd ai-game-01
python3 -m emberlight          # that's it — no dependencies
# optional clean install:
#   python3 -m venv .venv && . .venv/bin/activate && pip install -e .
```

Full detail: [LINUX.md](LINUX.md).

### Windows

1. Download `release/emberlight-windows-v0.3.0.zip`, extract it (e.g. to
   `C:\emberlight`).
2. Install Python 3.10+ from <https://www.python.org/downloads/windows/>
   (tick "Add python.exe to PATH").
3. In the extracted folder, run `pip install windows-curses`.
4. Double-click `run.bat` (or run `run.bat` from a prompt).

Full detail: [WINDOWS.md](WINDOWS.md). Recommended console: Windows Terminal.

## Controls quick reference

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

## What to report back

For each platform you try, tell G: (1) it installed and launched, (2) the
loop ran to a clean quit, and (3) any crash, freeze, or unreadable screen
(with the terminal/console and its size, and what you were doing). Your
approval here is the gate that closes G7.
