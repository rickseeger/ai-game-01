#!/usr/bin/env python3
"""Build the EMBERLIGHT Windows release artifact (node 4).

Reproducibly zips the source tree (package, launchers, docs, tests) into a
single ``release/emberlight-windows-v<VERSION>.zip`` that a Windows user can
download, extract, and run from a clean state (see WINDOWS.md).

Usage::

    python3 tools/package_windows.py

The archive is written to ``release/`` at the repository root and contains a
single top-level ``emberlight-windows/`` folder so extraction never scatters
files into the current directory.
"""

import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import emberlight  # noqa: E402  (after sys.path setup)

VERSION = emberlight.__version__
TOP = "emberlight-windows"

# Files/folders that ship in the artifact. Everything else (.git, caches,
# CI config, this script's own build machinery) is left out.
INCLUDE_TOP = (
    "README.md",
    "WINDOWS.md",
    "DESIGN.md",
    "pyproject.toml",
    "requirements.txt",
    "run.bat",
    "run.sh",
)
INCLUDE_DIRS = (
    "emberlight",
    "tests",
)
EXCLUDE_NAMES = {"__pycache__", ".git", ".venv", ".egg-info"}


def _want(path: pathlib.Path) -> bool:
    if path.name in EXCLUDE_NAMES:
        return False
    if path.suffix in (".pyc", ".pyo"):
        return False
    if "__pycache__" in path.parts:
        return False
    return True


def build() -> pathlib.Path:
    release_dir = ROOT / "release"
    release_dir.mkdir(exist_ok=True)
    out = release_dir / f"{TOP}-v{VERSION}.zip"

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in INCLUDE_TOP:
            p = ROOT / name
            if p.is_file():
                zf.write(p, f"{TOP}/{name}")
        for d in INCLUDE_DIRS:
            base = ROOT / d
            if not base.is_dir():
                continue
            for p in sorted(base.rglob("*")):
                if p.is_file() and _want(p):
                    zf.write(p, f"{TOP}/{p.relative_to(ROOT).as_posix()}")
    return out


def main() -> int:
    out = build()
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    print(f"wrote {out}")
    print(f"  {len(names)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
