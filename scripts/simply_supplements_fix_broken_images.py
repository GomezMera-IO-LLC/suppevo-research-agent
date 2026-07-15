#!/usr/bin/env python3
"""
Fix broken Simply Supplements image URLs.

The old media.simplysupplements.co.uk CDN is dead. All products using those
URLs need to be updated with valid Shopify CDN images.
"""
import json
import logging
import re
import time
import urllib.request
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

SUPPEVO_API_BASE = "https://api.dev.suppevo.com"
BRAND_ID = "91a56477-b06f-4440-ba06-46c730784533"

# Load Shopify cache
cache = json.load(open("scripts/simply_supplements_shopify_cache.json"))

# ============================================================================
# Get all Suppevo products with broken image URLs
# ============================================================================

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

# Find products with broken media.simplysupplements.co.uk URLs
broken = [
    p for p in all_products
    if p.get("imageUrl") and "media.simplysupplements.co.uk" in p.get("imageUrl", "")
]

log.info(f"Total products: {len(all_products)}")
log.info(f"Products with broken media.simplysupplements.co.uk URLs: {len(broken)}")

# ============================================================================
# Build Shopify lookup index
# ============================================================================


def normalize(name):
    n = name.lower().strip()
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    n = re.sub(r"\s+", " ", n)
    return n


def make_keys(name):
    keys = set()
    n = normalize(name)
    keys.add(n)
    # Remove dosage numbers
    no_nums = re.sub(r"\b\d+\b", "", n).strip()
    no_nums = re.sub(r"\s+", " ", no_nums)
    keys.add(no_nums)
    # Remove form words
    for word in ["capsules", "tablets", "softgels", "powder", "capsule", "tablet"]:
        for k in list(keys):
            keys.add(k.replace(word, "").strip())
    keys.discard("")
    return list(keys)


shopify_index = {}
for p in cache:
    title = p.get("title", "")
    images = p.get("images", [])
    if not images:
        continue
    img = images[0].get("src", "")
    if not img:
        continue
    for key in make_keys(title):
        if key not in shopify_index:
            shopify_index[key] = img

log.info(f"Shopify index: {len(shopify_index)} keys")

# ============================================================================
# Match broken products to Shopify images
# ============================================================================

fixed = []
unfixed = []

for product in broken:
    name = product.get("name", "")
    product_id = product.get("id", "")
    
    # Try matching
    image_url = None
    for key in make_keys(name):
        if key in shopify_index:
            image_url = shopify_index[key]
            break
    
    if image_url:
        fixed.append({"id": product_id, "name": name, "imageUrl": image_url})
    else:
        unfixed.append({"id": product_id, "name": name, "old_url": product.get("imageUrl", "")})

log.info(f"\nFixed: {len(fixed)}")
log.info(f"Unfixed: {len(unfixed)}")

if unfixed:
    log.info(f"\nUnfixed products:")
    for p in unfixed:
        log.info(f"  - {p['name']}")

# Save batches
if fixed:
    batches = []
    for i in range(0, len(fixed), 25):
        batches.append([{"id": p["id"], "imageUrl": p["imageUrl"]} for p in fixed[i:i+25]])
    
    with open("scripts/simply_supplements_fix_broken_batches.json", "w") as f:
        json.dump(batches, f, indent=2)
    log.info(f"\nSaved {len(batches)} batch(es) to scripts/simply_supplements_fix_broken_batches.json")

if unfixed:
    with open("scripts/simply_supplements_broken_unfixed.json", "w") as f:
        json.dump(unfixed, f, indent=2)
    log.info(f"Saved unfixed to scripts/simply_supplements_broken_unfixed.json")
