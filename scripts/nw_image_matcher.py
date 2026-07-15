#!/usr/bin/env python3
"""Nature's Way product image matching - optimized version."""
import json
import re

with open('/tmp/nw_image_lookup.json', 'r') as f:
    shopify_lookup = json.load(f)

# Pre-build filtered lookup
FILTERED = {}
for title, url in shopify_lookup.items():
    if 'short expiration' in title or 'last chance' in title:
        continue
    if 'sample' in title or 'bundle' in title:
        continue
    norm = title.replace('\u2019', "'").replace('\u2018', "'")
    FILTERED[norm] = url

FULL = {t.replace('\u2019', "'").replace('\u2018', "'"): u for t, u in shopify_lookup.items()}

SPECIAL = {
    'sambucus original syrup for kids': 'sambucus immune elderberry syrup for kids',
    'sambucus original syrup': 'sambucus immune elderberry syrup',
    'cell formula': 'cell forte\u00ae ip-6 & inositol',
    'myco defense': '5-mushroom blend',
    'gs-500 glucosamine sulfate': 'gs-500\u2122 glucosamine sulfate',
    'gs-750 glucosamine sulfate extra strength': 'gs-500\u2122 glucosamine sulfate',
    'tart cherry ultra gummies 1200 mg cherry flavor': 'tart cherry ultra gummies',
    'turmerich heart': 'turmeric', 'tumerich joint': 'turmeric',
    'echinacea root complex 900 mg': 'echinacea',
    'echinacea purpurea herb 400 mg': 'echinacea',
    'fortify gummy probiotic 6 billion berry flavored': 'fortify\u00ae 30 billion daily probiotic',
    'ostivone ipriflavone': 'osteoprime\u00ae',
    'prostate': 'saw palmetto', 'prostol': 'saw palmetto',
    'prostate advantage': 'saw palmetto',
    'senna leaves 1,350 mg': 'senna leaves',
    'shiitake maitake 250 mg': '5-mushroom blend',
    'american ginseng 1,100 mg': 'asian ginseng',
    'chlorofresh mint flavored': 'chlorofresh\u00ae liquid chlorophyll',
    'charcoal activated 560 mg': 'activated charcoal',
    'curica': 'theracurmin\u00ae hp',
    'curica turmeric 600 mg': 'theracurmin\u00ae hp',
    'curica turmeric drops orange flavored': 'theracurmin\u00ae hp',
    'forskohlii extract': 'forskohlii standardized extract',
}

HERBS = sorted([
    'phosphatidylserine', 'alpha lipoic', 'saw palmetto', 'black cohosh',
    'dong quai', 'milk thistle', 'slippery elm', 'gotu kola',
    'wild yam', 'red clover', 'uva ursi', 'black walnut', 'bladderwrack',
    'beet root', 'niacinamide', 'grape seed', 'horse chestnut',
    'primadophilus', 'weight manager', 'vitamin d3', 'vitamin c',
    'vitamin a', 'vitamin e', 'vitamin b12', 'vitamin b6',
    'evening primrose', 'ashwagandha', 'turmeric', 'echinacea',
    'valerian', 'ginger', 'ginkgo', 'garlic', 'cinnamon',
    'berberine', 'rhodiola', 'saffron', 'moringa', 'spirulina',
    'chlorella', 'kelp', 'neem', 'boswellia', 'feverfew',
    'chamomile', 'bilberry', 'artichoke', 'alfalfa', 'astragalus',
    'burdock', 'cayenne', 'dandelion', 'fenugreek', 'goldenseal',
    'hawthorn', 'kudzu', 'nettle', 'oregano', 'parsley',
    'rosemary', 'selenium', 'skullcap', 'lutein', 'folate',
    'potassium', 'nac', 'gaba', 'choline', 'inositol',
    'riboflavin', 'niacin', 'melatonin', 'resveratrol', 'quercetin',
    'coq10', 'glucomannan', 'gymnema', 'schisandra', 'vitex',
    'borage', 'marshmallow', 'elderberry', 'sambucus', 'cranberry',
    'maca', 'olive', 'flax', 'krill', 'coconut',
    'calcium', 'magnesium', 'zinc', 'iron', 'msm',
    'fortify', 'alive!', 'chlorofresh', 'biotin', 'horsetail',
    'licorice', 'hops', 'willow', 'dgl',
], key=len, reverse=True)


def find_shopify_match(suppevo_name):
    sl = suppevo_name.lower().strip().replace('\u2019', "'").replace('\u2018', "'")

    # Direct match
    if sl in FULL:
        return sl, FULL[sl]

    # Containment
    for st, url in FILTERED.items():
        if sl in st or st in sl:
            return st, url

    # Special mappings
    if sl in SPECIAL:
        mapped = SPECIAL[sl].replace('\u2019', "'").replace('\u2018', "'")
        if mapped in FILTERED:
            return mapped, FILTERED[mapped]
        # Try original lookup
        orig = SPECIAL[sl.replace("'", '\u2019')]
        if SPECIAL.get(sl) in shopify_lookup:
            return SPECIAL[sl], shopify_lookup[SPECIAL[sl]]
        return None, None

    # Strip dosage and retry containment
    stripped = re.sub(r'\s*\d[\d,]*\s*(mg|mcg|iu|billion|dfe)\b', '', sl).strip()
    if stripped != sl and len(stripped) > 2:
        for st, url in FILTERED.items():
            if stripped in st or st in stripped:
                return st, url

    # Herb keyword match
    for herb in HERBS:
        if herb in sl:
            for st, url in FILTERED.items():
                if herb in st:
                    return st, url
            break

    # Word overlap
    stop = {'for', 'with', 'the', 'and', 'of', 'in', 'a', 'an', 'mg', 'mcg', 'billion'}
    sw = set(re.sub(r'[^a-z0-9\s]', ' ', sl).split()) - stop
    if len(sw) < 2:
        return None, None
    best = None
    best_score = 0
    for st, url in FILTERED.items():
        words = set(re.sub(r'[^a-z0-9\s]', ' ', st).split()) - stop
        score = len(sw & words)
        if score > best_score and score >= 2:
            best_score = score
            best = (st, url)
    return best if best else (None, None)


if __name__ == '__main__':
    tests = [
        "St. John's Wort Herb 700 mg", "Astragalus Root 1,410 mg",
        "Sambucus Original Syrup for Kids", "Organic Hemp Mint Flavored",
        "Forskohlii", "American Ginseng 1,100 mg", "Turmerich Heart",
        "Krill Oil", "DGL Ultra", "Oregano Oil", "Cayenne Fruit",
    ]
    m = 0
    for name in tests:
        t, u = find_shopify_match(name)
        if t:
            m += 1
        print(f"  {'OK' if t else 'XX'} {name} -> {t or 'NO MATCH'}")
    print(f"\nMatched: {m}/{len(tests)}")
