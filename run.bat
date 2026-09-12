@echo off
REM EMBERLIGHT launcher (Windows).
REM Usage: run.bat [--demo | --version | ...]
cd /d "%~dp0"
python -m emberlight %*
