#!/usr/bin/env python3
import urllib.request
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

PARTS = ["MG6J4HN/A", "MG6K4HN/A", "MG6M4HN/A", "MG6N4HN/A", "MG6Q4HN/A"]
query = "&".join(f"parts.{i}={urllib.parse.quote(p, safe='')}" for i, p in enumerate(PARTS))
COOKIE = "as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"

def check_code(num):
    sid = f"R{num}"
    url = f"https://www.apple.com/in/shop/buyability-message?{query}&store={sid}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cookie": COOKIE})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            apu = data.get("body", {}).get("content", {}).get("buyabilityMessage", {}).get("apu", {})
            if apu and any(p in apu for p in PARTS):
                return sid
    except Exception:
        pass
    return None

print("Starting Fast Scan R700-R850...")
with ThreadPoolExecutor(max_workers=25) as executor:
    results = executor.map(check_code, range(700, 850))

found_stores = [r for r in results if r]
print("FOUND STORES:", found_stores)
