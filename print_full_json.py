#!/usr/bin/env python3
import urllib.request
import json
import urllib.parse

PARTS = ["MG6J4HN/A"]
query = "parts.0=" + urllib.parse.quote(PARTS[0], safe='')
COOKIE = "as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"

def print_store_data(sid):
    url = f"https://www.apple.com/in/shop/buyability-message?{query}&store={sid}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cookie": COOKIE})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            print(f"=== STORE {sid} ===")
            print(json.dumps(data, indent=2)[:1000])
    except Exception as e:
        print(f"Error {sid}: {e}")

print_store_data("R744")
print_store_data("R757")
print_store_data("R756")
