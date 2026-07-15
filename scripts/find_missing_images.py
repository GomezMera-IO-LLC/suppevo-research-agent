#!/usr/bin/env python3
"""Find all BulkSupplements products without images or with invalid image URLs."""
import json
import urllib.request
import urllib.error
import time

BRAND_ID = "4089dd6f-2a5c-4765-8e11-8e00af34063e"
API_BASE = "https://api.dev.suppevo.com"


def api_get(path, params=None):
    url = f"{API_BASE}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items() if v)
        if query:
            url += "?" + query
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_image_url(url):
    """Check if an image URL is accessible (returns HTTP 200)."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


# Get all products
all_products = []
cursor = None
page = 0
while True:
    params = {"limit": "100"}
    if cursor:
        params["cursor"] = cursor
    data = api_get(f"/public/brands/{BRAND_ID}/products", params)
    items = data.get("items", [])
    all_products.extend(items)
    page += 1
    cursor = data.get("next_cursor")
    if not cursor or not items:
        break
    time.sleep(0.2)

print(f"Total BulkSupplements products: {len(all_products)}")

# Find products without images
no_image = [p for p in all_products if not p.get("imageUrl")]
has_image = [p for p in all_products if p.get("imageUrl")]

print(f"Products WITHOUT images: {len(no_image)}")
print(f"Products WITH images: {len(has_image)}")

# Check for invalid image URLs (sample first 20 to avoid rate limits)
print(f"\nChecking image validity for {min(len(has_image), 20)} products...")
invalid_images = []
for i, p in enumerate(has_image[:20]):
    url = p["imageUrl"]
    if not check_image_url(url):
        invalid_images.append(p)
        print(f"  INVALID: {p['name']} -> {url[:80]}...")
    time.sleep(0.3)

if invalid_images:
    print(f"\nFound {len(invalid_images)} products with INVALID image URLs")
else:
    print("  All sampled image URLs are valid ✅")

# Print products without images
print(f"\n{'='*80}")
print(f"PRODUCTS WITHOUT IMAGES ({len(no_image)})")
print(f"{'='*80}")
print(f"{'ID':<40} | Name")
print("-" * 80)
for p in sorted(no_image, key=lambda x: x.get("name", "")):
    print(f"{p['id']} | {p.get('name', 'Unknown')}")

# Save to file
output = {
    "total_products": len(all_products),
    "missing_images": len(no_image),
    "products_without_images": [
        {"id": p["id"], "name": p.get("name", "")}
        for p in sorted(no_image, key=lambda x: x.get("name", ""))
    ],
}
with open("scripts/bulksupplements_missing_images.json", "w") as f:
    json.dump(output, f, indent=2)
print(f"\nSaved to scripts/bulksupplements_missing_images.json")
