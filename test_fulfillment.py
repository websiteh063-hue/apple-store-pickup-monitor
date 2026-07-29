#!/usr/bin/env python3
import urllib.request
import json
import urllib.parse

COOKIE = "as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"

def check_fulfillment(loc):
    url = f"https://www.apple.com/in/shop/fulfillment-messages?parts.0=MG6J4HN%2FA&location={loc}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cookie": COOKIE})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            print(f"=== LOCATION {loc} ===")
            print(json.dumps(data, indent=2)[:2000])
    except Exception as e:
        print(f"Error {loc}: {e}")

check_fulfillment("560092")
check_fulfillment("560017")
check_fulfillment("R744")
check_fulfillment("R756")
