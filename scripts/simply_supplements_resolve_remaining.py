#!/usr/bin/env python3
"""
Resolve remaining Simply Supplements products without images using fuzzy matching
against the Shopify cache, then try individual product page lookups.
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

SHOPIFY_BASE = "https://www.simplysupplements.co.uk"

# Load data
unmatched = json.load(open("scripts/simply_supplements_unmatched.json"))
cache = json.load(open("scripts/simply_supplements_shopify_cache.json"))

log.info(f"Unmatched products to resolve: {len(unmatched)}")
log.info(f"Shopify cache products: {len(cache)}")

# ============================================================================
# Build a more comprehensive index from Shopify cache
# ============================================================================

shopify_products = []
for p in cache:
    title = p.get("title", "")
    images = p.get("images", [])
    img = images[0]["src"] if images else None
    handle = p.get("handle", "")
    if img:
        shopify_products.append({
            "title": title.lower().strip(),
            "handle": handle,
            "image": img,
            "words": set(re.sub(r"[^a-z0-9 ]", " ", title.lower()).split()),
        })

# ============================================================================
# Fuzzy matching with higher tolerance
# ============================================================================


def fuzzy_match(name):
    """Find best Shopify match using word overlap."""
    name_lower = name.lower().strip()
    name_clean = re.sub(r"[^a-z0-9 ]", " ", name_lower)
    name_words = set(name_clean.split())
    # Remove noise
    noise = {"mg", "mcg", "iu", "ml", "plus", "max", "for", "with", "and", "the"}
    name_words -= noise
    # Remove pure numbers
    name_words = {w for w in name_words if not w.isdigit()}

    if not name_words:
        return None

    best_match = None
    best_score = 0

    for sp in shopify_products:
        shop_words = sp["words"] - noise
        shop_words = {w for w in shop_words if not w.isdigit()}
        if not shop_words:
            continue

        overlap = name_words & shop_words
        # Use Jaccard-like scoring: overlap relative to query
        score = len(overlap) / len(name_words) if name_words else 0

        if score > best_score and score >= 0.4:
            best_score = score
            best_match = sp

    if best_match:
        return {
            "handle": best_match["handle"],
            "image": best_match["image"],
            "title": best_match["title"],
            "score": best_score,
        }
    return None


# ============================================================================
# Try direct handle lookup on Shopify
# ============================================================================

HANDLE_GUESSES = {
    "Ginkgo 3000 mg & Ginseng 1000 mg": ["ginkgo-biloba-ginseng-tablets"],
    "GreenShell Mussel Extract Powder 500 mg": ["green-lipped-mussel-extract"],
    "Bilberry Plus 2000 mg": ["bilberry-plus-6000mg-tablets"],
    "Omega 3, 6 & 9 Fish Oils 1000 mg": ["omega-3-6-9-capsules-1000mg"],
    "Pure Inulin Powder": ["pure-inulin-powder"],
    "Celadrin 500 mg": ["celadrin-capsules-500mg"],
    "Co Enzyme Q10 300 mg": ["co-enzyme-q10-300mg-capsules"],
    "Glucosamine 500 mg, Marine Chondroitin 100 mg & MSM 100 mg": ["glucosamine-chondroitin-msm-tablets"],
    "Rhodiola Rosea 250 mg": ["rhodiola-rosea-capsules-500mg"],
    "Marine Chondroitin 750 mg": ["marine-chondroitin-capsules-750mg"],
    "Lecithin 1200 mg": ["lecithin-capsules-1200mg"],
    "Senna Max": ["senna-tablets-max-strength"],
    "Caffeine 200 mg": ["caffeine-tablets-200mg"],
    "Co Enzyme Q10 100 mg": ["co-enzyme-q10-100mg"],
    "Skin Care Plus": ["skin-care-plus-capsules"],
    "Multivits For Kids Strawberry Flavour": ["multivits-for-kids"],
    "NatiCol Marine Collagen Plus 400 mg": ["naticol-marine-collagen-plus"],
    "Omega 3 Fish Oil 1000 mg": ["omega-3-fish-oil-capsules-1000mg"],
    "Grapeseed 50 mg": ["grapeseed-capsules-50mg"],
    "5-HTP 100 mg": ["5-htp-capsules-100mg"],
    "Goji Berry 2000 mg": ["goji-berry-capsules-2000mg"],
    "DigestiWell Plus": ["digestiwell-plus-capsules"],
    "Chromium 200 mcg": ["chromium-tablets-200mcg"],
    "Capsicum 1000 mg": ["capsicum-capsules-1000mg"],
    "Probiotic Max": ["probiotic-max-capsules"],
    "OmegaMax": ["omegamax-capsules"],
    "Glucosamine Sulphate 2KCl 500 mg & Marine Chondroitin 400 mg (20%)": ["glucosamine-500mg-chondroitin-400mg"],
    "CLA 1000 mg": ["cla-capsules-1000mg"],
    "Vegetarian Glucosamine 750 mg": ["vegetarian-glucosamine-capsules-750mg"],
    "Super Greens Powder": ["super-greens-powder"],
    "Chromium Complex": ["chromium-complex-capsules"],
    "Hyaluronic Acid 50 mg": ["hyaluronic-acid-capsules-50mg"],
    "Pomegranate 10000 mg": ["pomegranate-capsules-10000mg"],
    "Korean Ginseng 1300 mg": ["korean-ginseng-capsules-1300mg"],
    "Vitamin D3 2000 IU": ["vitamin-d3-tablets-2000iu"],
    "Horny Goat Weed 2000 mg & Ginkgo Biloba 200 mg": ["horny-goat-weed-ginkgo-biloba"],
    "Fifty Plus Formula": ["fifty-plus-formula"],
    "Vitamin E 400 IU": ["vitamin-e-capsules-400iu"],
    "HSN Plus": ["hsn-plus-capsules"],
    "Vitamin C 500 mg with Rosehip": ["vitamin-c-500mg-rosehip"],
    "Selenium 200 mcg With Vitamins A, C & E": ["selenium-200mcg-vitamins-ace"],
    "Bromelain 350 mg": ["bromelain-capsules-350mg"],
    "Bilberry Plus 6000 mg": ["bilberry-plus-6000mg-tablets"],
    "Valerian Complex": ["valerian-complex-capsules"],
    "Black Cohosh 200 mg": ["black-cohosh-capsules-200mg"],
    "Alpha Lipoic Acid 250 mg": ["alpha-lipoic-acid-capsules-250mg"],
    "Pumpkin Seed 2000 mg": ["pumpkin-seed-capsules-2000mg"],
    "Acidophilus": ["acidophilus-capsules"],
    "MSM 1000 mg": ["msm-tablets-1000mg"],
    "Ginger 12000 mg": ["ginger-tablets-12000mg"],
    "Soya Isoflavones 400 mg": ["soya-isoflavones-capsules"],
    "Royal Jelly 750 mg": ["royal-jelly-capsules-750mg"],
    "Garlic 5000 mg": ["garlic-capsules-5000mg"],
    "Ginkgo Biloba 6000 mg": ["ginkgo-biloba-tablets-6000mg"],
    "Flaxseed Oil 1000 mg": ["flaxseed-oil-capsules-1000mg"],
    "Marine Collagen Powder with Vitamin C": ["marine-collagen-powder"],
    "Salmon Oil (500ml)": ["salmon-oil-for-dogs"],
    "Strawberry Whey Protein Powder": ["strawberry-whey-protein-powder"],
    "Slimming Shake - Vanilla Flavour": ["slimming-shake-vanilla"],
    "Slimming Shake - Strawberry Flavour": ["slimming-shake-strawberry"],
}


def try_shopify_handle(handle):
    """Fetch product image from a Shopify handle."""
    url = f"{SHOPIFY_BASE}/products/{handle}.json"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            product = data.get("product", {})
            images = product.get("images", [])
            if images:
                return images[0].get("src")
    except Exception:
        pass
    return None


# ============================================================================
# Main resolution
# ============================================================================

matched = []
still_unmatched = []

for product in unmatched:
    name = product["name"]
    product_id = product["id"]
    image_url = None

    # Strategy 1: Fuzzy match from cache
    result = fuzzy_match(name)
    if result and result["score"] >= 0.6:
        image_url = result["image"]
        log.info(f"  FUZZY ({result['score']:.0%}): {name} -> {result['title']}")

    # Strategy 2: Try handle guesses
    if not image_url and name in HANDLE_GUESSES:
        for handle in HANDLE_GUESSES[name]:
            time.sleep(2.0)
            image_url = try_shopify_handle(handle)
            if image_url:
                log.info(f"  HANDLE: {name} -> {handle}")
                break

    if image_url:
        matched.append({"id": product_id, "name": name, "imageUrl": image_url})
    else:
        still_unmatched.append({"id": product_id, "name": name})
        log.info(f"  MISS: {name}")

# ============================================================================
# Results
# ============================================================================

log.info(f"\n{'=' * 60}")
log.info("RESULTS")
log.info(f"{'=' * 60}")
log.info(f"Resolved: {len(matched)}")
log.info(f"Still unmatched: {len(still_unmatched)}")

if matched:
    # Save batch updates
    batches = []
    for i in range(0, len(matched), 25):
        batches.append([{"id": p["id"], "imageUrl": p["imageUrl"]} for p in matched[i:i+25]])

    with open("scripts/simply_supplements_remaining_batches.json", "w") as f:
        json.dump(batches, f, indent=2)
    log.info(f"Update batches ({len(batches)}): scripts/simply_supplements_remaining_batches.json")

if still_unmatched:
    with open("scripts/simply_supplements_still_unmatched.json", "w") as f:
        json.dump(still_unmatched, f, indent=2)
    log.info(f"Still unmatched: scripts/simply_supplements_still_unmatched.json")
    log.info(f"\nStill unmatched products:")
    for p in still_unmatched:
        log.info(f"  - {p['name']}")
