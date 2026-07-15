#!/usr/bin/env python3
"""
BulkSupplements.com Image Enrichment Script

Fetches product images from the BulkSupplements Shopify collection API and
matches them to existing Suppevo products by name, then generates batch
update payloads.

Strategy:
1. Fetch all products from Shopify collection API (paginated, ~30 per page)
2. Build a lookup map: normalized name → image URL
3. Get all BulkSupplements products from Suppevo missing images
4. Match by normalized name
5. Output batch update payloads for the suppevo MCP server

Usage:
    # Dry run — find images and report matches:
    python scripts/bulksupplements_image_enrichment.py

    # Save matched images to JSON for batch updating:
    python scripts/bulksupplements_image_enrichment.py --save
"""

import argparse
import json
import logging
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

# ============================================================================
# Configuration
# ============================================================================

SUPPEVO_API_BASE = os.environ.get("SUPPEVO_API_BASE", "https://api.dev.suppevo.com")
BRAND_ID = "4089dd6f-2a5c-4765-8e11-8e00af34063e"
SHOPIFY_BASE = "https://www.bulksupplements.com"
SHOPIFY_DELAY = 2.0  # seconds between Shopify collection page requests

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


def normalize_name(name: str) -> str:
    """Normalize a product name for matching."""
    n = name.lower().strip()
    # Remove trademark/registered symbols
    n = n.replace("®", "").replace("™", "")
    # Normalize whitespace
    n = re.sub(r"\s+", " ", n)
    return n


def make_match_keys(name: str) -> list:
    """Generate multiple matching keys from a product name."""
    keys = set()
    n = normalize_name(name)
    keys.add(n)
    
    # Remove content in parentheses
    no_parens = re.sub(r"\s*\([^)]*\)", "", n).strip()
    keys.add(no_parens)
    
    # Remove dosage (e.g., "500 mg", "1000 iu", "400 iu")
    no_dose = re.sub(r"\s+\d+\s*(mg|mcg|iu|g|ml|%|mcg)\b", "", n).strip()
    keys.add(no_dose)
    
    # Remove both
    no_both = re.sub(r"\s+\d+\s*(mg|mcg|iu|g|ml|%)\b", "", no_parens).strip()
    keys.add(no_both)
    
    # Add/remove "powder" suffix
    for k in list(keys):
        if k.endswith(" powder"):
            keys.add(k[:-7].strip())
        else:
            keys.add(k + " powder")
    
    # Add/remove "extract" variations
    for k in list(keys):
        if "extract" in k:
            keys.add(k.replace(" extract", "").strip())
            keys.add(k.replace("extract ", "").strip())
    
    # Remove empty strings
    keys.discard("")
    return list(keys)


# ============================================================================
# Shopify Collection API
# ============================================================================


def fetch_shopify_collection_page(page: int) -> list:
    """Fetch a page of products from the Shopify collection."""
    url = f"{SHOPIFY_BASE}/collections/all/products.json?page={page}&limit=30"
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
            return fetch_shopify_collection_page(page)  # retry
        log.warning(f"  HTTP {e.code} fetching page {page}")
        return []
    except Exception as e:
        log.warning(f"  Error fetching page {page}: {e}")
        return []


def get_all_shopify_products() -> list:
    """Fetch all products from the Shopify collection API."""
    all_products = []
    page = 1
    
    while True:
        log.info(f"  Fetching Shopify page {page}...")
        products = fetch_shopify_collection_page(page)
        
        if not products:
            break
        
        all_products.extend(products)
        log.info(f"    Got {len(products)} products (total: {len(all_products)})")
        
        page += 1
        time.sleep(SHOPIFY_DELAY)
    
    return all_products


def extract_image_from_shopify_product(product: dict) -> Optional[str]:
    """Extract the main product image from a Shopify product object."""
    images = product.get("images", [])
    if images:
        src = images[0].get("src", "")
        if src:
            return src
    
    # Try featured image from first variant
    variants = product.get("variants", [])
    for v in variants:
        fi = v.get("featured_image")
        if fi and fi.get("src"):
            return fi["src"]
    
    return None


# ============================================================================
# Suppevo API
# ============================================================================


def suppevo_get(path: str, params: dict = None) -> dict:
    """GET request to Suppevo public API."""
    url = f"{SUPPEVO_API_BASE}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        if query:
            url += "?" + query
    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log.warning(f"Suppevo API error: {e}")
        return {"items": [], "error": str(e)}


def get_all_suppevo_products() -> list:
    """Paginate through all BulkSupplements products in Suppevo."""
    all_products = []
    cursor = None
    page = 0

    while True:
        params = {"limit": "100"}
        if cursor:
            params["cursor"] = cursor

        data = suppevo_get(f"/public/brands/{BRAND_ID}/products", params)
        items = data.get("items", [])
        all_products.extend(items)
        page += 1

        log.info(f"  Fetched Suppevo page {page}: {len(items)} products (total: {len(all_products)})")

        cursor = data.get("next_cursor")
        if not cursor or not items:
            break

        time.sleep(0.2)

    return all_products


# ============================================================================
# Matching Logic
# ============================================================================


def build_shopify_index(shopify_products: list) -> dict:
    """Build a lookup index from normalized names to image URLs."""
    index = {}
    
    for product in shopify_products:
        title = product.get("title", "")
        image_url = extract_image_from_shopify_product(product)
        
        if not image_url or not title:
            continue
        
        # Add all matching keys
        keys = make_match_keys(title)
        for key in keys:
            if key not in index:
                index[key] = image_url
    
    return index


def find_image_for_product(product_name: str, shopify_index: dict) -> Optional[str]:
    """Try to find an image URL for a Suppevo product name."""
    keys = make_match_keys(product_name)
    
    for key in keys:
        if key in shopify_index:
            return shopify_index[key]
    
    return None


# ============================================================================
# Main
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Enrich BulkSupplements products with images from their Shopify store"
    )
    parser.add_argument("--save", action="store_true", help="Save results to JSON")
    parser.add_argument("--shopify-cache", type=str, help="Path to cached Shopify data")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("BulkSupplements.com Image Enrichment")
    log.info("=" * 60)

    # Step 1: Get Shopify products (with caching)
    cache_path = Path("scripts/bulksupplements_shopify_cache.json")
    
    if args.shopify_cache and Path(args.shopify_cache).exists():
        log.info(f"\nLoading Shopify data from cache: {args.shopify_cache}")
        with open(args.shopify_cache) as f:
            shopify_products = json.load(f)
    elif cache_path.exists():
        log.info(f"\nLoading Shopify data from cache: {cache_path}")
        with open(cache_path) as f:
            shopify_products = json.load(f)
    else:
        log.info("\nFetching all products from BulkSupplements Shopify store...")
        shopify_products = get_all_shopify_products()
        
        # Cache for future runs
        with open(cache_path, "w") as f:
            json.dump(shopify_products, f)
        log.info(f"Cached {len(shopify_products)} Shopify products to: {cache_path}")
    
    log.info(f"Total Shopify products: {len(shopify_products)}")

    # Step 2: Build matching index
    log.info("\nBuilding image lookup index...")
    shopify_index = build_shopify_index(shopify_products)
    log.info(f"Index has {len(shopify_index)} name variants mapped to images")

    # Step 3: Get Suppevo products
    log.info("\nFetching BulkSupplements products from Suppevo...")
    suppevo_products = get_all_suppevo_products()
    log.info(f"Total Suppevo products: {len(suppevo_products)}")

    # Filter to those missing images
    missing_images = [p for p in suppevo_products if not p.get("imageUrl")]
    log.info(f"Products missing images: {len(missing_images)}")

    # Step 4: Match
    log.info("\nMatching products...")
    matched = []
    unmatched = []

    for product in missing_images:
        name = product.get("name", "")
        product_id = product.get("id", "")

        image_url = find_image_for_product(name, shopify_index)

        if image_url:
            matched.append({
                "id": product_id,
                "name": name,
                "imageUrl": image_url,
            })
        else:
            unmatched.append({"id": product_id, "name": name})

    # Step 5: Report
    log.info(f"\n{'=' * 60}")
    log.info("RESULTS")
    log.info(f"{'=' * 60}")
    log.info(f"Total processed:  {len(missing_images)}")
    log.info(f"Matched:          {len(matched)} ✅")
    log.info(f"Unmatched:        {len(unmatched)} ❌")
    log.info(f"Match rate:       {len(matched)/max(len(missing_images),1)*100:.1f}%")

    if unmatched:
        log.info(f"\nSample unmatched products (first 30):")
        for p in unmatched[:30]:
            log.info(f"  - {p['name']}")
        if len(unmatched) > 30:
            log.info(f"  ... and {len(unmatched) - 30} more")

    # Step 6: Save results
    if args.save and matched:
        output_dir = Path("scripts")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save matched products
        matched_path = output_dir / "bulksupplements_image_batch.json"
        with open(matched_path, "w") as f:
            json.dump(matched, f, indent=2)
        log.info(f"\nMatched products saved to: {matched_path}")

        # Save unmatched
        if unmatched:
            unmatched_path = output_dir / "bulksupplements_unmatched.json"
            with open(unmatched_path, "w") as f:
                json.dump(unmatched, f, indent=2)
            log.info(f"Unmatched products saved to: {unmatched_path}")

        # Generate batch update commands (25 products per batch)
        batches = []
        for i in range(0, len(matched), 25):
            batch = matched[i:i+25]
            batches.append([
                {"id": p["id"], "imageUrl": p["imageUrl"]}
                for p in batch
            ])
        
        batches_path = output_dir / "bulksupplements_update_batches.json"
        with open(batches_path, "w") as f:
            json.dump(batches, f, indent=2)
        log.info(f"Update batches ({len(batches)} batches of max 25): {batches_path}")

    elif not matched:
        log.info("\nNo matches found. Check if Shopify cache is populated.")


if __name__ == "__main__":
    main()
