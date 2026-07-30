#!/usr/bin/env python3
import cloudscraper
import json

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

COOKIE = "as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.apple.com/in/shop/buy-iphone/iphone-17",
    "Cookie": COOKIE,
}

url = "https://www.apple.com/in/shop/fulfillment-messages?parts.0=MG6J4HN%2FA&location=400051"
print("Requesting fulfillment-messages with full headers...")
try:
    r = scraper.get(url, headers=headers, timeout=10)
    print("HTTP Status Code:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        print("Success! JSON Keys:", list(data.keys()))
        s = json.dumps(data, indent=2)
        print("JSON Output Snippet:\n", s[:1000])
    else:
        print("Response Text:", r.text[:300])
except Exception as e:
    print("Error:", e)
