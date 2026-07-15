#!/usr/bin/env python3
"""Check if the DSLD API is working with alternative endpoints."""
import json
import urllib.request
import re
import time

API_BASE = "https://api.dev.suppevo.com"
BRAND_ID = "61bba5ef-9106-49f7-820a-d709e0fe534f"

# Get all products
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

# Check NIH images pattern
with_images = [p for p in all_products if p.get("imageUrl") and "ods.od.nih.gov" in p.get("imageUrl", "")]
no_image = [p for p in all_products if not p.get("imageUrl")]

print(f"Products with NIH images: {len(with_images)}")
print(f"Products without images: {len(no_image)}")

# Extract DSLD IDs from existing image URLs
dsld_ids = []
for p in with_images:
    match = re.search(r"/thumbnails/(\d+)\.jpg", p.get("imageUrl", ""))
    if match:
        dsld_ids.append(int(match.group(1)))

if dsld_ids:
    print(f"\nDSLD ID range: {min(dsld_ids)} - {max(dsld_ids)}")
    print(f"Sample DSLD IDs: {sorted(dsld_ids)[:10]}")

# Try DSLD label endpoint directly for a known ID
print("\nTesting DSLD API with known ID 265517...")
try:
    req = urllib.request.Request("https://api.ods.od.nih.gov/dsld/v9/label/265517")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"  Success! Product: {data.get('Product_Name', 'N/A')}")
        print(f"  UPC: {data.get('UPC', 'N/A')}")
        print(f"  Brand: {data.get('Brand_Name', 'N/A')}")
except Exception as e:
    print(f"  Error: {e}")

# Try browsing
print("\nTesting DSLD browse endpoint...")
try:
    req = urllib.request.Request("https://api.ods.od.nih.gov/dsld/v9/browse-products?brandName=Genestra+Brands&size=5")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        results = data.get("list", [])
        print(f"  Got {len(results)} results")
        for r in results[:3]:
            print(f"    {r.get('dsld_id')} | {r.get('product_name', 'N/A')} | UPC: {r.get('upc', 'N/A')}")
except Exception as e:
    print(f"  Error: {e}")
