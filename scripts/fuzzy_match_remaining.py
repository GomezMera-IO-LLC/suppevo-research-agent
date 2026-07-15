#!/usr/bin/env python3
"""Fuzzy match remaining BulkSupplements products using Shopify cache."""
import json

missing = json.load(open("scripts/bulksupplements_missing_images.json"))
cache = json.load(open("scripts/bulksupplements_shopify_cache.json"))

# Build index
shopify_index = []
for p in cache:
    title = p.get("title", "")
    images = p.get("images", [])
    img = images[0]["src"] if images else None
    if img:
        shopify_index.append((title.lower(), p["handle"], img))

missing_products = missing["products_without_images"]
matches = []

for product in missing_products:
    name = product["name"].lower()
    name_words = set(name.replace("-", " ").replace("(", "").replace(")", "").replace("%", "").split())
    # Remove common noise words
    for w in ["mg", "500", "600", "400", "200", "1200", "50", "60", "7", "5:1", "30", "p.e"]:
        name_words.discard(w)

    best_match = None
    best_score = 0

    for shop_title, handle, img in shopify_index:
        shop_words = set(shop_title.replace("-", " ").replace("(", "").replace(")", "").replace("%", "").split())
        overlap = name_words & shop_words
        if len(name_words) > 0:
            score = len(overlap) / len(name_words)
        else:
            score = 0
        if score > best_score and score >= 0.5:
            best_score = score
            best_match = (handle, img, shop_title)

    if best_match:
        matches.append({
            "id": product["id"],
            "name": product["name"],
            "handle": best_match[0],
            "imageUrl": best_match[1],
            "shopify_title": best_match[2],
            "score": best_score,
        })

print(f"Fuzzy matched: {len(matches)} of {len(missing_products)}")
print()
for m in sorted(matches, key=lambda x: -x["score"]):
    print(f"  {m['score']:.0%} | {m['name']} -> {m['shopify_title']}")

# Save high-confidence matches
update_products = [{"id": m["id"], "imageUrl": m["imageUrl"]} for m in matches if m["score"] >= 0.5]
print(f"\nMatches (>=50%): {len(update_products)}")

with open("scripts/bulksupplements_fuzzy_batch.json", "w") as f:
    json.dump(update_products, f, indent=2)
print("Saved to scripts/bulksupplements_fuzzy_batch.json")
