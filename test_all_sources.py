#!/usr/bin/env python3
import cloudscraper
import json
import urllib.parse
import urllib.request

scraper = cloudscraper.create_scraper()
PARTS = ["MG6J4HN/A", "MG6K4HN/A", "MG6M4HN/A", "MG6N4HN/A", "MG6Q4HN/A"]
COOKIE = "as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE"
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"

headers = {
    "User-Agent": UA,
    "Cookie": COOKIE,
    "Accept": "*/*",
    "Referer": "https://www.apple.com/in/shop/buy-iphone/iphone-17",
}

def test_endpoint(url, label):
    print(f"\n==========================================")
    print(f"Testing: {label}")
    print(f"URL: {url}")
    print(f"==========================================")
    try:
        r = scraper.get(url, headers=headers, timeout=10)
        print("HTTP Status Code:", r.status_code)
        if r.status_code == 200:
            try:
                data = r.json()
                s = json.dumps(data, indent=2)
                print("JSON Snippet (first 1000 chars):")
                print(s[:1000])
                if "stores" in s or "pickupMessage" in s or "apu" in s or "buyabilityMessage" in s:
                    print(">>> VALID DATA FOUND IN RESPONSE <<<")
            except Exception:
                print("Text snippet:", r.text[:300])
        else:
            print("Response:", r.text[:200])
    except Exception as e:
        print("Request Error:", e)

# 1. buyability-message per store (Current method)
test_endpoint("https://www.apple.com/in/shop/buyability-message?parts.0=MG6J4HN%2FA&store=R744", "1. buyability-message (Store R744 BKC)")

# 2. fulfillment-messages with store
test_endpoint("https://www.apple.com/in/shop/fulfillment-messages?parts.0=MG6J4HN%2FA&store=R744", "2. fulfillment-messages (Store R744)")

# 3. fulfillment-messages with location pincode 400051 (Mumbai)
test_endpoint("https://www.apple.com/in/shop/fulfillment-messages?parts.0=MG6J4HN%2FA&location=400051", "3. fulfillment-messages (Pincode 400051)")

# 4. fulfillment-messages with pl=true
test_endpoint("https://www.apple.com/in/shop/fulfillment-messages?pl=true&parts.0=MG6J4HN%2FA&location=400051", "4. fulfillment-messages (pl=true Pincode 400051)")

# 5. tile/fulfillment-messages
test_endpoint("https://www.apple.com/in/shop/tile/fulfillment-messages?parts.0=MG6J4HN%2FA&store=R744", "5. tile/fulfillment-messages (Store R744)")

# 6. bag/buyability-message
test_endpoint("https://www.apple.com/in/shop/bag/buyability-message?parts.0=MG6J4HN%2FA&store=R744", "6. bag/buyability-message")
