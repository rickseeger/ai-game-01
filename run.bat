@echo off
setlocal EnableExtensions
REM EMBERLIGHT launcher (Windows).
REM Usage: run.bat [--demo | --version | ...]
cd /d "%~dp0"

REM Locate Python: try `python`, then the `py` launcher (both installed by
REM the official python.org installer when "Add to PATH" is ticked).
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py"

if not defined PY (
    echo EMBERLIGHT needs Python 3.10 or newer on PATH.
    echo Install it from https://www.python.org/downloads/windows/ and tick
    echo "Add python.exe to PATH", then run:
    echo     pip install windows-curses
    exit /b 1
)

%PY% -m emberlight %*
