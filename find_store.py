#!/usr/bin/env python3
import cloudscraper
import json

scraper = cloudscraper.create_scraper()

def search(pincode):
    url = f"https://www.apple.com/in/shop/fulfillment-messages?parts.0=MG6J4HN%2FA&location={pincode}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Cookie": "as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE"
    }
    try:
        r = scraper.get(url, headers=headers, timeout=10)
        print(f"Status for {pincode}:", r.status_code)
        print(r.text[:300])
        stores = data.get("body", {}).get("content", {}).get("pickupMessage", {}).get("stores", [])
        print(f"--- Results for pincode {pincode} ---")
        for s in stores:
            print(f"StoreName: {s.get('storeName')} | Code: {s.get('storeNumber')} | City: {s.get('city')}")
    except Exception as e:
        print(f"Error {pincode}: {e}")

search("560092")
search("560017")
search("560001")
