#!/usr/bin/env python3
"""
Genestra Brands Image Enrichment via NIH DSLD API.

The NIH Dietary Supplement Label Database has product images accessible via UPC.
Pattern: https://api.ods.od.nih.gov/dsld/s3/pdf/thumbnails/{dsld_id}.jpg

Strategy:
1. Get all Genestra products from Suppevo (with UPCs)
2. For products without images, search DSLD by UPC to get dsld_id
3. Construct image URL from dsld_id
4. Batch update products with images
"""
import json
import logging
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
DSLD_API = "https://api.ods.od.nih.gov/dsld/v9"

# ============================================================================
# Get Suppevo products
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
log.info(f"Total products: {len(all_products)}")
log.info(f"Without images: {len(no_image)}")
log.info(f"With UPCs (no image): {sum(1 for p in no_image if p.get('upc'))}")

# ============================================================================
# Search DSLD by UPC
# ============================================================================


def search_dsld_by_upc(upc):
    """Search the DSLD database for a product by UPC barcode."""
    url = f"{DSLD_API}/search?query={upc}&searchfield=UPC"
    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("list", [])
            if results:
                return results[0].get("dsld_id")
    except Exception as e:
        log.warning(f"  DSLD error for UPC {upc}: {e}")
    return None


def search_dsld_by_name(name):
    """Search DSLD by product name."""
    # URL encode the name
    encoded = urllib.request.quote(name)
    url = f"{DSLD_API}/search?query={encoded}&searchfield=Product_Name"
    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("list", [])
            # Find Genestra result
            for r in results:
                brand = (r.get("brand_name") or "").lower()
                if "genestra" in brand:
                    return r.get("dsld_id")
            # If no Genestra match, return first result if it's close
            if results:
                return results[0].get("dsld_id")
    except Exception as e:
        pass
    return None


# ============================================================================
# Match products
# ============================================================================

matched = []
unmatched = []

for i, product in enumerate(no_image):
    name = product.get("name", "")
    upc = product.get("upc", "")
    pid = product["id"]
    dsld_id = None

    # Try UPC first
    if upc:
        time.sleep(0.5)
        dsld_id = search_dsld_by_upc(upc)

    # Try name search if UPC didn't work
    if not dsld_id:
        time.sleep(0.5)
        dsld_id = search_dsld_by_name(f"Genestra {name}")

    if dsld_id:
        image_url = f"https://api.ods.od.nih.gov/dsld/s3/pdf/thumbnails/{dsld_id}.jpg"
        matched.append({"id": pid, "name": name, "imageUrl": image_url})
        if (i + 1) % 20 == 0:
            log.info(f"  [{i+1}/{len(no_image)}] Progress: {len(matched)} matched")
    else:
        unmatched.append({"id": pid, "name": name})

    if (i + 1) % 50 == 0:
        log.info(f"  [{i+1}/{len(no_image)}] Matched: {len(matched)}, Unmatched: {len(unmatched)}")

# ============================================================================
# Results
# ============================================================================

log.info(f"\n{'=' * 60}")
log.info("RESULTS")
log.info(f"{'=' * 60}")
log.info(f"Matched: {len(matched)}")
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
    log.info(f"Unmatched: scripts/genestra_unmatched.json")
    log.info(f"\nSample unmatched:")
    for p in unmatched[:10]:
        log.info(f"  - {p['name']}")
