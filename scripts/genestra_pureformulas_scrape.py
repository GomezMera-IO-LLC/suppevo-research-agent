#!/usr/bin/env python3
"""
Genestra Brands Image Enrichment via PureFormulas.com

PureFormulas carries Genestra products with good images. Their product URLs
follow: /product/{slug}-by-genestra/{item_number}

Strategy:
1. Load the list of Genestra products without images
2. For each product, search pureformulas.com via web search
3. Fetch the product page and extract the image URL
4. Generate batch update payloads

Note: This is slow (2-3 seconds per product due to web search rate limits)
but reliable since PureFormulas doesn't block basic fetches.
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

# Load unmatched products
unmatched = json.load(open("scripts/genestra_unmatched.json"))
log.info(f"Products to process: {len(unmatched)}")

# PureFormulas image URL pattern observed:
# https://www.pureformulas.com/ccstore/v1/images/?source=/file/v{id}/products/{slug}.jpg&height=780&width=780
# 
# But we can also use a simpler approach: their product images are also available at:
# https://www.pureformulas.com/ccstore/v1/images/?source=/file/products/{slug}.jpg
#
# Actually, the most reliable approach is to fetch each product page.
# But since that's slow, let's try using a Genestra-specific CDN that we can derive.
#
# Looking at the existing NIH pattern - all 94 products have DSLD IDs.
# Let's try to brute-force adjacent DSLD IDs to find more Genestra products.

# Alternative approach: Use the UPC to construct a predictable image URL.
# Many supplement retailers use a CDN pattern based on UPC.
# 
# NHC (Natural Healthy Concepts) uses:
# https://www.nhc.com/media/catalog/product/{first_char}/{second_char}/{upc}.jpg
#
# Let's try fullscript.com which is a major Genestra retailer:
# They use Shopify and have product images.


def fetch_page_images(url):
    """Fetch a page and extract image URLs containing 'genestra' or product-related terms."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # Find image URLs
            img_urls = re.findall(r'(https?://[^"\'>\s]+\.(?:jpg|jpeg|png|webp))', html)
            # Filter for product images (not icons, logos, etc)
            product_imgs = [u for u in img_urls if any(
                term in u.lower() for term in ["product", "genestra", "seroyal", "hmf", "ccstore"]
            ) and "icon" not in u.lower() and "logo" not in u.lower() and len(u) > 50]
            return product_imgs
    except Exception as e:
        return []


def try_pureformulas(product_name):
    """Try to find product image on pureformulas.com via their brand page."""
    # Construct a search-friendly slug
    slug = product_name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    
    # Try common URL patterns
    urls_to_try = [
        f"https://www.pureformulas.com/product/{slug}-by-genestra",
        f"https://www.pureformulas.com/product/{slug}-by-seroyal",
    ]
    
    for url in urls_to_try:
        imgs = fetch_page_images(url)
        if imgs:
            # Return the first large product image
            for img in imgs:
                if "height=780" in img or "width=780" in img:
                    return img
            return imgs[0]
    
    return None


def try_fullscript(product_name):
    """Try fullscript.com catalog page for Genestra."""
    slug = product_name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    
    url = f"https://fullscript.com/catalog/products/{slug}"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # Look for product image
            matches = re.findall(r'(https://[^"\']+(?:fullscript|spree)[^"\']+\.(?:jpg|png|webp))', html)
            if matches:
                return matches[0]
    except Exception:
        pass
    return None


def try_nhc(product_name):
    """Try Natural Healthy Concepts for Genestra products."""
    slug = product_name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    
    url = f"https://www.nhc.com/{slug}-by-genestra"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # Look for product image in og:image meta tag
            match = re.search(r'property="og:image"\s+content="([^"]+)"', html)
            if match:
                return match.group(1)
            # Try img src
            matches = re.findall(r'(https://[^"\']+genestra[^"\']+\.(?:jpg|png|webp))', html, re.IGNORECASE)
            if matches:
                return matches[0]
    except Exception:
        pass
    return None


# ============================================================================
# Process products
# ============================================================================

matched = []
failed = []

for i, product in enumerate(unmatched):
    name = product["name"]
    pid = product["id"]
    image_url = None
    
    # Try PureFormulas first
    time.sleep(1.5)
    image_url = try_pureformulas(name)
    
    # Try NHC
    if not image_url:
        time.sleep(1.0)
        image_url = try_nhc(name)
    
    if image_url:
        matched.append({"id": pid, "name": name, "imageUrl": image_url})
        log.info(f"  [{i+1}/{len(unmatched)}] ✅ {name}")
    else:
        failed.append({"id": pid, "name": name, "upc": product.get("upc", "")})
        log.info(f"  [{i+1}/{len(unmatched)}] ❌ {name}")
    
    # Progress report
    if (i + 1) % 25 == 0:
        log.info(f"  --- Progress: {i+1}/{len(unmatched)} | Matched: {len(matched)} | Failed: {len(failed)} ---")

# ============================================================================
# Results
# ============================================================================

log.info(f"\n{'=' * 60}")
log.info("RESULTS")
log.info(f"{'=' * 60}")
log.info(f"Matched: {len(matched)}")
log.info(f"Failed: {len(failed)}")
log.info(f"Match rate: {len(matched)/max(len(unmatched),1)*100:.1f}%")

if matched:
    batches = []
    for i in range(0, len(matched), 25):
        batches.append([{"id": p["id"], "imageUrl": p["imageUrl"]} for p in matched[i:i+25]])
    with open("scripts/genestra_retailer_batches.json", "w") as f:
        json.dump(batches, f, indent=2)
    log.info(f"Update batches ({len(batches)}): scripts/genestra_retailer_batches.json")

if failed:
    with open("scripts/genestra_still_missing.json", "w") as f:
        json.dump(failed, f, indent=2)
    log.info(f"Still missing: scripts/genestra_still_missing.json")
