#!/usr/bin/env python3
import json, sys
sys.path.insert(0, '/Users/carlosgomez/repos/gomezmera/suppevo-research-agent/scripts')
from nw_image_matcher import find_shopify_match

null_products = [
    {"id": "01c50e07-602e-4dac-84cf-967d50d61b69", "name": "St. John's Wort Herb 700 mg"},
    {"id": "06da58c5-5d55-4943-ad08-805cab085094", "name": "Shiitake Maitake 250 mg"},
    {"id": "089fadab-631b-4bfd-8404-0e9e7ef77562", "name": "Myco Defense"},
    {"id": "08cbc124-30e7-4048-87eb-8860c57323a2", "name": "Echinacea Root Complex 900 mg"},
    {"id": "09077f07-28a7-4c0c-8934-27f4d617716d", "name": "Sambucus Original Syrup for Kids"},
    {"id": "0e005115-3703-49e1-989d-07099265e605", "name": "GS-500 Glucosamine Sulfate"},
    {"id": "0e21bd77-8bd1-40a7-b031-f1a7430fb3dd", "name": "Senna Leaves 1,350 mg"},
    {"id": "0f136e41-8cb8-42d4-8d19-24e1db02450e", "name": "Turmerich Heart"},
    {"id": "0f2802af-46de-49ef-8eb7-9981692b63d3", "name": "GS-750 Glucosamine Sulfate Extra Strength"},
    {"id": "10dacd03-9990-43cc-b05d-0d8618cbd0af", "name": "American Ginseng 1,100 mg"},
    {"id": "1931f6e4-1d28-4ef4-9c40-9d1d6f2614e8", "name": "Prostate"},
    {"id": "1ac02b4b-6646-4034-9c13-fbb14648dcef", "name": "Astragalus Root 1,410 mg"},
    {"id": "1d927b41-774d-4a1a-b3c7-7a7f34fa37e5", "name": "Echinacea Purpurea Herb 400 mg"},
    {"id": "1e61dd0f-2df0-484e-89a1-89dbb8b31148", "name": "Prostol"},
    {"id": "432d2dc3-3ecd-4575-ad47-9458c60aacef", "name": "Krill Oil"},
    {"id": "4513d043-15ff-4583-b103-b20deebb38bf", "name": "DGL Ultra"},
    {"id": "45ae1e46-7580-4b43-aa17-fb48d445b76e", "name": "Vitamin D3"},
    {"id": "4ab641d3-15a9-4f17-b1b2-07e71669ca0a", "name": "Glucomannan 1,995 mg"},
    {"id": "4eba615f-33cc-4a73-bef1-3cec07a66ec3", "name": "Oregano Oil"},
    {"id": "51574927-137e-49ba-ab9b-854935c5c216", "name": "MSM 1000 mg"},
    {"id": "57634151-f77d-4e29-9999-d358830c5117", "name": "Dong Quai Root 1130 mg"},
    {"id": "5f70f661-329c-4acd-b99c-128a4f21bc52", "name": "Charcoal Activated 560 mg"},
    {"id": "6356f10f-f743-4c1a-8b5e-6179ea7579e7", "name": "Licorice Root 900 mg"},
    {"id": "648b34b0-243e-43b7-b47f-f8bf229c08ff", "name": "Willow"},
    {"id": "64cd59da-0294-45b0-a579-0566a331a5f1", "name": "Choline & Inositol"},
]

matched = []
unmatched = []
for p in null_products:
    t, u = find_shopify_match(p["name"])
    if t and u:
        matched.append({"id": p["id"], "imageUrl": u})
    else:
        unmatched.append(p["name"])

print(f"Matched: {len(matched)}, Unmatched: {len(unmatched)}")
for n in unmatched:
    print(f"  XX {n}")

with open("/tmp/nw_batch1.json", "w") as f:
    json.dump(matched, f)
print(f"Batch 1 saved: {len(matched)} products")
