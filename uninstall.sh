#!/bin/bash
# Stops and removes the pickup LaunchDaemons (and any leftover v1 LaunchAgents).
# Your DB, logs and .env are left untouched.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  exec sudo -- "$0" "$@"
fi

RUN_USER="${SUDO_USER:-root}"
RUN_UID="$(id -u "$RUN_USER" 2>/dev/null || echo 0)"
LA="$(eval echo ~"$RUN_USER")/Library/LaunchAgents"
LD="/Library/LaunchDaemons"

for label in com.pickup.monitor com.pickup.dashboard; do
  launchctl bootout "system/$label" 2>/dev/null || true
  rm -f "$LD/$label.plist"
  if [ "$RUN_USER" != "root" ]; then
    sudo -u "$RUN_USER" launchctl bootout "gui/$RUN_UID/$label"  2>/dev/null || true
    sudo -u "$RUN_USER" launchctl bootout "user/$RUN_UID/$label" 2>/dev/null || true
  fi
  rm -f "$LA/$label.plist"
done

# Any stray processes from a previous install.
pkill -f "monitor_daemon.py"         2>/dev/null || true
pkill -f "dashboard.py --production" 2>/dev/null || true

echo "Stopped and removed. (pickup_history.db, logs and .env kept.)"
