## Summary

`update_ingredient` returns `500 INTERNAL_ERROR` for any ingredient that has had evidence links created via `create_evidence_link`. The issue appears to be a version/state conflict: evidence link creation modifies derived fields on the ingredient record (`biomarker_ids`, `evidence_link_count`) without properly updating the record's version marker (`updated_at`), causing subsequent explicit updates to fail.

## Steps to Reproduce

1. Take an ingredient that currently has no evidence links (e.g., Tart Cherry `220e7349-e75f-4a98-8825-2ac6e01c2c12`)
2. Create an evidence link referencing that ingredient via `create_evidence_link`
3. Confirm the evidence link was created successfully
4. Attempt to update the ingredient via `update_ingredient` (any field — even `short_description` or `name`)
5. **Result:** `500 INTERNAL_ERROR`

## Affected Ingredients (confirmed)

| Ingredient | ID | Product Count | Evidence Links | Update Result |
|-----------|-----|:---:|:---:|:---:|
| Tart Cherry | `220e7349-e75f-4a98-8825-2ac6e01c2c12` | 14 | 1 | ❌ 500 |
| Curcumin | `a1dece07-405f-4977-8fe8-597339651f10` | 50 | 3 | ❌ 500 |
| Quercetin | `3cf7164c-fe28-4cfd-a2f2-95112f30159e` | 1,058 | 8 | ❌ 500 |
| L. acidophilus | `5766fb11-5edc-4b7d-b97b-cf955dc5c50e` | 126 | 7 | ❌ 500 |
| Vitamin C | `897a1cb8-32bf-4923-adc8-47f13804761d` | 6,506 | 2+ | ❌ 500 |

## Working Ingredients (for comparison)

| Ingredient | ID | Product Count | Evidence Links | Update Result |
|-----------|-----|:---:|:---:|:---:|
| Resveratrol | `61778152-3176-4bc9-ba16-4125b2bc2e66` | 0 | 1 | ✅ |
| NAC | `736811b0-e511-4bf5-8276-500d97c70338` | 77 | 3 | ✅ |
| Folic Acid | `5d077f55-93b1-4cb8-8704-867045ec3e61` | 4,097 | 1 | ✅ |
| Inulin | `4c6f6b87-2397-46a4-afeb-56796823664b` | 83 | 1 | ✅ |

## Root Cause Analysis

**The issue is NOT product count** — Folic Acid has 4,097 products and updates fine.

**Likely cause:** `create_evidence_link` modifies the ingredient record's `biomarker_ids` array and `evidence_link_count` counter **without atomically updating `updated_at`** (or a version field used for optimistic concurrency). When `update_ingredient` subsequently runs, it encounters a stale version check (likely DynamoDB `ConditionCheckFailedException`) because:

1. Evidence link creation writes to `biomarker_ids` on the ingredient → record state changes
2. `updated_at` is NOT bumped (still shows old May dates on affected records)
3. `update_ingredient` reads the record, attempts conditional write, fails because the record was modified out-of-band

**Key evidence:**
- All failing ingredients had evidence links created in the same session (2026-06-18)
- Their `updated_at` timestamps still show May dates despite `biomarker_ids` being populated today
- Resveratrol works because we called `update_ingredient` on it *immediately* after creating the evidence link (before any stale state)
- NAC and Folic Acid work because their evidence link creation properly triggered an update (or they had no prior version conflict)

## Expected Behavior

`update_ingredient` should succeed regardless of whether `create_evidence_link` was called previously for that ingredient.

## Suggested Fix

1. **Option A (preferred):** In `create_evidence_link`, when updating the ingredient's `biomarker_ids` and `evidence_link_count`, also atomically update `updated_at` (and any version field) so the record stays consistent.

2. **Option B:** Remove the conditional/version check from `update_ingredient` writes, or use `UpdateExpression` ADD/SET operations that don't depend on reading the full current state.

3. **Option C:** Use DynamoDB `UpdateExpression` with `SET` for the derived fields in `create_evidence_link` instead of a full item put/replace, avoiding version conflicts entirely.

## Environment

- API accessed via suppevo-data-mcp (MCP server)
- DynamoDB backend (inferred from error pattern)
- Date of occurrence: 2026-06-18

## Additional Context

This was discovered while adding XO mechanism descriptions to ingredients linked to the Uric Acid biomarker. The `bulk_create_evidence_links` endpoint also returns `Internal error processing item` for all items, which may be the same underlying issue at batch scale.

## Also Affected: `bulk_create_evidence_links`

The `bulk_create_evidence_links` endpoint returns `Internal error processing item` for every item in the batch, even when individual `create_evidence_link` calls succeed for the same data. This may share the same root cause (concurrent writes to ingredient records during batch processing).
