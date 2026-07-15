#!/usr/bin/env python3
"""
GNC Preventive Nutrition Image Enrichment

GNC uses a custom e-commerce platform (Salesforce Commerce Cloud).
Product images follow the pattern:
https://www.gnc.com/dw/image/v2/BBLB_PRD/on/demandware.static/-/Sites-gnc-master/default/dw{hash}/{sku}.jpg

Strategy: Use GNC's search/product page to find image URLs for each product.
GNC product URLs follow: https://www.gnc.com/preventive-nutrition/{slug}.html
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

BRAND_ID = "796e891f-a29e-4c28-87b9-bd7b7d6091e4"
SUPPEVO_API_BASE = "https://api.dev.suppevo.com"

# ============================================================================
# Get products without images
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
log.info(f"Total GNC PN products: {len(all_products)}")
log.info(f"Without images: {len(no_image)}")

# ============================================================================
# GNC product image lookup
# GNC product pages have og:image meta tags we can extract
# ============================================================================


def name_to_slug(name):
    """Convert product name to GNC URL slug."""
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug


def fetch_gnc_image(product_name):
    """Try to fetch product image from GNC website."""
    slug = name_to_slug(product_name)

    # Try various URL patterns
    urls_to_try = [
        f"https://www.gnc.com/preventive-nutrition/{slug}.html",
        f"https://www.gnc.com/gnc-preventive-nutrition/{slug}.html",
        f"https://www.gnc.com/{slug}.html",
    ]

    for url in urls_to_try:
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                # Look for og:image
                match = re.search(r'property="og:image"\s+content="([^"]+)"', html)
                if match:
                    img = match.group(1)
                    if "gnc.com" in img or "demandware" in img:
                        return img
                # Look for product image in data
                match = re.search(r'"imageURL"\s*:\s*"([^"]+gnc[^"]+\.(?:jpg|png|webp))"', html)
                if match:
                    return match.group(1)
                # Look for large product images
                matches = re.findall(r'(https://www\.gnc\.com/dw/image[^"\'>\s]+)', html)
                if matches:
                    # Get largest image
                    for m in matches:
                        if "large" in m or "1000" in m or "800" in m:
                            return m
                    return matches[0]
        except urllib.error.HTTPError:
            continue
        except Exception:
            continue

    return None


# ============================================================================
# Process products
# ============================================================================

matched = []
failed = []

for i, product in enumerate(no_image):
    name = product.get("name", "")
    pid = product["id"]

    time.sleep(2.0)
    image_url = fetch_gnc_image(name)

    if image_url:
        matched.append({"id": pid, "name": name, "imageUrl": image_url})
        log.info(f"  [{i+1}/{len(no_image)}] ✅ {name}")
    else:
        failed.append({"id": pid, "name": name})
        log.info(f"  [{i+1}/{len(no_image)}] ❌ {name}")

log.info(f"\n{'=' * 60}")
log.info("RESULTS")
log.info(f"{'=' * 60}")
log.info(f"Matched: {len(matched)}")
log.info(f"Failed: {len(failed)}")

if matched:
    batches = []
    for i in range(0, len(matched), 25):
        batches.append([{"id": p["id"], "imageUrl": p["imageUrl"]} for p in matched[i:i+25]])
    with open("scripts/gnc_update_batches.json", "w") as f:
        json.dump(batches, f, indent=2)
    log.info(f"Update batches: scripts/gnc_update_batches.json")

if failed:
    with open("scripts/gnc_failed.json", "w") as f:
        json.dump(failed, f, indent=2)
    log.info(f"Failed: scripts/gnc_failed.json")
