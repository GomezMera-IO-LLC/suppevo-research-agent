#!/usr/bin/env python3
"""
Bee&You Plus+ Product Enrichment

Fetches all products from the Bee&You Shopify store and creates them in Suppevo.
Filters to only supplement products (not skincare/cosmetics).
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

SHOPIFY_BASE = "https://beeandyou.com"
BRAND_ID = "5f34d7d5-230c-4902-9e53-b26e86825b4d"
BRAND_NAME = "Bee&You Plus+"

# Supplement-related product types and keywords
SUPPLEMENT_TYPES = {"supplement", "vitamins", "health", "food", "honey", "propolis"}
SUPPLEMENT_KEYWORDS = [
    "propolis", "royal jelly", "bee pollen", "honey", "immune",
    "throat spray", "nasal", "capsule", "tablet", "gummy",
    "vitamin", "supplement", "extract", "tincture", "syrup",
    "elderberry", "manuka", "raw honey", "energy", "superfood",
]
EXCLUDE_KEYWORDS = ["serum", "cream", "moisturizer", "shampoo", "soap", "candle", "lip balm"]

# Category mapping
def map_category(title, product_type, tags):
    title_lower = title.lower()
    if any(w in title_lower for w in ["immune", "propolis", "elderberry", "throat"]):
        return "immunity"
    if any(w in title_lower for w in ["energy", "royal jelly", "bee pollen"]):
        return "energy"
    if any(w in title_lower for w in ["honey", "raw honey", "manuka"]):
        return "general"
    if any(w in title_lower for w in ["vitamin", "gummy", "capsule"]):
        return "general"
    if any(w in title_lower for w in ["sleep", "calm"]):
        return "sleep"
    if any(w in title_lower for w in ["digestive", "gut"]):
        return "digestion"
    return "general"


def is_supplement(product):
    """Filter: is this a supplement/food product (not skincare/cosmetics)?"""
    title = product.get("title", "").lower()
    ptype = (product.get("product_type") or "").lower()
    tags = [t.lower() for t in product.get("tags", [])]

    # Exclude skincare
    if any(kw in title for kw in EXCLUDE_KEYWORDS):
        return False
    if ptype in {"skincare", "cosmetics", "beauty"}:
        return False

    # Include supplements
    if any(kw in title for kw in SUPPLEMENT_KEYWORDS):
        return True
    if ptype in SUPPLEMENT_TYPES:
        return True
    if any(kw in " ".join(tags) for kw in SUPPLEMENT_KEYWORDS):
        return True

    return False


# ============================================================================
# Fetch all Shopify products
# ============================================================================

log.info("Fetching all products from Bee&You Shopify store...")
all_shopify = []
page = 1
while True:
    url = f"{SHOPIFY_BASE}/collections/all/products.json?page={page}&limit=30"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            products = data.get("products", [])
            if not products:
                break
            all_shopify.extend(products)
            log.info(f"  Page {page}: {len(products)} products (total: {len(all_shopify)})")
            page += 1
            time.sleep(2.0)
    except Exception as e:
        log.warning(f"  Error on page {page}: {e}")
        break

log.info(f"Total Shopify products: {len(all_shopify)}")

# Filter to supplements only
supplements = [p for p in all_shopify if is_supplement(p)]
log.info(f"Supplement products (filtered): {len(supplements)}")
log.info(f"Excluded (skincare/other): {len(all_shopify) - len(supplements)}")

# ============================================================================
# Build product data for Suppevo
# ============================================================================

products_to_create = []

for sp in supplements:
    title = sp.get("title", "")
    images = sp.get("images", [])
    image_url = images[0]["src"] if images else None
    variants = sp.get("variants", [])
    
    # Get form from title
    title_lower = title.lower()
    if "capsule" in title_lower:
        form = "Capsule"
    elif "tablet" in title_lower or "gummy" in title_lower or "gummies" in title_lower:
        form = "Tablet or Pill"
    elif "spray" in title_lower:
        form = "Spray"
    elif "liquid" in title_lower or "syrup" in title_lower or "tincture" in title_lower:
        form = "Liquid"
    elif "powder" in title_lower:
        form = "Powder"
    elif "honey" in title_lower:
        form = "Liquid"
    else:
        form = None

    category = map_category(title, sp.get("product_type", ""), sp.get("tags", []))

    product = {
        "name": title,
        "category": category,
        "brand": BRAND_NAME,
        "brand_id": BRAND_ID,
        "form": form,
        "manufacturer": "BeeAndYou",
        "country_of_origin": "Turkey",
        "website": "https://beeandyou.com/",
    }

    if image_url:
        product["imageUrl"] = image_url

    products_to_create.append(product)

log.info(f"\nProducts to create in Suppevo: {len(products_to_create)}")

# Show what we'll create
for p in products_to_create:
    has_img = "✅" if p.get("imageUrl") else "❌"
    log.info(f"  {has_img} [{p['category']}] {p['name']}")

# Save for batch creation
batches = []
for i in range(0, len(products_to_create), 25):
    batches.append(products_to_create[i:i+25])

with open("scripts/beeandyou_create_batches.json", "w") as f:
    json.dump(batches, f, indent=2)
log.info(f"\nSaved {len(batches)} batch(es) to scripts/beeandyou_create_batches.json")
