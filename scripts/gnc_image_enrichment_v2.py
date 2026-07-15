#!/usr/bin/env python3
"""
GNC Preventive Nutrition Image Enrichment v2

Uses curl to fetch GNC product pages and extract og:image URLs.
GNC uses Salesforce Commerce Cloud (Demandware).
"""
import json
import logging
import re
import subprocess
import time
import urllib.request
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

BRAND_ID = "796e891f-a29e-4c28-87b9-bd7b7d6091e4"
SUPPEVO_API_BASE = "https://api.dev.suppevo.com"

# Known GNC product URLs (from search results and manual research)
# Pattern: https://www.gnc.com/{category}/{sku}.html
KNOWN_SKUS = {
    "Healthy Blood Sugar Formula": "715122",
    "Blood Pressure Formula": "090708",
    "Liver Formula": "099817",
    "Cleansing Formula": "214111",
    "CoQ-10 50 mg": "774424",
    "CoQ-10 100 mg": "083212",
    "CoQ-10 400 mg": "082574",
    "Super CoQ-10 100 mg": "079147",
    "Memorall": "066581",
    "Sleep Soundly Advanced": "083991",
    "Tri-Sleep": "214661",
    "Phytosterols 800 mg": "109943",
    "Pycnogenol 100 mg": "100834",
    "Lycopene": "062101",
    "Multi-Oil": "073381",
    "Multi-Enzyme Formula": "079802",
    "Colon Care": "046866",
    "Quercetin 1000 mg": "102074",
    "Ocular Formula": "058388",
    "Eye Health Formula": "205355",
    "Energy Enhancing Formula Refreshing Citrus": "119430",
    "Healthy Digestion Formula Refreshing Citrus": "119270",
    "Nattokinase Heart Health Formula": "102128",
}

# Get products
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


def fetch_og_image_curl(url):
    """Use curl to fetch a page and extract og:image."""
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-redirs", "5", "-H", "User-Agent: Mozilla/5.0", url],
            capture_output=True, text=True, timeout=15
        )
        html = result.stdout
        # Extract og:image
        match = re.search(r'property="og:image"\s+content="([^"]+)"', html)
        if match:
            img = match.group(1)
            # Clean up HTML entities
            img = img.replace("&amp;", "&")
            # URL encode spaces
            img = img.replace(" ", "%20")
            return img
    except Exception as e:
        log.warning(f"  curl error: {e}")
    return None


def find_product_url(product_name, upc):
    """Try to find the GNC product page URL."""
    # Try known SKU
    sku = KNOWN_SKUS.get(product_name)
    if sku:
        # Try various category paths
        for cat in ["other-supplements", "antioxidants", "coenzyme-q10",
                    "digestive-supplements", "sleep-supplements", "heart-supplements",
                    "preventive-nutrition", "brain-supplements", "eye-supplements",
                    "stress-supplements", "china-products", "probiotics"]:
            url = f"https://www.gnc.com/{cat}/{sku}.html"
            return url

    # Try UPC-derived SKU (last 6 digits of UPC is often the GNC SKU)
    if upc and len(upc) >= 6:
        # GNC UPCs: 048107{sku} -> sku is the last 6 digits
        if upc.startswith("048107"):
            sku = upc[6:]
            return f"https://www.gnc.com/other-supplements/{sku}.html"

    return None


# Process products
matched = []
failed = []

for i, product in enumerate(no_image):
    name = product.get("name", "")
    upc = product.get("upc", "")
    pid = product["id"]

    product_url = find_product_url(name, upc)

    if product_url:
        time.sleep(1.5)
        image_url = fetch_og_image_curl(product_url)

        if image_url and "demandware" in image_url:
            matched.append({"id": pid, "name": name, "imageUrl": image_url})
            log.info(f"  [{i+1}/{len(no_image)}] ✅ {name}")
        else:
            # Try alternate category
            for cat in ["preventive-nutrition", "antioxidants", "other-supplements",
                        "digestive-supplements", "heart-supplements"]:
                alt_url = product_url.replace(product_url.split("/")[3], cat)
                time.sleep(1.0)
                image_url = fetch_og_image_curl(alt_url)
                if image_url and "demandware" in image_url:
                    matched.append({"id": pid, "name": name, "imageUrl": image_url})
                    log.info(f"  [{i+1}/{len(no_image)}] ✅ {name} (alt)")
                    break
            else:
                failed.append({"id": pid, "name": name})
                log.info(f"  [{i+1}/{len(no_image)}] ❌ {name}")
    else:
        failed.append({"id": pid, "name": name})
        log.info(f"  [{i+1}/{len(no_image)}] ❌ {name} (no URL)")

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
    log.info(f"Update batches ({len(batches)}): scripts/gnc_update_batches.json")

if failed:
    with open("scripts/gnc_failed.json", "w") as f:
        json.dump(failed, f, indent=2)
    log.info(f"Failed: scripts/gnc_failed.json")
    for p in failed:
        log.info(f"  - {p['name']}")
