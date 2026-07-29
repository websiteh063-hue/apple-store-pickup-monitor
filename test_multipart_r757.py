#!/usr/bin/env python3
import urllib.request
import json
import urllib.parse

PARTS = ["MG6J4HN/A", "MG6K4HN/A", "MG6M4HN/A", "MG6N4HN/A", "MG6Q4HN/A"]
query = "&".join(f"parts.{i}={urllib.parse.quote(p, safe='')}" for i, p in enumerate(PARTS))
COOKIE = "as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

url = f"https://www.apple.com/in/shop/buyability-message?{query}&store=R757"
req = urllib.request.Request(url, headers={"User-Agent": UA, "Cookie": COOKIE})
data = json.loads(urllib.request.urlopen(req).read().decode())
apu = data["body"]["content"]["buyabilityMessage"]["apu"]
print("Multi-part query R757 APU:", json.dumps(apu, indent=2))
