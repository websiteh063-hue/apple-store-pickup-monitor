#!/bin/bash
# Long-running monitor process. launchd (system domain, KeepAlive) starts this
# once at boot and restarts it if it ever dies. The 3-minute schedule lives
# inside monitor_daemon.py, NOT in launchd.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

# Secrets live in .env (chmod 600). install.sh migrates them out of
# run_monitor.sh on first run.
set -a
[ -f "$DIR/.env" ] && . "$DIR/.env"
set +a

if [ -z "${TELEGRAM_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
  echo "FATAL: TELEGRAM_TOKEN / TELEGRAM_CHAT_ID not set. Create $DIR/.env" >&2
  exit 78   # EX_CONFIG
fi

export DB_PATH="$DIR/pickup_history.db"
export PICKUP_INTERVAL="${PICKUP_INTERVAL:-180}"

# -u so each line lands in monitor.log immediately (no buffering).
# stdout/stderr go to monitor.log so the file you already watch keeps updating;
# launchd-monitor.log then only ever contains pre-exec/startup failures.
exec python3 -u "$DIR/monitor_daemon.py" >> "$DIR/monitor.log" 2>&1
