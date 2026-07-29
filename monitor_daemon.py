#!/usr/bin/env python3
"""Long-lived scheduler for the pickup monitor.

WHY THIS EXISTS
---------------
launchd's StartInterval only fires while the job's domain is *active*. A
LaunchAgent lives in gui/<uid>, which drops into "on-demand-only mode" whenever
there is no active Aqua (console) session -- e.g. a headless Mac administered
over SSH. In that state launchd records the timer event and then refuses the
spawn ("pending spawn, domain in on-demand-only mode"), so StartInterval never
fires again even though `launchctl kickstart` still works.

The fix is to stop asking launchd to schedule anything. launchd now has exactly
one job: keep ONE process alive (KeepAlive) in the system domain, which is
always active. The interval lives here, in userspace, where it is observable,
testable and immune to session state.

Behaviour:
  * runs monitor.main() in-process every PICKUP_INTERVAL seconds (default 180)
  * runs publish_json.py as a subprocess afterwards (only if GITHUB_TOKEN set)
  * a failing cycle is logged and never kills the loop
  * schedule is monotonic-clock based, so it does not drift; cycles missed
    while the Mac was asleep are skipped rather than replayed in a burst
  * exits cleanly every PICKUP_MAX_UPTIME seconds (default 6h) so launchd
    restarts it with a fresh interpreter -- cheap insurance against leaks
  * handles SIGTERM promptly so `launchctl bootout` is not a 20s hang
"""
import datetime
import os
import signal
import subprocess
import sys
import time
import traceback

DIR = os.path.dirname(os.path.abspath(__file__))
INTERVAL = float(os.environ.get("PICKUP_INTERVAL", "120"))
MAX_UPTIME = float(os.environ.get("PICKUP_MAX_UPTIME", str(6 * 3600)))
PUBLISH_SCRIPT = os.path.join(DIR, "publish_json.py")
PUBLISH_LOG = os.path.join(DIR, "publish.log")

_stop = False


def _handle_signal(signum, _frame):
    global _stop
    _stop = True
    log(f"received signal {signum}; finishing current cycle and exiting")


def log(msg):
    stamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[daemon {stamp}] {msg}", flush=True)


def interruptible_sleep(deadline):
    """Sleep until monotonic `deadline`, waking often enough to see SIGTERM."""
    while not _stop:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 1.0))


def run_publish():
    if not os.environ.get("GITHUB_TOKEN"):
        return
    try:
        with open(PUBLISH_LOG, "a") as fh:
            subprocess.run(
                [sys.executable, PUBLISH_SCRIPT],
                cwd=DIR,
                stdout=fh,
                stderr=subprocess.STDOUT,
                timeout=120,
                check=False,
            )
    except subprocess.TimeoutExpired:
        log("publish_json.py timed out after 120s (ignored)")
    except Exception:
        log("publish_json.py failed (ignored):\n" + traceback.format_exc())


def main():
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    os.chdir(DIR)
    sys.path.insert(0, DIR)

    # Imported here, not at module top: monitor.py validates TELEGRAM_TOKEN /
    # TELEGRAM_CHAT_ID at import time. If they are missing we want the failure
    # in the log with context, and we want launchd's ThrottleInterval to slow
    # the restart loop rather than spin.
    import monitor

    log(
        f"started pid={os.getpid()} interval={INTERVAL:.0f}s "
        f"max_uptime={MAX_UPTIME:.0f}s python={sys.executable}"
    )

    started = time.monotonic()
    next_run = started

    while not _stop:
        now = time.monotonic()
        if now < next_run:
            interruptible_sleep(next_run)
            continue

        try:
            monitor.main()
        except Exception:
            log("monitor.main() raised (loop continues):\n" + traceback.format_exc())
        else:
            run_publish()

        # Advance to the next slot in the future. If the Mac slept through
        # several slots we skip them instead of firing back-to-back checks.
        now = time.monotonic()
        missed = 0
        while next_run <= now:
            next_run += INTERVAL
            missed += 1
        if missed > 1:
            log(f"skipped {missed - 1} interval(s) (machine likely slept)")

        if now - started >= MAX_UPTIME:
            log("max uptime reached; exiting 0 for launchd to restart cleanly")
            return 0

    log("stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
