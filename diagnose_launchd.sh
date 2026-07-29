#!/bin/bash
# Confirms (or refutes) the on-demand-only diagnosis. Run over SSH, no sudo
# needed for the first half. Read the ANSWER lines at the bottom.
UID_NUM="$(id -u)"

echo "=== 1. Is there an active console (Aqua) session? ==========================="
echo "console owner : $(stat -f%Su /dev/console)"
echo "who -a        :"; who
echo "managername   : $(launchctl managername 2>/dev/null)"   # Aqua vs Background
echo "  -> over SSH this prints 'Background'. What matters is whether a HUMAN"
echo "     is logged in at the physical console (console owner = your user)."
echo

echo "=== 2. Domain state ========================================================"
launchctl print "gui/$UID_NUM"  2>/dev/null | sed -n '1,25p'
echo "--- system domain (should always be running) ---"
sudo launchctl print system 2>/dev/null | sed -n '1,12p'
echo

echo "=== 3. The jobs ============================================================"
for label in com.pickup.monitor com.pickup.dashboard; do
  echo "--- $label ---"
  if sudo launchctl print "system/$label" >/dev/null 2>&1; then
    echo "domain: system (LaunchDaemon)  <-- correct for a headless 24/7 Mac"
    sudo launchctl print "system/$label" | grep -E "^\s*(state|pid|runs|last exit|program) " || true
  elif launchctl print "gui/$UID_NUM/$label" >/dev/null 2>&1; then
    echo "domain: gui/$UID_NUM (LaunchAgent)  <-- subject to on-demand-only mode"
    launchctl print "gui/$UID_NUM/$label" | grep -E "^\s*(state|pid|runs|last exit|program) " || true
  else
    echo "not loaded in any domain"
  fi
  echo
done

echo "=== 4. launchd's own log for the last hour ================================="
log show --last 1h --predicate \
  'process == "launchd" AND eventMessage CONTAINS "com.pickup"' \
  --style compact 2>/dev/null | tail -40
echo

echo "=== 5. Sleep/wake in the last 6h (a sleeping Mac runs nothing) ============="
pmset -g log | grep -Ei "Sleep +|Wake +" | tail -10
pmset -g custom | sed -n '1,20p'
echo

echo "=== ANSWER ================================================================="
echo "If section 4 shows 'domain in on-demand-only mode' and section 3 shows the"
echo "job in gui/$UID_NUM, the diagnosis is confirmed: the agent's domain is not"
echo "active, so launchd accepts the interval event and then declines the spawn."
echo "Fix: sudo ./install.sh  (moves both jobs to the system domain)."
