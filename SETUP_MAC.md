# Run the pickup monitor 24/7 on your Mac (M2)

This runs the monitor **every 3 minutes** and keeps a **live dashboard** up at
`http://localhost:5001`, both managed by macOS `launchd` so they survive reboots
and restart if they crash. No GitHub, no cloud — the SQLite DB is local and live.

## What's in this folder

| File | Purpose |
|------|---------|
| `monitor.py` | The 3-state pickup checker (no alert cooldown — pings on every stocked run). |
| `dashboard.py` | Live web dashboard + REST API. Auto-refreshes every 15s. |
| `db.py` | SQLite history the monitor writes and the dashboard reads. |
| `run_monitor.sh` / `run_dashboard.sh` | Wrappers launchd calls (load `.env`, set paths). |
| `install.sh` / `uninstall.sh` | Set up / tear down the launchd jobs. |
| `.env.example` | Template for your Telegram secrets. |

## One-time setup

**1. Put this folder somewhere permanent**, e.g. your home folder:
`/Users/<you>/apple-pickup-monitor`. (Not Downloads — don't move it after install;
the launchd jobs point at this exact path.)

**2. Install the two Python packages** (Terminal, inside the folder):
```bash
cd ~/apple-pickup-monitor
pip3 install flask cloudscraper
```
If `pip3` complains about an "externally managed environment", use:
```bash
pip3 install --user flask cloudscraper
```

**3. Add your Telegram secrets:**
```bash
cp .env.example .env
open -e .env          # fill in TELEGRAM_TOKEN and TELEGRAM_CHAT_ID, then save
```

**4. Install and start everything:**
```bash
chmod +x install.sh uninstall.sh run_monitor.sh run_dashboard.sh
./install.sh
```
You'll see `Installed and started.` The monitor begins immediately and repeats
every 3 minutes; the dashboard is live at **http://localhost:5001**.

## Keep the Mac awake (important)

A sleeping Mac won't run checks. Two things handle this:

- The dashboard runs under `caffeinate -i`, which **prevents idle sleep** while it's
  running — so as long as the dashboard is up, the 3-min schedule keeps firing.
- **Closing the lid still sleeps the Mac** unless it's plugged in with an external
  display (clamshell mode). For 24/7, keep it **plugged in and the lid open**, or set
  **System Settings → Battery/Lock Screen** so it doesn't sleep on power. To be
  extra safe: `sudo pmset -c sleep 0 disablesleep 0`.

## Viewing the dashboard

- On the Mac: **http://localhost:5001**
- From your phone (same Wi-Fi): find the Mac's IP with
  `ipconfig getifaddr en0`, then open `http://<that-ip>:5001` on your phone.

The page shows a live green pulse ("last check 40s ago"), both stores' current
status with colour swatches, a running **live check feed** (so you can watch the
3-min cadence), plus 7-day changes and reliability. Telegram still fires the moment
stock appears.

## Everyday commands

```bash
# see the monitor's live output
tail -f ~/apple-pickup-monitor/monitor.log

# is it running?
launchctl list | grep pickup

# send yourself a test heartbeat right now
cd ~/apple-pickup-monitor && set -a; . .env; set +a; HEARTBEAT=1 python3 monitor.py

# stop everything (DB kept)
./uninstall.sh

# restart after changing a file
./uninstall.sh && ./install.sh
```

## Troubleshooting

- **Dashboard won't load** → `tail ~/apple-pickup-monitor/dashboard.log`. Usually Flask
  isn't installed (`pip3 install flask`) or port 5001 is taken (`PORT=5055 ./install.sh`
  after editing the wrapper, or just change `PORT` in `run_dashboard.sh`).
- **No Telegram messages** → check `.env` values; run the test heartbeat command above
  and read the error it prints.
- **Checks stop overnight** → the Mac slept. Revisit "Keep the Mac awake".
- **`pip3 install` blocked** → add `--break-system-packages` (Homebrew Python) or use a
  virtualenv.
