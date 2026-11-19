@echo off
REM Runs the game from anywhere - resolves the repo root relative to this
REM script's own location, so it works whether you double-click it or run
REM it from a terminal in any directory.
cd /d "%~dp0\.."
uv run python src\game.py
