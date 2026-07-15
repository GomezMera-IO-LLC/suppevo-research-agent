#!/usr/bin/env python3
"""Filter bad fuzzy matches and output clean batch for Simply Supplements."""
import json

batches = json.load(open("scripts/simply_supplements_remaining_batches.json"))
all_matched = batches[0]  # single batch of 20

# IDs to EXCLUDE (wrong fuzzy matches)
bad_ids = {
    "14036530-5985-4bf3-8725-3d640170a23b",  # Pure Inulin -> creatine powder (WRONG)
    "c752aa5d-5e9a-47fe-a4e8-90afa05a250d",  # Selenium with Vit ACE -> multivitamins (WRONG)
    "459fde0b-0b97-4ec4-b3b9-542e49bba101",  # CoQ10 100mg -> CoQ10 300mg image (acceptable but different dose)
}

good = [p for p in all_matched if p["id"] not in bad_ids]
print(f"Total matched: {len(all_matched)}")
print(f"Filtered out: {len(all_matched) - len(good)}")
print(f"Good to push: {len(good)}")

# Save clean batch
with open("scripts/simply_supplements_final_batch.json", "w") as f:
    json.dump([good], f, indent=2)
print("Saved to scripts/simply_supplements_final_batch.json")
print(json.dumps(good))
