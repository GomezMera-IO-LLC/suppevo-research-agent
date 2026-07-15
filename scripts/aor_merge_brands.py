#!/usr/bin/env python3
"""
Merge two duplicate AOR brands.
Move all products from 'Premium' (52fdab44) to 'Advanced' (8dae5cff),
then delete the Premium brand.
"""
import json
import urllib.request
import time

API_BASE = "https://api.dev.suppevo.com"
SOURCE_BRAND_ID = "52fdab44-815e-4a5a-afeb-0067e8b5934e"  # Premium (to delete)
TARGET_BRAND_ID = "8dae5cff-3d62-4cf3-89dc-338eb5e2f92c"  # Advanced (to keep)

# Get all products from source brand
all_products = []
cursor = None
while True:
    url = f"{API_BASE}/public/brands/{SOURCE_BRAND_ID}/products?limit=100"
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

print(f"Products to move from Premium to Advanced: {len(all_products)}")

# Build batch updates - just change brand_id and brand name
batches = []
for i in range(0, len(all_products), 25):
    batch = []
    for p in all_products[i:i+25]:
        batch.append({
            "id": p["id"],
            "brand_id": TARGET_BRAND_ID,
            "brand": "AOR Advanced Orthomolecular Research Advanced",
        })
    batches.append(batch)

print(f"Update batches: {len(batches)}")

with open("scripts/aor_merge_batches.json", "w") as f:
    json.dump(batches, f, indent=2)
print("Saved to scripts/aor_merge_batches.json")
