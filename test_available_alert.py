#!/usr/bin/env python3
"""Test sending a simulated 'AVAILABLE' stock alert to Telegram."""
import os
import sys
import urllib.parse
import urllib.request
import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Load .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
BUY_URL = "https://www.apple.com/in/shop/buy-iphone/iphone-17"

ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
now = datetime.datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST")

# Simulated available items across all 3 stores
available_sample = [
    "Lavender @ Apple BKC",
    "Sage @ Apple Saket",
    "Mist Blue @ Apple Borivali"
]

alert_text = (
    "🎉 iPhone 17 256GB pickup AVAILABLE now: "
    + "; ".join(available_sample)
    + f".\nReserve/buy: {BUY_URL} → choose 'Pick up' and pick the store.\n"
    + f"(checked {now})"
)

print("--- Simulated Alert Payload ---")
print(alert_text)
print("-------------------------------")

tokens = [
    ("Bot 1 (@rushabhddhbot)", "1446577636:AAGxIFePY_zO01wX4v75iTC-AQCyCc5hgCk"),
    ("Bot 2 (@Fortune_feedbackbot)", os.environ.get("TELEGRAM_TOKEN", ""))
]

for label, token in tokens:
    if not token or not CHAT_ID:
        continue
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": alert_text}).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=30) as r:
            res = r.read().decode()
            print(f"[{label}] Telegram API Response: {res[:120]}")
    except Exception as e:
        print(f"[{label}] Send Error: {e}")

