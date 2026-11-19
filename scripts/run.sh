#!/usr/bin/env bash
# Runs the game from anywhere - resolves the repo root relative to this
# script's own location, so it works whether you double-click it or run
# it from a terminal in any directory.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
uv run python src/game.py
