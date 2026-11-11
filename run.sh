#!/usr/bin/env bash
set -e

# Match-Link Unix/macOS Local Launcher
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment in .venv..."
    python3 -m venv .venv
    ./.venv/bin/pip install --upgrade pip
    ./.venv/bin/pip install -r requirements.txt
fi

echo "Starting Match-Link FastAPI server on http://localhost:8000..."
./.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
