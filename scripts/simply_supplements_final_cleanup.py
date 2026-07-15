#!/usr/bin/env python3
"""
Final cleanup for Simply Supplements: find all products still without valid images,
attempt to fix them, and flag non-product entries for deletion.
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
SHOPIFY_BASE = "https://www.simplysupplements.co.uk"

# ============================================================================
# Get all products
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

log.info(f"Total products: {len(all_products)}")

# Find products without images OR with broken media.simplysupplements.co.uk URLs
no_image = []
for p in all_products:
    img = p.get("imageUrl") or ""
    if not img or "media.simplysupplements.co.uk" in img:
        no_image.append(p)

log.info(f"Products without valid images: {len(no_image)}")

# ============================================================================
# Identify non-product entries (category pages, navigation items)
# These should be deleted, not fixed.
# ============================================================================

NON_PRODUCT_KEYWORDS = [
    "new products", "the marketplace", "vitamins and minerals",
    "nutritional shakes", "vegetarian supplements", "probiotics",
    "find the best", "perfect partners", "weight management",
    "thyroid function supplements",
]

to_delete = []
to_fix = []

for p in no_image:
    name = p.get("name", "").lower()
    is_non_product = any(kw in name for kw in NON_PRODUCT_KEYWORDS)
    # Also flag if no ingredients AND very low completeness AND generic name
    if is_non_product:
        to_delete.append(p)
    else:
        to_fix.append(p)

log.info(f"Non-product entries to delete: {len(to_delete)}")
log.info(f"Products to attempt fixing: {len(to_fix)}")

for p in to_delete:
    log.info(f"  DELETE: {p.get('name', '?')} ({p['id']})")

# ============================================================================
# Try to fix remaining products via Shopify handle lookup
# ============================================================================

HANDLE_MAP = {
    "Turmeric & Curcumin Supplements": "turmeric-1400mg-tablets",
    "Pet Calm Formula for Dogs": None,  # pet product, delete
    "Green Coffee Bean MAX Capsules 20,000mg": "green-coffee-bean-extract-20000mg",
    "Bovine Collagen Powder with Vitamin C": "bovine-collagen-powder",
    "Vitamin C 500mg with Rosehip 400mg": "vitamin-c-500mg-rosehip-400mg",
    "Co-Enzyme Q10 30mg": "co-enzyme-q10-30mg",
    "Royal Jelly Tablets 750mg": "royal-jelly-capsules-750mg",
    "GreenShell Mussel Extract Powder 500 mg": "green-lipped-mussel-capsules",
    "Celadrin 500 mg": "celadrin-capsules-500mg",
    "Rhodiola Rosea 250 mg": "rhodiola-rosea-capsules-500mg",
    "Marine Chondroitin 750 mg": "marine-chondroitin-capsules-750mg",
    "Senna Max": "senna-tablets-max-strength",
    "Caffeine 200 mg": "caffeine-tablets-200mg",
    "Skin Care Plus": "skin-care-plus-capsules",
    "Multivits For Kids Strawberry Flavour": "multivits-for-kids",
    "5-HTP 100 mg": "5-htp-capsules-100mg",
    "DigestiWell Plus": "digestiwell-plus-capsules",
    "Capsicum 1000 mg": "capsicum-capsules-1000mg",
    "Probiotic Max": "probiotic-max-capsules",
    "OmegaMax": "omegamax-capsules",
    "Vegetarian Glucosamine 750 mg": "vegetarian-glucosamine-capsules-750mg",
    "Horny Goat Weed 2000 mg & Ginkgo Biloba 200 mg": "horny-goat-weed-ginkgo-biloba",
    "Fifty Plus Formula": "fifty-plus-formula",
    "HSN Plus": "hsn-plus-capsules",
    "Valerian Complex": "valerian-complex-capsules",
    "Acidophilus": "acidophilus-capsules",
    "Pure Inulin Powder": "pure-inulin-powder",
    "Co Enzyme Q10 100 mg": "co-enzyme-q10-100mg",
    "Slimming Shake - Vanilla Flavour": None,  # likely discontinued
    "Slimming Shake - Strawberry Flavour": None,  # likely discontinued
    "Salmon Oil (500ml)": None,  # pet product
    "Strawberry Whey Protein Powder": None,  # likely discontinued
    "Super Greens Powder": None,  # already fixed
    "Marine Collagen Powder with Vitamin C": "marine-collagen-powder",
}

# Also add pet products to delete list
PET_PRODUCTS = ["Pet Calm Formula for Dogs", "Salmon Oil (500ml)"]


def try_shopify(handle):
    """Try fetching image from Shopify."""
    url = f"{SHOPIFY_BASE}/products/{handle}.json"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            images = data.get("product", {}).get("images", [])
            if images:
                return images[0].get("src")
    except Exception:
        pass
    return None


fixed = []
still_broken = []
also_delete = []

for p in to_fix:
    name = p.get("name", "")
    pid = p["id"]

    # Check if it's a pet product or discontinued
    if name in PET_PRODUCTS:
        also_delete.append(p)
        log.info(f"  DELETE (pet/discontinued): {name}")
        continue

    handle = HANDLE_MAP.get(name)

    if handle is None and name in HANDLE_MAP:
        # Explicitly marked as discontinued/delete
        also_delete.append(p)
        log.info(f"  DELETE (discontinued): {name}")
        continue

    if handle:
        time.sleep(2.0)
        image_url = try_shopify(handle)
        if image_url:
            fixed.append({"id": pid, "name": name, "imageUrl": image_url})
            log.info(f"  FIXED: {name} -> {handle}")
        else:
            still_broken.append({"id": pid, "name": name})
            log.info(f"  MISS (handle 404): {name} -> {handle}")
    else:
        still_broken.append({"id": pid, "name": name})
        log.info(f"  MISS (no handle): {name}")

# ============================================================================
# Output
# ============================================================================

log.info(f"\n{'=' * 60}")
log.info("FINAL RESULTS")
log.info(f"{'=' * 60}")
log.info(f"Fixed with new images: {len(fixed)}")
log.info(f"To delete (non-products/pets/discontinued): {len(to_delete) + len(also_delete)}")
log.info(f"Still broken (no match): {len(still_broken)}")

all_delete = to_delete + also_delete
delete_ids = [p["id"] for p in all_delete]

if fixed:
    batches = []
    for i in range(0, len(fixed), 25):
        batches.append([{"id": p["id"], "imageUrl": p["imageUrl"]} for p in fixed[i:i + 25]])
    with open("scripts/simply_supplements_final_fix_batches.json", "w") as f:
        json.dump(batches, f, indent=2)
    log.info(f"Fix batches saved: scripts/simply_supplements_final_fix_batches.json")

if delete_ids:
    with open("scripts/simply_supplements_to_delete.json", "w") as f:
        json.dump({"ids": delete_ids, "products": [{"id": p["id"], "name": p.get("name", "")} for p in all_delete]}, f, indent=2)
    log.info(f"Delete list saved: scripts/simply_supplements_to_delete.json")

if still_broken:
    with open("scripts/simply_supplements_still_broken.json", "w") as f:
        json.dump(still_broken, f, indent=2)
    log.info(f"Still broken saved: scripts/simply_supplements_still_broken.json")
