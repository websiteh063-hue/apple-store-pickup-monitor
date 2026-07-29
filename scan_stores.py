#!/usr/bin/env python3
import urllib.request
import json
import urllib.parse
import time

PARTS = ["MG6J4HN/A", "MG6K4HN/A", "MG6M4HN/A", "MG6N4HN/A", "MG6Q4HN/A"]
query = "&".join(f"parts.{i}={urllib.parse.quote(p, safe='')}" for i, p in enumerate(PARTS))
COOKIE = "as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"

found = {}
print("Scanning Apple Store codes...")
for num in range(740, 785):
    sid = f"R{num}"
    url = f"https://www.apple.com/in/shop/buyability-message?{query}&store={sid}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cookie": COOKIE})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            apu = data.get("body", {}).get("content", {}).get("buyabilityMessage", {}).get("apu", {})
            if apu and any(p in apu for p in PARTS):
                print(f"FOUND STORE CODE: {sid}")
                found[sid] = apu
    except Exception:
        pass
    time.sleep(0.1)

print("Scan Complete! Found stores:", list(found.keys()))
