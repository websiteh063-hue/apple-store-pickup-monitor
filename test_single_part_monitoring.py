import urllib.request
import json
import urllib.parse
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PARTS = {
    "MG6J4HN/A": "Black",
    "MG6K4HN/A": "White",
    "MG6M4HN/A": "Lavender",
    "MG6N4HN/A": "Sage",
    "MG6Q4HN/A": "Mist Blue",
}
STORES = {
    "R744": "Apple BKC",
    "R757": "Apple Borivali",
    "R756": "Apple Saket",
    "R778": "Apple Hebbal",
}
COOKIE = "as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"

for sid, store_name in STORES.items():
    ready = []
    for part, colour_name in PARTS.items():
        url = f"https://www.apple.com/in/shop/buyability-message?parts.0={urllib.parse.quote(part, safe='')}&store={sid}"
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Cookie": COOKIE})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode())
                apu = data["body"]["content"]["buyabilityMessage"]["apu"]
                if apu.get(part, {}).get("isBuyable") is True:
                    ready.append(colour_name)
        except Exception as e:
            print(f"Error {sid} {part}: {e}")
    if ready:
        print(f"✅ {store_name} ({sid}): AVAILABLE -> {', '.join(ready)}")
    else:
        print(f"❌ {store_name} ({sid}): NO STOCK")
