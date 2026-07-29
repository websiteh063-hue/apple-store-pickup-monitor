#!/usr/bin/env python3
import urllib.request
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

PARTS = ["MG6J4HN/A"]
query = "parts.0=" + urllib.parse.quote(PARTS[0], safe='')
COOKIE = "as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"

def check_store_info(sid):
    url = f"https://www.apple.com/in/shop/buyability-message?{query}&store={sid}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cookie": COOKIE})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            b = data.get("body", {}).get("content", {}).get("buyabilityMessage", {})
            name = b.get("storeName") or b.get("store", {}).get("storeName")
            city = b.get("storeCity") or b.get("city")
            if name or city:
                return (sid, name, city)
            # Print keys if any
            return (sid, list(b.keys()), None)
    except Exception:
        pass
    return None

print("Inspecting store details...")
for num in range(740, 770):
    sid = f"R{num}"
    res = check_store_info(sid)
    if res:
        print(f"Code: {res[0]} -> {res[1]} ({res[2]})")
