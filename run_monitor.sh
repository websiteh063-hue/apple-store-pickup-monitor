#!/bin/bash
# Runs one pickup check. launchd calls this every 3 minutes (StartInterval 180).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

# ===================== FILL IN YOUR VALUES =====================
export TELEGRAM_TOKEN="1446577636:AAGxIFePY_zO01wX4v75iTC-AQCyCc5hgCk"
export TELEGRAM_CHAT_ID="549489041"
# Optional — publish live data to your public GitHub site. Leave GITHUB_TOKEN
# empty ("") to disable publishing.
export GITHUB_TOKEN=""
export GITHUB_REPO="rushabhddh/temprepo"
# ==============================================================

# If a .env file exists it overrides the values above (optional).
set -a; [ -f "$DIR/.env" ] && . "$DIR/.env"; set +a
export DB_PATH="$DIR/pickup_history.db"
python3 monitor.py >> "$DIR/monitor.log" 2>&1

# Publish data.json to the public GitHub Pages site via the Contents API
# (throttled, no git). Skips itself if GITHUB_TOKEN/GITHUB_REPO aren't in .env.
# A publish failure never breaks the monitor.
python3 publish_json.py >> "$DIR/publish.log" 2>&1 || true
