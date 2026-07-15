#!/usr/bin/env python3
"""
Simply Supplements Image Enrichment Script

Fetches product images from the Simply Supplements Shopify store and matches
them to existing Suppevo products by name, then generates batch update payloads.

Strategy:
1. Fetch all products from Simply Supplements Shopify collection API (paginated)
2. Build a lookup map: normalized name → image URL
3. Get all Simply Supplements products from Suppevo missing images
4. Match by normalized name
5. Output batch update payloads for the suppevo MCP server
"""

import json
import logging
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

SUPPEVO_API_BASE = os.environ.get("SUPPEVO_API_BASE", "https://api.dev.suppevo.com")
BRAND_ID = "91a56477-b06f-4440-ba06-46c730784533"
SHOPIFY_BASE = "https://www.simplysupplements.co.uk"
SHOPIFY_DELAY = 2.0

# ============================================================================
# Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ============================================================================
# Name Normalization
# ============================================================================


def normalize_name(name):
    n = name.lower().strip()
    n = n.replace("®", "").replace("™", "").replace("(r)", "")
    n = re.sub(r"\s+", " ", n)
    return n


def make_match_keys(name):
    keys = set()
    n = normalize_name(name)
    keys.add(n)

    # Remove content in parentheses
    no_parens = re.sub(r"\s*\([^)]*\)", "", n).strip()
    keys.add(no_parens)

    # Remove dosage (e.g., "500 mg", "1000 iu", "400 iu", "250 mcg")
    no_dose = re.sub(r"\s+\d+[\.,]?\d*\s*(mg|mcg|iu|g|ml|%)\b", "", n).strip()
    keys.add(no_dose)

    # Remove both
    no_both = re.sub(r"\s+\d+[\.,]?\d*\s*(mg|mcg|iu|g|ml|%)\b", "", no_parens).strip()
    keys.add(no_both)

    # Remove "capsules", "tablets", "softgels", "powder"
    for suffix in [" capsules", " tablets", " softgels", " powder", " capsule", " tablet"]:
        for k in list(keys):
            if k.endswith(suffix):
                keys.add(k[: -len(suffix)].strip())

    keys.discard("")
    return list(keys)


# ============================================================================
# Shopify Collection API
# ============================================================================


def fetch_shopify_page(page):
    url = f"{SHOPIFY_BASE}/products.json?page={page}&limit=30"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("products", [])
    except urllib.error.HTTPError as e:
        if e.code == 429:
            log.warning(f"  Rate limited on page {page}, waiting 10s...")
            time.sleep(10)
            return fetch_shopify_page(page)
        log.warning(f"  HTTP {e.code} fetching page {page}")
        return []
    except Exception as e:
        log.warning(f"  Error fetching page {page}: {e}")
        return []


def get_all_shopify_products():
    all_products = []
    page = 1
    while True:
        log.info(f"  Fetching Shopify page {page}...")
        products = fetch_shopify_page(page)
        if not products:
            break
        all_products.extend(products)
        log.info(f"    Got {len(products)} products (total: {len(all_products)})")
        page += 1
        time.sleep(SHOPIFY_DELAY)
    return all_products


def extract_image(product):
    images = product.get("images", [])
    if images:
        return images[0].get("src")
    return None


# ============================================================================
# Suppevo API
# ============================================================================


def get_all_suppevo_products():
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
    return all_products


# ============================================================================
# Matching
# ============================================================================


def build_shopify_index(shopify_products):
    index = {}
    for product in shopify_products:
        title = product.get("title", "")
        image_url = extract_image(product)
        if not image_url or not title:
            continue
        keys = make_match_keys(title)
        for key in keys:
            if key not in index:
                index[key] = image_url
    return index


def find_image(product_name, shopify_index):
    keys = make_match_keys(product_name)
    for key in keys:
        if key in shopify_index:
            return shopify_index[key]
    return None


# ============================================================================
# Main
# ============================================================================


def main():
    log.info("=" * 60)
    log.info("Simply Supplements Image Enrichment")
    log.info("=" * 60)

    # Step 1: Get Shopify products (with caching)
    cache_path = Path("scripts/simply_supplements_shopify_cache.json")

    if cache_path.exists():
        log.info(f"\nLoading Shopify data from cache: {cache_path}")
        with open(cache_path) as f:
            shopify_products = json.load(f)
    else:
        log.info("\nFetching all products from Simply Supplements Shopify store...")
        shopify_products = get_all_shopify_products()
        with open(cache_path, "w") as f:
            json.dump(shopify_products, f)
        log.info(f"Cached {len(shopify_products)} Shopify products to: {cache_path}")

    log.info(f"Total Shopify products: {len(shopify_products)}")

    # Step 2: Build matching index
    log.info("\nBuilding image lookup index...")
    shopify_index = build_shopify_index(shopify_products)
    log.info(f"Index has {len(shopify_index)} name variants mapped to images")

    # Step 3: Get Suppevo products
    log.info("\nFetching Simply Supplements products from Suppevo...")
    suppevo_products = get_all_suppevo_products()
    log.info(f"Total Suppevo products: {len(suppevo_products)}")

    missing_images = [p for p in suppevo_products if not p.get("imageUrl")]
    log.info(f"Products missing images: {len(missing_images)}")

    # Step 4: Match
    log.info("\nMatching products...")
    matched = []
    unmatched = []

    for product in missing_images:
        name = product.get("name", "")
        product_id = product.get("id", "")
        image_url = find_image(name, shopify_index)
        if image_url:
            matched.append({"id": product_id, "name": name, "imageUrl": image_url})
        else:
            unmatched.append({"id": product_id, "name": name})

    # Step 5: Report
    log.info(f"\n{'=' * 60}")
    log.info("RESULTS")
    log.info(f"{'=' * 60}")
    log.info(f"Total processed:  {len(missing_images)}")
    log.info(f"Matched:          {len(matched)}")
    log.info(f"Unmatched:        {len(unmatched)}")
    log.info(f"Match rate:       {len(matched)/max(len(missing_images),1)*100:.1f}%")

    if unmatched:
        log.info(f"\nUnmatched products:")
        for p in unmatched[:30]:
            log.info(f"  - {p['name']}")
        if len(unmatched) > 30:
            log.info(f"  ... and {len(unmatched) - 30} more")

    # Step 6: Save results
    output_dir = Path("scripts")

    if matched:
        matched_path = output_dir / "simply_supplements_image_batch.json"
        with open(matched_path, "w") as f:
            json.dump(matched, f, indent=2)
        log.info(f"\nMatched products saved to: {matched_path}")

        # Generate batch update commands (25 per batch)
        batches = []
        for i in range(0, len(matched), 25):
            batch = matched[i : i + 25]
            batches.append([{"id": p["id"], "imageUrl": p["imageUrl"]} for p in batch])

        batches_path = output_dir / "simply_supplements_update_batches.json"
        with open(batches_path, "w") as f:
            json.dump(batches, f, indent=2)
        log.info(f"Update batches ({len(batches)}): {batches_path}")

    if unmatched:
        unmatched_path = output_dir / "simply_supplements_unmatched.json"
        with open(unmatched_path, "w") as f:
            json.dump(unmatched, f, indent=2)
        log.info(f"Unmatched products saved to: {unmatched_path}")


if __name__ == "__main__":
    main()
