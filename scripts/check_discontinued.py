#!/usr/bin/env python3
"""Check which remaining products without images are discontinued."""
import json
import urllib.request
import time

SHOPIFY_BASE = "https://www.bulksupplements.com"

# The 12 remaining products without images
REMAINING = [
    {"id": "05d412e9-37f2-4732-ae28-3b1eb5c24605", "name": "Acerola Extract (25% Vitamin C)"},
    {"id": "067a5380-8f13-4c30-b725-83f8b70b5e44", "name": "Cayenne Extract"},
    {"id": "a8e7618e-d29c-4ad8-b58f-b0aaf1af5cbb", "name": "Cayenne Extract (500 mg)"},
    {"id": "9b2e8113-9604-4f6e-bd5d-dae41c3c1049", "name": "Creatinol o-Phosphate"},
    {"id": "9334df5f-a7e5-4a0f-8d21-71b754c97581", "name": "Gamma Aminobutyric Acid"},
    {"id": "4065721c-599d-4899-bc3e-e0d1152121b9", "name": "Gamma Aminobutyric Acid 600 mg"},
    {"id": "05a52b9a-538d-4189-9c8c-8f060884e950", "name": "Galla Chinensis Extract"},
    {"id": "1375ef47-b3e1-49a5-ac54-37fbd9275314", "name": "Konjac Root Extract"},
    {"id": "568bbf85-7c92-40c8-a8e5-fa7eaa93a960", "name": "L-Ornithine Alpha-Ketoglutarate"},
    {"id": "80b5c970-de84-444e-a85b-62402a0b580d", "name": "Lemon Powder"},
    {"id": "0c98cbaa-4d35-4799-93d4-46d0147dfc42", "name": "Pomegranate Extract 40% Ellagic Acid"},
    {"id": "269e1c09-d526-4b49-b674-1ecba426afe5", "name": "Sulbutiamine"},
]

# Try various handle patterns for each
HANDLE_ATTEMPTS = {
    "Acerola Extract (25% Vitamin C)": ["acerola-extract", "acerola-cherry-extract-powder", "acerola-extract-powder"],
    "Cayenne Extract": ["cayenne-extract", "cayenne-pepper-extract-powder", "cayenne-extract-powder", "cayenne-pepper-powder"],
    "Cayenne Extract (500 mg)": ["cayenne-extract", "cayenne-pepper-extract-powder", "cayenne-pills"],
    "Creatinol o-Phosphate": ["creatinol-o-phosphate", "creatinol-o-phosphate-powder"],
    "Gamma Aminobutyric Acid": ["gaba-gamma-aminobutyric-acid-powder", "gaba-powder", "gaba"],
    "Gamma Aminobutyric Acid 600 mg": ["gaba-gamma-aminobutyric-acid-powder", "gaba-capsules", "gaba-pills"],
    "Galla Chinensis Extract": ["galla-chinensis-extract", "chinese-gallnut-extract"],
    "Konjac Root Extract": ["konjac-root-extract-powder", "glucomannan-konjac-root", "konjac-root-powder"],
    "L-Ornithine Alpha-Ketoglutarate": ["l-ornithine-alpha-ketoglutarate", "ornithine-akg", "okg-powder"],
    "Lemon Powder": ["lemon-powder", "lemon-juice-powder", "organic-lemon-powder"],
    "Pomegranate Extract 40% Ellagic Acid": ["pomegranate-extract-powder", "pomegranate-extract", "ellagic-acid-powder"],
    "Sulbutiamine": ["sulbutiamine-powder", "sulbutiamine"],
}


def try_handle(handle):
    """Check if a Shopify handle exists and has images."""
    url = f"{SHOPIFY_BASE}/products/{handle}.json"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            product = data.get("product", {})
            images = product.get("images", [])
            if images:
                return images[0].get("src")
    except Exception:
        pass
    return None


found = []
not_found = []

for product in REMAINING:
    name = product["name"]
    handles = HANDLE_ATTEMPTS.get(name, [])
    image_url = None

    for handle in handles:
        time.sleep(2.5)
        image_url = try_handle(handle)
        if image_url:
            print(f"  FOUND: {name} -> {handle}")
            found.append({"id": product["id"], "name": name, "imageUrl": image_url})
            break

    if not image_url:
        print(f"  DISCONTINUED: {name} ({product['id']})")
        not_found.append(product)

print(f"\nResults: {len(found)} found, {len(not_found)} discontinued")
print(f"\nDiscontinued product IDs to delete:")
for p in not_found:
    print(f"  {p['id']}  # {p['name']}")

# Save results
output = {"found": found, "discontinued": not_found}
with open("scripts/bulksupplements_discontinued.json", "w") as f:
    json.dump(output, f, indent=2)
