#!/bin/bash
# One-shot installer for the pickup monitor + dashboard.
#
# WHAT CHANGED AND WHY
# --------------------
# v1 installed two LaunchAgents into gui/$UID. On a headless Mac driven over
# SSH there is often no active Aqua session, so launchd puts gui/$UID into
# "on-demand-only mode": explicit demands (launchctl kickstart, bootstrap's
# RunAtLoad) still spawn, but timer events do not. That is exactly the
# "pending spawn, domain in on-demand-only mode" line in the launchd log, and
# it is why StartInterval fired zero times after the initial run.
#
# v2 installs LaunchDAEMONS into the system domain, which is always active and
# needs no login at all, and moves the 3-minute cadence out of launchd into
# monitor_daemon.py. launchd's only remaining responsibility is KeepAlive.
#
# Usage:   sudo ./install.sh            # install
#          sudo ./install.sh --power    # also apply 24/7 power settings
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
APPLY_POWER=0
[ "${1:-}" = "--power" ] && APPLY_POWER=1

# --- must be root to write /Library/LaunchDaemons -----------------------------
if [ "$(id -u)" -ne 0 ]; then
  echo "Re-running with sudo (LaunchDaemons live in /Library/LaunchDaemons)..."
  exec sudo -- "$0" "$@"
fi

RUN_USER="${SUDO_USER:-root}"
if [ "$RUN_USER" = "root" ]; then
  echo "ERROR: run this as your normal user via sudo, not as root directly." >&2
  exit 1
fi
RUN_GROUP="$(id -gn "$RUN_USER")"
RUN_UID="$(id -u "$RUN_USER")"

# --- refuse TCC-protected locations -------------------------------------------
# A LaunchDaemon has no TCC grants. If the project sat in ~/Desktop, ~/Documents,
# ~/Downloads or iCloud Drive, every file read would fail with EPERM and the
# failure would look like a random crash loop. Catch it here instead.
case "$DIR" in
  */Desktop/*|*/Documents/*|*/Downloads/*|*/Library/Mobile\ Documents/*)
    echo "ERROR: $DIR is inside a TCC-protected folder." >&2
    echo "       A LaunchDaemon cannot read it. Move the project to e.g." >&2
    echo "       ~/server/projects/apple and re-run." >&2
    exit 1 ;;
esac

# --- secrets: migrate out of run_monitor.sh into .env (chmod 600) --------------
if [ ! -f "$DIR/.env" ]; then
  if grep -qE '^export TELEGRAM_TOKEN=' "$DIR/run_monitor.sh" 2>/dev/null; then
    echo "Creating $DIR/.env from the values currently in run_monitor.sh"
    grep -E '^export (TELEGRAM_TOKEN|TELEGRAM_CHAT_ID|GITHUB_TOKEN|GITHUB_REPO)=' \
      "$DIR/run_monitor.sh" | sed 's/^export //' > "$DIR/.env"
  else
    echo "ERROR: no $DIR/.env and no tokens in run_monitor.sh." >&2
    echo "       cp .env.example .env  and fill it in." >&2
    exit 1
  fi
fi
chown "$RUN_USER:$RUN_GROUP" "$DIR/.env"
chmod 600 "$DIR/.env"

# shellcheck disable=SC1091
set -a; . "$DIR/.env"; set +a
if [ -z "${TELEGRAM_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
  echo "ERROR: TELEGRAM_TOKEN / TELEGRAM_CHAT_ID are empty in $DIR/.env" >&2
  exit 1
fi

chmod +x "$DIR/run_monitor_daemon.sh" "$DIR/run_dashboard.sh"
[ -f "$DIR/run_monitor.sh" ] && chmod +x "$DIR/run_monitor.sh"

# --- 1. tear down the old LaunchAgents ----------------------------------------
LA="$(eval echo ~"$RUN_USER")/Library/LaunchAgents"
for label in com.pickup.monitor com.pickup.dashboard; do
  sudo -u "$RUN_USER" launchctl bootout "gui/$RUN_UID/$label"  2>/dev/null || true
  sudo -u "$RUN_USER" launchctl bootout "user/$RUN_UID/$label" 2>/dev/null || true
  rm -f "$LA/$label.plist"
done

# --- 2. write the LaunchDaemons -----------------------------------------------
LD="/Library/LaunchDaemons"

cat > "$LD/com.pickup.monitor.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.pickup.monitor</string>
  <key>ProgramArguments</key><array><string>$DIR/run_monitor_daemon.sh</string></array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <key>UserName</key><string>$RUN_USER</string>
  <key>GroupName</key><string>$RUN_GROUP</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>ExitTimeOut</key><integer>20</integer>
  <key>ProcessType</key><string>Standard</string>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>PICKUP_INTERVAL</key><string>180</string>
  </dict>
  <key>StandardOutPath</key><string>$DIR/launchd-monitor.log</string>
  <key>StandardErrorPath</key><string>$DIR/launchd-monitor.log</string>
</dict></plist>
PLIST

cat > "$LD/com.pickup.dashboard.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.pickup.dashboard</string>
  <key>ProgramArguments</key><array><string>$DIR/run_dashboard.sh</string></array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <key>UserName</key><string>$RUN_USER</string>
  <key>GroupName</key><string>$RUN_GROUP</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>ExitTimeOut</key><integer>20</integer>
  <key>ProcessType</key><string>Standard</string>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
  <key>StandardOutPath</key><string>$DIR/launchd-dashboard.log</string>
  <key>StandardErrorPath</key><string>$DIR/launchd-dashboard.log</string>
</dict></plist>
PLIST

# launchd refuses to load daemons that are group/world-writable.
chown root:wheel "$LD/com.pickup.monitor.plist" "$LD/com.pickup.dashboard.plist"
chmod 644        "$LD/com.pickup.monitor.plist" "$LD/com.pickup.dashboard.plist"
plutil -lint "$LD/com.pickup.monitor.plist" "$LD/com.pickup.dashboard.plist" >/dev/null

# logs/db must stay writable by the run user
touch "$DIR/monitor.log" "$DIR/publish.log" "$DIR/dashboard.log" \
      "$DIR/launchd-monitor.log" "$DIR/launchd-dashboard.log"
chown "$RUN_USER:$RUN_GROUP" "$DIR"/*.log
[ -f "$DIR/pickup_history.db" ] && chown "$RUN_USER:$RUN_GROUP" "$DIR/pickup_history.db"

# --- 3. bootstrap into the system domain --------------------------------------
for label in com.pickup.monitor com.pickup.dashboard; do
  launchctl bootout "system/$label" 2>/dev/null || true
  launchctl bootstrap system "$LD/$label.plist"
  launchctl enable  "system/$label"
done

# --- 4. optional: 24/7 power policy -------------------------------------------
if [ "$APPLY_POWER" -eq 1 ]; then
  pmset -a sleep 0 disksleep 0 powernap 0 womp 1 autorestart 1
  pmset -a displaysleep 10
  echo "Applied 24/7 power settings (system sleep disabled)."
else
  echo
  echo "NOTE: a sleeping Mac runs nothing. For 24/7 operation run:"
  echo "  sudo pmset -a sleep 0 disksleep 0 powernap 0 womp 1 autorestart 1"
  echo "  (on a laptop with the lid shut you also need an external display or"
  echo "   clamshell power, otherwise macOS sleeps regardless.)"
fi

echo
echo "Installed as LaunchDaemons (system domain — no login required)."
echo "  Dashboard : http://localhost:5001"
echo "  Monitor   : every ${PICKUP_INTERVAL:-180}s, scheduled in-process"
echo "  Logs      : $DIR/monitor.log   $DIR/launchd-monitor.log"
echo
echo "Verify:"
echo "  sudo launchctl print system/com.pickup.monitor | grep -E 'state|runs|pid'"
echo "  tail -f $DIR/monitor.log"
echo "  sudo $DIR/uninstall.sh   # to remove"
