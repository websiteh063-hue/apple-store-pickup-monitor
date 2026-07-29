#!/usr/bin/env python3
"""Export current SQLite state to docs/data.json for the public GitHub Pages
dashboard. Run after a check; publish_to_github.sh then commits + pushes it.
"""
import datetime
import json
import os

import db

DB_PATH = os.environ.get("DB_PATH", "pickup_history.db")
OUT = os.environ.get("STATUS_JSON", "docs/data.json")

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

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w") as f:
    json.dump(payload, f, indent=2, default=str)

print(f"Wrote {OUT}: {len(payload['current'].get('stores', []))} stores, "
      f"{len(payload['changes'])} changes")
