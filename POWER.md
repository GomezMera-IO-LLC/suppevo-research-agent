# Suppevo Biomedical Research Agent

A Kiro Power for biomedical research focused on dietary supplements. Identifies biomarkers, maps ingredients to supplement products, and verifies all scientific evidence through PubMed citations — while ensuring full DSHEA compliance.

## Overview

This power combines MCP servers with direct REST API access to multiple biomedical databases:

1. **suppevo-pubmed-mcp** — Search PubMed, fetch article metadata, verify citations, and find PMIDs.
2. **suppevo-data-mcp** — Access the Suppevo platform for products, ingredients, biomarkers, evidence links, and ingredient intelligence.
3. **DSLD API** (direct REST) — NIH Dietary Supplement Label Database for label-level product data.
4. **ClinicalTrials.gov API** (direct REST) — Clinical trial registry for dose, duration, and study design data.
5. **NIH ODS Fact Sheets** (direct REST) — Authoritative daily values, upper limits, and safety information.

Together they enable a multi-source research workflow where every claim is backed by verifiable references and every ingredient-to-product mapping complies with DSHEA regulations.

## Keywords

biomedical, research, biomarkers, ingredients, evidence, pubmed, supplements, DSHEA, FDA, compliance, citations, nutrition, health claims, structure-function claims, dietary supplements, DSLD, clinical trials, daily values

## Capabilities

### Biomarker Identification
- Search and retrieve biomarker reference ranges
- Identify ingredients that support specific biomarkers
- Cross-reference biomarker data with PubMed literature

### Ingredient Research
- Browse the Suppevo ingredient database
- Get dosing guides, interactions, alternatives, and effectiveness data
- Map ingredients to supplement products
- Verify ingredient safety and efficacy through PubMed

### Evidence Link Verification
- Every evidence link MUST include a valid PubMed reference (PMID)
- Use `verify_citation` to confirm PMID matches the expected title
- Use `search_by_title` to find correct PMIDs for known articles
- Never report an evidence link without a verified PubMed URL

### Label Data Verification (DSLD)
- Cross-reference product labels with NIH DSLD for accuracy
- Verify serving sizes, ingredient amounts, and %DV
- Search by UPC barcode for exact product matching
- CC0 licensed, public domain data (free, no restrictions)

### Clinical Trial Research (ClinicalTrials.gov)
- Search completed interventional studies for dose/duration evidence
- Find active trials to identify evidence gaps
- Extract study population and intervention details
- Support evidence links with NCT numbers

### Reference Values (NIH ODS)
- Get authoritative Daily Values (DV) and Tolerable Upper Limits (UL)
- Access nutrient-specific fact sheets for vitamins and minerals
- Verify deficiency thresholds and safety notes
- Available in Consumer and Health Professional reading levels

### DSHEA Compliance
- All language must comply with the Dietary Supplement Health and Education Act (DSHEA)
- Use structure/function claims only (e.g., "supports immune health")
- Never make disease claims (e.g., "treats diabetes", "cures cancer")
- Always include appropriate qualifiers and disclaimers
- See the `dshea-compliance.md` steering file for detailed guidance

## Workflow

### Research a Biomarker

1. Search Suppevo for the biomarker → get reference ranges and linked ingredients
2. For each linked ingredient, search PubMed for supporting evidence
3. Verify each citation with `verify_citation`
4. Report findings with DSHEA-compliant language and PubMed links

### Add or Verify an Evidence Link

1. Identify the claim (ingredient → biomarker/benefit relationship)
2. Search PubMed for supporting literature
3. Fetch the article abstract to confirm relevance
4. Verify the citation (PMID ↔ title match)
5. Create or update the evidence link in Suppevo with the verified PMID
6. Format the reference as: `https://pubmed.ncbi.nlm.nih.gov/{PMID}/`

### Ingredient-to-Product Mapping

1. Search Suppevo for products containing the target ingredient
2. Verify product claims use DSHEA-compliant language
3. Cross-reference ingredient dosing with PubMed literature
4. Report effective dose ranges supported by evidence

### Product & Brand Data Collection

1. Create/verify brand entity → `find_brand_by_name` or `create_brand`
2. Enumerate products from brand website or retail sources
3. Extract supplement facts (ingredients with amounts, units, %DV)
4. Check for duplicates → `find_product_by_upc` or search by name+brand
5. Create products → `bulk_create_products` (max 25/batch)
6. Upload images → `upload_product_image` presigned URL
7. Link ingredients → `auto_link_ingredients`
8. Validate completeness → `public_get_product_completeness`
9. See `product-collection-workflow.md` steering file for detailed guidance

### Validate Existing Data

1. Run `python scripts/validate_product_data.py` for full datastore audit
2. Review reports: incomplete products, missing images, duplicates, brand gaps
3. Use `--generate-tasks` to get prioritized enrichment work items
4. Fill gaps via `update_product`, `upload_product_image`, `auto_link_ingredients`

## MCP Servers

This power uses two MCP servers:

### pubmed
- **Package:** `suppevo-pubmed-mcp`
- **Tools:** `search_pubmed`, `fetch_article`, `fetch_abstract`, `verify_citation`, `search_by_title`

### suppevo
- **Package:** `suppevo-data-mcp`
- **Tools:** 100+ tools for products, ingredients, biomarkers, evidence links, and more

## Additional Data Sources (Direct REST API)

These sources are accessed via `web_fetch` — no MCP server required.

### DSLD — Dietary Supplement Label Database (NIH)
- **Base URL:** `https://api.ods.od.nih.gov/dsld/v9/`
- **Auth:** None required (optional data.gov API key for higher rate limits)
- **Rate Limit:** 1,000 req/hr (10,000 with API key)
- **License:** CC0 1.0 (public domain)
- **Key Endpoints:** `/label/{id}`, `/browse-products`, `/browse-brands`, `/search-filter`
- **Use for:** Serving sizes, ingredient amounts, %DV, UPC lookup, label claims

### ClinicalTrials.gov
- **Base URL:** `https://clinicaltrials.gov/api/v2/`
- **Auth:** None required
- **Spec:** OpenAPI 3.0 (YAML at `/api/oas/v2`)
- **Key Endpoints:** `/studies` (search), `/studies/{nctId}` (detail)
- **Use for:** Studied doses, durations, populations, outcomes, trial status

### NIH ODS Fact Sheets
- **Base URL:** `https://ods.od.nih.gov/api/`
- **Auth:** None required
- **Format:** XML or HTML per fact sheet
- **URL Pattern:** `?resourcename={Name}&readinglevel=Health%20Professional&outputformat=HTML`
- **Use for:** Daily Values, Upper Limits, deficiency thresholds, drug interactions

### Cochrane Library (via PubMed)
- **Access:** Search PubMed with `"Cochrane Database Syst Rev"[Journal]`
- **Use for:** Systematic reviews and meta-analyses (strongest evidence tier)

## Setup

See the individual server documentation:
- PubMed MCP: Requires optional NCBI API key for higher rate limits
- Suppevo MCP: Requires Suppevo API credentials (JWT token)
- DSLD: No setup required (optional data.gov API key from https://api.data.gov/signup/)
- ClinicalTrials.gov: No setup required
- NIH ODS: No setup required

## Important Rules

1. **Every evidence link must have a verified PubMed reference.** No exceptions.
2. **Never make disease claims.** Only structure/function claims are permitted.
3. **Always verify citations before reporting.** Use `verify_citation` to confirm PMID accuracy.
4. **Use qualifying language.** "May support", "helps maintain", "plays a role in" — not "prevents", "treats", "cures".
5. **Include disclaimers when appropriate.** "These statements have not been evaluated by the FDA. This product is not intended to diagnose, treat, cure, or prevent any disease."
6. **Cross-reference multiple sources.** Use DSLD for label verification, NIH ODS for DV/UL values, and ClinicalTrials.gov for dose/duration data.
7. **Cite data sources.** When reporting DV or UL values, note "Source: NIH ODS". When reporting label data, note "Source: DSLD".
