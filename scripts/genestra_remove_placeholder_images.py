#!/usr/bin/env python3
"""
Find and remove Genestra products that got the NHC placeholder image
(nhc-social.png) instead of an actual product image. These are likely
discontinued products that don't have real product pages.
"""
import json
import urllib.request
import time

SUPPEVO_API_BASE = "https://api.dev.suppevo.com"
BRAND_ID = "61bba5ef-9106-49f7-820a-d709e0fe534f"

# Get all products
all_products = []
cursor = None
while True:
    url = f"{SUPPEVO_API_BASE}/public/brands/{BRAND_ID}/products?limit=100"
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

print(f"Total Genestra products: {len(all_products)}")

# Find products with the NHC placeholder image
placeholder_url = "nhc-social.png"
placeholder_products = [
    p for p in all_products
    if p.get("imageUrl") and placeholder_url in p.get("imageUrl", "")
]

print(f"Products with NHC placeholder image: {len(placeholder_products)}")
print()
for p in placeholder_products:
    print(f"  {p['id']} | {p.get('name', '?')}")

# Save IDs for deletion
ids_to_delete = [p["id"] for p in placeholder_products]
batches = [ids_to_delete[i:i+25] for i in range(0, len(ids_to_delete), 25)]

with open("scripts/genestra_placeholder_delete_batches.json", "w") as f:
    json.dump(batches, f, indent=2)

print(f"\nSaved {len(batches)} batch(es) to scripts/genestra_placeholder_delete_batches.json")
print(f"Total to delete: {len(ids_to_delete)}")
