# com.pickup.monitor: StartInterval fires once, then never again

## Root cause

`gui/501` is not an **active** domain, so launchd holds every timer-driven spawn.

The evidence points at nothing else:

| Observation | What it rules in / out |
|---|---|
| `launchctl kickstart` works, `runs = 1`, `last exit code = 0` | Script, PATH, env, permissions, exec bit, plist parse — all fine. The job is loadable and runnable **on demand**. |
| `interval event: domain response: 36` | launchd's timer *did* fire. The event reached the job. This is not a missed timer. |
| `pending spawn, domain in on-demand-only mode` | launchd then declined to execute the spawn, citing **domain state**, not job state. |
| `runs` stays at 1 forever (not 2, not delayed) | Not sleep/wake coalescing — a slept machine replays the event on wake and `runs` increments. Nothing is queuing up. |
| Dashboard "works" | It only ever needed **one** spawn, which `RunAtLoad` produced during `bootstrap` — itself an explicit demand. Its `KeepAlive` is equally dead; you just haven't crashed it yet. |

### What "domain in on-demand-only mode" means

launchd domains are hierarchical: `system` → `user/<uid>` → `gui/<uid>`. A domain
is either **active** (jobs run freely, timers fire, KeepAlive respawns) or
**on-demand-only** (the domain is loaded and enumerable, but launchd will only
spawn a job in response to an explicit demand — an XPC/Mach lookup, a socket
connection, `launchctl kickstart`, or the RunAtLoad that accompanies
`bootstrap`).

`gui/<uid>` is bound to the **Aqua session** — a human logged in at the physical
console. When there is no active Aqua session (never logged in since boot,
sitting at the login window, FileVault booted but not unlocked to the desktop,
or logged out with only SSH sessions), launchd keeps the domain loaded so
`launchctl list` still shows your labels, but demotes it to on-demand-only.
Timers keep firing into it and keep getting parked as "pending spawn".

**SSH does not create an Aqua session.** An SSH login gets you the background
`user/<uid>` domain (`launchctl managername` prints `Background`). Your
`install.sh` explicitly named `gui/$UID_NUM`, which is why bootstrap succeeded —
the domain object exists — but existing and being *active* are different things.

### Why StartInterval specifically dies

`StartInterval` is a demand *source*, not a guarantee. It generates an event;
executing it still requires an active domain. `kickstart` bypasses this because
it is an operator-issued demand, which on-demand-only mode explicitly permits.
That asymmetry — kickstart works, interval doesn't — is the fingerprint.

### Classification

Not a launchd bug. Not a plist bug — the plist is valid and would work fine on a
Mac with someone logged in at the desktop. It is an **architecture/domain
mismatch**: a headless, SSH-administered, 24/7 machine running its production
workload as a LaunchAgent in a session-scoped domain that has no session.

## Fix

Two independent changes, both applied:

1. **LaunchAgent → LaunchDaemon** (`/Library/LaunchDaemons`, `system` domain).
   The system domain is bootstrapped by PID 1 at boot and is never
   on-demand-only. No login, no Aqua session, no fast-user-switching state can
   affect it. `UserName`/`GroupName` keep the process running as `rushabhddh`,
   so `pickup_history.db` and the logs keep their ownership and nothing runs as
   root.

2. **StartInterval → KeepAlive + in-process scheduler** (`monitor_daemon.py`).
   Moving to a daemon alone would fix today's bug, but the cadence would still
   be a launchd implementation detail you cannot see or test. With one
   long-lived process:
   - the schedule is ordinary Python you can run in a terminal and watch;
   - the `cloudscraper` challenge cookie and TLS session stay warm across
     checks instead of being rebuilt 480×/day — fewer cold handshakes against
     Apple's endpoint, and less chance of being challenged;
   - drift is handled explicitly (monotonic clock), and intervals missed while
     the Mac slept are **skipped**, not replayed as a burst of alerts;
   - launchd's only job is `KeepAlive` — the one thing it does unconditionally
     in the system domain;
   - `ThrottleInterval 30` turns a bad `.env` into a slow retry loop instead of
     a spin;
   - the process voluntarily exits every 6h so launchd hands it a fresh
     interpreter.

### Trade-offs accepted

- A LaunchDaemon has **no TCC grants**. It cannot read `~/Desktop`,
  `~/Documents`, `~/Downloads` or iCloud Drive. `~/server/projects/apple` is
  unprotected, so this is fine — but do not move the project into one of those
  folders. `install.sh` now refuses to install if you do.
- No login keychain, no GUI, no user Mach bootstrap. This project needs none of
  it; secrets come from `.env` (now `chmod 600`, migrated out of
  `run_monitor.sh`).
- The daemon may start before the network is up at boot. `monitor.py` already
  retries with backoff, and a failed cycle no longer kills the loop.

### Still your responsibility: sleep

None of this runs while the Mac is asleep. `caffeinate -i` inside the dashboard
only helps while the dashboard is alive. For a 24/7 box set the policy at the
system level:

```
sudo pmset -a sleep 0 disksleep 0 powernap 0 womp 1 autorestart 1
```

On a laptop with the lid closed you also need external power + display
(clamshell), or macOS sleeps regardless of `pmset`.

## Migration

```bash
cd ~/server/projects/apple
./diagnose_launchd.sh          # confirm the diagnosis first (optional)
sudo ./install.sh --power      # boots out the agents, installs the daemons
tail -f monitor.log            # should tick every 180s, forever
```

Verify it is genuinely in the system domain and staying up:

```bash
sudo launchctl print system/com.pickup.monitor | grep -E 'state|pid|runs|last exit'
```

Expect `state = running`, a stable `pid`, and `runs` incrementing only when the
6-hour recycle happens — the 180s checks are now internal, so `runs` staying
low is the *correct* behaviour.

`run_monitor.sh` is left in place for manual one-shot runs (`./run_monitor.sh`);
launchd no longer calls it.
