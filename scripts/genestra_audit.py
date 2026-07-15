#!/usr/bin/env python3
"""Audit Genestra Brands products for missing/broken images."""
import json
import urllib.request
import time

BRAND_ID = "61bba5ef-9106-49f7-820a-d709e0fe534f"
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
has_nih = [p for p in all_products if p.get("imageUrl") and "ods.od.nih.gov" in p.get("imageUrl", "")]
has_other = [p for p in all_products if p.get("imageUrl") and "ods.od.nih.gov" not in p.get("imageUrl", "")]

print(f"Total Genestra Brands products: {len(all_products)}")
print(f"Without images: {len(no_image)}")
print(f"With NIH thumbnail images: {len(has_nih)}")
print(f"With other images: {len(has_other)}")
print(f"Image coverage: {(len(has_nih) + len(has_other))/len(all_products)*100:.1f}%")
print(f"\nProducts without images (first 30):")
for p in no_image[:30]:
    print(f"  {p.get('name', '?')}")

with open("scripts/genestra_missing_images.json", "w") as f:
    json.dump({
        "total": len(all_products),
        "missing": len(no_image),
        "products": [{"id": p["id"], "name": p.get("name", "")} for p in no_image]
    }, f, indent=2)
print(f"\nSaved to scripts/genestra_missing_images.json")
