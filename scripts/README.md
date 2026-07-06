# Suppevo Data Quality Scripts

## Overview

These scripts audit and validate data in the Suppevo datastore. They use the public API for reading and MCP servers for authenticated operations (create, update, delete).

| Script | Purpose |
|--------|---------|
| `validate_product_data.py` | Audit products, brands, ingredients for completeness and duplicates |
| `verify_evidence_links.py` | Verify PubMed citations on evidence links |

---

## validate_product_data.py

Audits the Suppevo datastore for product completeness, brand coverage gaps, unlinked ingredients, and duplicates.

### What it does

1. Fetches all brands → checks completeness (website, logo, location, etc.)
2. Fetches all products → scores each on completeness (ingredients, image, UPC, etc.)
3. Detects duplicate products (same UPC or same name+brand)
4. Checks for unlinked ingredient names
5. Generates JSON reports for each issue category
6. Optionally produces a prioritized enrichment task list

### Prerequisites

Python 3.8+ (no external dependencies — uses only stdlib).

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPPEVO_API_BASE` | No | API base URL (default: `https://api.dev.suppevo.com`) |

### Usage

```bash
# Full audit (all brands and products):
python scripts/validate_product_data.py

# Audit a specific brand:
python scripts/validate_product_data.py --brand "Thorne"

# Only products below 80% completeness (default threshold):
python scripts/validate_product_data.py --min-score 80

# Stricter threshold:
python scripts/validate_product_data.py --min-score 90

# Check for duplicates only:
python scripts/validate_product_data.py --duplicates-only

# List products missing images:
python scripts/validate_product_data.py --missing-images

# Generate prioritized enrichment task list:
python scripts/validate_product_data.py --generate-tasks
```

### Output Files

| File | Contents |
|------|----------|
| `scripts/validation_report.json` | Summary statistics |
| `scripts/incomplete_products.json` | Products below threshold with issue list |
| `scripts/missing_images.json` | Products without images |
| `scripts/duplicates.json` | Potential duplicate groups |
| `scripts/brand_gaps.json` | Brands with missing fields |
| `scripts/enrichment_tasks.json` | Prioritized tasks (with `--generate-tasks`) |

### Completeness Scoring

Products are scored on these weighted fields:

| Field | Weight |
|-------|--------|
| Name + Brand | 20% |
| Category + Form | 10% |
| Ingredients with amounts | 25% |
| Image | 15% |
| Serving size + per container | 10% |
| UPC or ASIN | 10% |
| Dosage + Description | 10% |

### Enrichment Task Priority

When using `--generate-tasks`, tasks are prioritized:
1. **P1**: Products with no ingredients (critical — useless without supplement facts)
2. **P2**: Products with no image (needed for user experience)
3. **P3**: Products missing UPC/ASIN (needed for deduplication)

---

## verify_evidence_links.py

## verify_evidence_links.py

Automated PubMed citation verification for all evidence links in the Suppevo database.

### What it does

1. Fetches all biomarkers with linked ingredients from the Suppevo public API
2. For each ingredient, retrieves all evidence links
3. Verifies each citation's PMID against PubMed using NCBI E-utilities
4. Compares the expected title to the actual title at that PMID
5. Categorizes links as: ✅ verified, ⚠️ borderline (needs review), or ❌ invalid
6. Generates a JSON report for review
7. Optionally deletes invalid links after user confirmation

### Prerequisites

Python 3.8+ (no external dependencies — uses only stdlib).

The script uses:
- NCBI E-utilities (direct HTTP) for PubMed verification
- Suppevo public API (direct HTTP) for reading evidence links
- `suppevo-data-mcp` (via `uvx`) for deletions — handles authentication automatically

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NCBI_API_KEY` | No | NCBI API key for 10 req/sec (default: 3 req/sec without key) |

No `SUPPEVO_AUTH_TOKEN` needed — the MCP server handles authentication for deletion operations.

### Usage

```bash
# Step 1: Run verification (dry run — no deletions)
python scripts/verify_evidence_links.py

# Step 2: Review the report
cat scripts/verification_report.json | python -m json.tool

# Step 3: Delete invalid links (uses MCP server for auth, prompts for confirmation)
python scripts/verify_evidence_links.py --delete

# Resume from a specific biomarker (if interrupted)
python scripts/verify_evidence_links.py --start-from hemoglobin-a1c

# Skip already-verified ingredients from a previous run
python scripts/verify_evidence_links.py --skip-file scripts/verified_ingredients.txt

# With NCBI API key for faster verification
NCBI_API_KEY="your-key" python scripts/verify_evidence_links.py
```

### Report Format

The script generates `scripts/verification_report.json` with:

```json
{
  "summary": {
    "total_scanned": 535,
    "verified_correct": 200,
    "to_delete": 280,
    "borderline_review": 15,
    "errors": 5
  },
  "to_delete": [...],      // Links with fabricated citations
  "borderline": [...],     // Links needing manual review (0.3-0.5 similarity)
  "verified": [...]        // Links with confirmed valid PMIDs
}
```

### Verification Logic

- **Similarity ≥ 0.5**: Verified correct (same paper, minor title differences)
- **Similarity 0.3-0.5**: Borderline — needs manual review (could be same paper with different title format)
- **Similarity < 0.3**: Invalid — PMID points to completely unrelated paper

### Rate Limiting

- **With NCBI API key**: 0.35s between requests (~170 verifications/min)
- **Without API key**: 1.0s between requests (~60 verifications/min)
- Full scan of ~535 links takes approximately 5-10 minutes with an API key

### Notes

- The script deduplicates ingredients (each ingredient is only checked once even if it appears under multiple biomarkers)
- Progress is logged in real-time
- The `verified_ingredients.txt` output file can be used as a `--skip-file` for subsequent runs
- Borderline results should be manually reviewed before deciding keep/delete
