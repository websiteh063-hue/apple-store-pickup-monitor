#!/usr/bin/env python3
import cloudscraper
import json
import urllib.parse

scraper = cloudscraper.create_scraper()
PARTS = ["MG6J4HN/A", "MG6K4HN/A", "MG6M4HN/A", "MG6N4HN/A", "MG6Q4HN/A"]
COOKIE = "as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"

headers = {
    "User-Agent": UA,
    "Cookie": COOKIE,
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.apple.com/in/shop/buy-iphone/iphone-17",
}

def test_url(url, label):
    print(f"\n--- Testing: {label} ---")
    try:
        r = scraper.get(url, headers=headers, timeout=10)
        print("Status:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            s = json.dumps(data, indent=2)
            print("Snippet:", s[:2000])
            if "pickupMessage" in s or "stores" in s or "pickupSearchQuote" in s or "Available" in s:
                print(">>> FOUND PICKUP DATA! <<<")
        else:
            print("Response:", r.text[:200])
    except Exception as e:
        print("Error:", e)

# Test 1: pl=true & mts.0=regular
test_url("https://www.apple.com/in/shop/fulfillment-messages?pl=true&mts.0=regular&parts.0=MG6J4HN%2FA&location=400051", "pl=true location=400051")

# Test 2: pl=true & mts.0=regular with store R744
test_url("https://www.apple.com/in/shop/fulfillment-messages?pl=true&mts.0=regular&parts.0=MG6J4HN%2FA&store=R744", "pl=true store=R744")

# Test 3: buyability-message vs fulfillment-messages with pl=true
test_url("https://www.apple.com/in/shop/fulfillment-messages?pl=true&parts.0=MG6J4HN%2FA&location=Mumbai", "location=Mumbai")

# Test 4: buyability-message with all parameters
q = "&".join(f"parts.{i}={urllib.parse.quote(p)}" for i, p in enumerate(PARTS))
test_url(f"https://www.apple.com/in/shop/fulfillment-messages?pl=true&mts.0=regular&{q}&location=400051", "all parts pl=true location=400051")
