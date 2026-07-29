#!/usr/bin/env python3
import cloudscraper
import json

scraper = cloudscraper.create_scraper()
COOKIE = "as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"

headers = {
    "User-Agent": UA,
    "Cookie": COOKIE,
}

def check_part(part, name, store="R744"):
    url = f"https://www.apple.com/in/shop/buyability-message?parts.0={part}&store={store}"
    try:
        r = scraper.get(url, headers=headers, timeout=10)
        data = r.json()
        b = data["body"]["content"]["buyabilityMessage"]
        sth = b.get("sth", {}).get(part, {}).get("isBuyable")
        apu = b.get("apu", {}).get(part, {}).get("isBuyable")
        print(f"Part: {part} ({name}) @ {store} -> APU (Pickup): {apu} | STH (Delivery): {sth}")
    except Exception as e:
        print(f"Error {part}: {e}")

parts = {
    "MG6J4HN/A": "iPhone 17 256GB Black",
    "MG6K4HN/A": "iPhone 17 256GB White",
    "MG6M4HN/A": "iPhone 17 256GB Lavender",
    "MG6N4HN/A": "iPhone 17 256GB Sage",
    "MG6Q4HN/A": "iPhone 17 256GB Mist Blue",
}

print("=== CHECKING APPLE BKC (R744) ===")
for p, name in parts.items():
    check_part(p, name, "R744")

print("\n=== CHECKING APPLE BORIVALI (R757) ===")
for p, name in parts.items():
    check_part(p, name, "R757")

print("\n=== CHECKING APPLE SAKET (R756) ===")
for p, name in parts.items():
    check_part(p, name, "R756")
