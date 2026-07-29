#!/bin/bash
# Runs the live dashboard continuously. launchd keeps it alive (KeepAlive).
#
# caffeinate flags: -i = no idle sleep, -s = no system sleep while on AC.
# This is belt-and-braces only. The authoritative setting is
#   sudo pmset -a sleep 0 disksleep 0
# because caffeinate cannot keep the machine awake if the dashboard itself is
# the thing that died -- and if the Mac sleeps, the monitor stops too.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
set -a; [ -f "$DIR/.env" ] && . "$DIR/.env"; set +a
export DB_PATH="$DIR/pickup_history.db"
exec caffeinate -is python3 -u dashboard.py --production >> "$DIR/dashboard.log" 2>&1
