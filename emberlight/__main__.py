"""Enable `python -m emberlight` to launch the game."""

import sys

from .main import main

if __name__ == "__main__":
    raise SystemExit(main())
