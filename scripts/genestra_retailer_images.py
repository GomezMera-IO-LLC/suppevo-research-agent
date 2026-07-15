#!/usr/bin/env python3
"""
Genestra Brands Image Enrichment via Canadian Retailers.

Searches healthyplanetcanada.com and other retailers for Genestra product images.
These retailers have product pages with images that follow predictable patterns.

Strategy:
1. Get all Genestra products missing images (with UPCs)
2. For each product, search healthyplanetcanada.com by name
3. Extract image URL from search results or product pages
4. Generate batch update payloads
"""
import json
import logging
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

SUPPEVO_API_BASE = "https://api.dev.suppevo.com"
BRAND_ID = "61bba5ef-9106-49f7-820a-d709e0fe534f"

# ============================================================================
# Get Suppevo products without images
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

no_image = [p for p in all_products if not p.get("imageUrl")]
log.info(f"Total products: {len(all_products)}, without images: {len(no_image)}")

# ============================================================================
# Image lookup via HealthyPlanetCanada.com
# Their image URLs follow pattern:
# https://www.healthyplanetcanada.com/media/catalog/product/cache/.../genestra-{product-slug}.jpg
#
# But the most reliable approach is using their search to find products by name
# and the Genestra product images on Amazon which follow:
# https://m.media-amazon.com/images/I/{asin_image_id}.jpg
#
# Actually the most reliable free source is iHerb or HealthyPlanetCanada
# which both show Genestra products with standard packaging images.
#
# Simplest approach: Genestra uses a consistent image naming on their CDN
# via seroyal.com. Let's try the pattern:
# https://www.seroyal.com/media/catalog/product/{first_letter}/{second_letter}/{sku}.jpg
# ============================================================================

# Alternative: Try using the DSLD directly with correct API format
# The DSLD v9 API uses: GET /dsld/v9/label/{dsld_id}
# And search: GET /dsld/v9/browse-products?brandName=Genestra+Brands


def search_dsld_brand():
    """Get all Genestra products from DSLD browse endpoint."""
    url = "https://api.ods.od.nih.gov/dsld/v9/browse-products?brandName=Genestra+Brands&size=500"
    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except Exception as e:
        log.warning(f"DSLD browse error: {e}")
        return None


log.info("Trying DSLD browse-products API for Genestra Brands...")
dsld_data = search_dsld_brand()

if dsld_data and "list" in dsld_data:
    dsld_products = dsld_data["list"]
    log.info(f"DSLD returned {len(dsld_products)} Genestra products")

    # Build UPC -> dsld_id map
    dsld_by_upc = {}
    dsld_by_name = {}
    for dp in dsld_products:
        dsld_id = dp.get("dsld_id")
        upc = dp.get("upc", "")
        name = (dp.get("product_name") or "").lower().strip()
        if dsld_id:
            if upc:
                dsld_by_upc[upc] = dsld_id
            if name:
                dsld_by_name[name] = dsld_id

    log.info(f"DSLD index: {len(dsld_by_upc)} by UPC, {len(dsld_by_name)} by name")

    # Match products
    matched = []
    unmatched = []

    for product in no_image:
        name = product.get("name", "")
        upc = product.get("upc", "")
        pid = product["id"]
        dsld_id = None

        # Try UPC match
        if upc:
            dsld_id = dsld_by_upc.get(upc)

        # Try name match
        if not dsld_id:
            name_lower = name.lower().strip()
            dsld_id = dsld_by_name.get(name_lower)
            # Try with "genestra brands" prefix
            if not dsld_id:
                dsld_id = dsld_by_name.get(f"genestra brands {name_lower}")

        # Try fuzzy name match
        if not dsld_id:
            name_words = set(re.sub(r"[^a-z0-9 ]", " ", name.lower()).split())
            name_words -= {"mg", "mcg", "iu", "natural", "flavor", "flavour"}
            name_words = {w for w in name_words if len(w) > 2}
            
            best_score = 0
            best_id = None
            for dsld_name, did in dsld_by_name.items():
                dsld_words = set(re.sub(r"[^a-z0-9 ]", " ", dsld_name).split())
                dsld_words -= {"mg", "mcg", "iu", "natural", "flavor", "flavour", "genestra", "brands"}
                dsld_words = {w for w in dsld_words if len(w) > 2}
                if not name_words or not dsld_words:
                    continue
                overlap = name_words & dsld_words
                score = len(overlap) / len(name_words)
                if score > best_score and score >= 0.6:
                    best_score = score
                    best_id = did
            
            if best_id:
                dsld_id = best_id

        if dsld_id:
            image_url = f"https://api.ods.od.nih.gov/dsld/s3/pdf/thumbnails/{dsld_id}.jpg"
            matched.append({"id": pid, "name": name, "imageUrl": image_url, "dsld_id": dsld_id})
        else:
            unmatched.append({"id": pid, "name": name, "upc": upc})

    log.info(f"\n{'=' * 60}")
    log.info("RESULTS")
    log.info(f"{'=' * 60}")
    log.info(f"Matched via DSLD: {len(matched)}")
    log.info(f"Unmatched: {len(unmatched)}")
    log.info(f"Match rate: {len(matched)/max(len(no_image),1)*100:.1f}%")

    if matched:
        batches = []
        for i in range(0, len(matched), 25):
            batches.append([{"id": p["id"], "imageUrl": p["imageUrl"]} for p in matched[i:i+25]])
        with open("scripts/genestra_update_batches.json", "w") as f:
            json.dump(batches, f, indent=2)
        log.info(f"Update batches ({len(batches)}): scripts/genestra_update_batches.json")

    if unmatched:
        with open("scripts/genestra_unmatched.json", "w") as f:
            json.dump(unmatched, f, indent=2)
        log.info(f"Unmatched saved: scripts/genestra_unmatched.json")
        log.info(f"\nSample unmatched (first 15):")
        for p in unmatched[:15]:
            log.info(f"  - {p['name']} (UPC: {p.get('upc', 'N/A')})")

else:
    log.error("DSLD browse API failed. Trying alternative approach...")
    
    # Fallback: Try healthyplanetcanada.com search
    # Their product URLs follow: /genestra-{slug}.html
    # Images: /media/catalog/product/cache/.../genestra_{sku}.jpg
    log.info("Falling back to direct image URL construction...")
    
    # Genestra product images on healthyplanetcanada follow a pattern
    # where the image filename is based on a slug of the product name.
    # Example: genestra-hmf-forte-120-veggie-caps.html
    # Image: https://www.healthyplanetcanada.com/media/catalog/product/cache/...
    
    # For now, save the list of products needing images for manual review
    with open("scripts/genestra_unmatched.json", "w") as f:
        json.dump([{"id": p["id"], "name": p.get("name", ""), "upc": p.get("upc", "")} for p in no_image], f, indent=2)
    log.info(f"Saved {len(no_image)} products needing images to scripts/genestra_unmatched.json")
