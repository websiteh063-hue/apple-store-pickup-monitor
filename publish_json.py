#!/usr/bin/env python3
"""Publish data.json to GitHub via the Contents API — no git, no clone, no push.

One HTTPS request updates docs/data.json in your repo, which refreshes the public
GitHub Pages dashboard. Throttled so we don't exceed Pages' ~10-builds/hour limit.

Add to your .env:
  GITHUB_TOKEN=github_pat_...        # a token with Contents: read & write on the repo
  GITHUB_REPO=rushabhddh/temprepo    # owner/repo

Optional .env overrides:
  GITHUB_BRANCH=main
  GITHUB_JSON_PATH=docs/data.json
  PUBLISH_MIN_SECONDS=420            # min seconds between publishes (default 7 min)

If GITHUB_TOKEN / GITHUB_REPO are absent, this exits quietly (monitor still runs).
"""
import base64
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

import db

TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPO")               # "owner/repo"
PATH = os.environ.get("GITHUB_JSON_PATH", "docs/data.json")
BRANCH = os.environ.get("GITHUB_BRANCH", "main")
DB_PATH = os.environ.get("DB_PATH", "pickup_history.db")
MIN_INTERVAL = int(os.environ.get("PUBLISH_MIN_SECONDS", "420"))
STAMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_publish")

if not TOKEN or not REPO:
    print("[publish] GITHUB_TOKEN / GITHUB_REPO not set — skipping publish")
    sys.exit(0)

# --- throttle: don't publish more often than MIN_INTERVAL ---
now = time.time()
if os.path.exists(STAMP):
    try:
        if now - float(open(STAMP).read().strip()) < MIN_INTERVAL:
            print(f"[publish] throttled (< {MIN_INTERVAL}s since last)")
            sys.exit(0)
    except Exception:
        pass

# --- build the JSON payload straight from the DB (no local file needed) ---
db.init_db(DB_PATH)
payload = {
    "generated_at_utc": datetime.datetime.now(datetime.timezone.utc)
    .strftime("%Y-%m-%d %H:%M:%SZ"),
    "telegram_bot_url": "https://t.me/Fortune_feedbackbot",
    "telegram_bot_username": "Fortune_feedbackbot",
    "current": db.current_status(DB_PATH),
    "changes": db.changes(days=7, db_path=DB_PATH),
    "stats": db.stats(days=7, db_path=DB_PATH),
}
content = json.dumps(payload, indent=2, default=str)

API = f"https://api.github.com/repos/{REPO}/contents/{PATH}"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "pickup-monitor",
}


def _request(url, method="GET", data=None):
    req = urllib.request.Request(
        url, method=method, headers=HEADERS,
        data=json.dumps(data).encode() if data else None,
    )
    return urllib.request.urlopen(req, timeout=30)


# --- get the current file SHA (required to update an existing file) ---
sha = None
try:
    with _request(f"{API}?ref={BRANCH}") as resp:
        sha = json.load(resp).get("sha")
except urllib.error.HTTPError as e:
    if e.code != 404:
        print(f"[publish] could not read current file: {e.code} {e.read()[:200].decode()}")
        sys.exit(1)
    # 404 => file doesn't exist yet; we'll create it.

# --- PUT the new content ---
body = {
    "message": f"live data {payload['generated_at_utc']}",
    "content": base64.b64encode(content.encode()).decode(),
    "branch": BRANCH,
}
if sha:
    body["sha"] = sha

try:
    with _request(API, "PUT", body) as resp:
        json.load(resp)
    open(STAMP, "w").write(str(now))
    print(f"[publish] updated {PATH} on {REPO}@{BRANCH}")
except urllib.error.HTTPError as e:
    print(f"[publish] publish failed: {e.code} {e.read()[:300].decode()}")
    sys.exit(1)
