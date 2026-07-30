#!/usr/bin/env python3
import os
import urllib.request
import urllib.parse
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TOKEN = "5954357064:AAEHIBucPDlgMthnDi7COBFDA0R_7aTsCzs"
CHAT_IDS = ["1008857254", "-1002458379798", "601135012"]

text = "⚠️ TEST ALERT: Verifying exact Telegram delivery across all 3 destinations!"

for cid in CHAT_IDS:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": cid, "text": text}).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            print(f"✅ Success for {cid}: Message ID = {res['result']['message_id']}")
    except Exception as e:
        print(f"❌ Failed for {cid}: {e}")
