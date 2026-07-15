#!/usr/bin/env python3
"""Audit Simply Supplements products for missing images."""
import json
import urllib.request
import time

BRAND_ID = "91a56477-b06f-4440-ba06-46c730784533"
API_BASE = "https://api.dev.suppevo.com"

all_products = []
cursor = None
while True:
    url = f"{API_BASE}/public/brands/{BRAND_ID}/products?limit=100"
    if cursor:
        url += f"&cursor={cursor}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    items = data.get("items", [])
    all_products.extend(items)
    cursor = data.get("next_cursor")
    if not cursor or not items:
        break
    time.sleep(0.2)

no_image = [p for p in all_products if not p.get("imageUrl")]
has_image = [p for p in all_products if p.get("imageUrl")]

print(f"Total Simply Supplements products: {len(all_products)}")
print(f"With images: {len(has_image)}")
print(f"Without images: {len(no_image)}")
print(f"Image coverage: {len(has_image)/len(all_products)*100:.1f}%")
print()
print(f"Products without images:")
for p in no_image:
    print(f"  {p['id']} | {p.get('name', '?')} | score: {p.get('completeness_score', 0)}")

# Save
with open("scripts/simply_supplements_missing_images.json", "w") as f:
    json.dump({"total": len(all_products), "missing": len(no_image), "products": [{"id": p["id"], "name": p.get("name", "")} for p in no_image]}, f, indent=2)
print(f"\nSaved to scripts/simply_supplements_missing_images.json")
