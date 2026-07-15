---
inclusion: auto
---

# Biomedical Research Workflow

This steering file defines the standard workflow for the Suppevo Biomedical Research Agent. Follow these steps when conducting research on biomarkers, ingredients, or evidence links.

## Core Principles

1. **Evidence-first**: Every claim must be backed by at least one verified PubMed citation.
2. **DSHEA-compliant**: All language must use structure/function claims only.
3. **Verified references**: Every PMID must be confirmed via `verify_citation` before reporting.
4. **Transparent methodology**: Always state what was searched, how many results were found, and what criteria were used for selection.
5. **Multi-source corroboration**: Cross-reference findings across multiple databases (PubMed, DSLD, ClinicalTrials.gov, NIH ODS) when possible.

## Research Sources

The agent has access to multiple research databases, organized by access method:

### Tier 1 — MCP Server Tools (Primary)

| Source | Access | Use Case |
|--------|--------|----------|
| **PubMed** | `search_pubmed`, `fetch_article`, `verify_citation` | Literature search, citation verification |
| **Suppevo** | 100+ tools via suppevo MCP server | Products, ingredients, biomarkers, evidence links |

### Tier 2 — Direct REST APIs (via web_fetch)

| Source | Base URL | Use Case |
|--------|----------|----------|
| **DSLD** | `https://api.ods.od.nih.gov/dsld/v9/` | Label data, serving sizes, DV%, ingredient amounts |
| **ClinicalTrials.gov** | `https://clinicaltrials.gov/api/v2/` | Active trials, dose/duration data, study designs |
| **NIH ODS Fact Sheets** | `https://ods.od.nih.gov/api/` | Authoritative DV, UL, safety, and RDA values |

### Tier 3 — Web Search Fallback

| Source | Access | Use Case |
|--------|--------|----------|
| **Cochrane Reviews** | PubMed search (indexed there) + web search | Systematic reviews, meta-analyses |
| **Examine.com** | Web search/scrape only | Dosing summaries, effect sizes (no API) |

## DSLD API Reference

The NIH Dietary Supplement Label Database provides label-level data for US supplements. **CC0 licensed, public domain.**

### Endpoints

```
GET /label/{dsldId}              — Full label data for a product
GET /browse-products             — Search products by name keyword or letter
GET /browse-brands               — Search brands by name keyword or letter
GET /brand-products              — List products under a brand
GET /ingredient-groups           — Search ingredient groups + factsheet links
GET /search-filter               — Complex search with filters (ingredient, brand, form, etc.)
GET /search-filter-histogram     — Label counts grouped by year
```

### Example Calls

```
# Get label by DSLD ID
https://api.ods.od.nih.gov/dsld/v9/label/82118

# Search products by name
https://api.ods.od.nih.gov/dsld/v9/browse-products/?method=by_keyword&q=Vitamin%20D

# Search by UPC/barcode (wrap in encoded quotes)
https://api.ods.od.nih.gov/dsld/v9/search-filter?q=%2280004843%22

# Get ingredient group info + factsheet links
https://api.ods.od.nih.gov/dsld/v9/ingredient-groups/?method=factsheet&term=Folic%20Acid
```

### Rate Limits
- Without API key: 1,000 requests/hour per IP
- With free data.gov API key: 10,000 requests/hour
- Get a key at: https://api.data.gov/signup/

### When to Use DSLD
- Verifying serving size, servings per container, and supplement form
- Confirming exact ingredient amounts and %DV as printed on labels
- Cross-referencing product claims and label statements
- Finding all products containing a specific ingredient
- Validating UPC barcodes

## ClinicalTrials.gov API Reference

Free REST API (OpenAPI 3.0) for searching clinical trial registrations.

### Endpoints

```
GET /studies                     — Search studies with query parameters
GET /studies/{nctId}             — Get a single study by NCT number
GET /studies/metadata            — Data model field definitions
GET /stats/size                  — Study size statistics
GET /version                     — API version and data timestamp
```

### Example Calls

```
# Search for supplement trials
https://clinicaltrials.gov/api/v2/studies?query.term=tart+cherry+supplementation&filter.overallStatus=COMPLETED

# Get a specific trial
https://clinicaltrials.gov/api/v2/studies/NCT00000419

# Search for dose-finding studies
https://clinicaltrials.gov/api/v2/studies?query.term=magnesium+dose-response&filter.studyType=INTERVENTIONAL
```

### When to Use ClinicalTrials.gov
- Finding studied doses and durations for an ingredient
- Identifying active/completed trials for evidence gaps
- Getting study population details (age, sex, health status)
- Confirming intervention details (form, dose, frequency)
- Finding primary/secondary outcome measures

### Search Tips for Supplements
- Use `filter.studyType=INTERVENTIONAL` to focus on trials (not observational)
- Use `filter.overallStatus=COMPLETED` for finished studies with results
- Combine ingredient name + condition: `"vitamin D" AND "bone density"`
- Add `dietary supplement` to narrow results

## NIH ODS Fact Sheets

Authoritative reference for recommended daily values, tolerable upper limits, and safety data.

### URL Pattern

```
https://ods.od.nih.gov/api/index.aspx?resourcename={Name}&readinglevel={Level}&outputformat={Format}
```

- **resourcename**: Ingredient name (e.g., `VitaminD`, `Magnesium`, `Zinc`, `Folate`, `Omega3FattyAcids`)
- **readinglevel**: `Consumer` | `Health Professional` | `Datos en español`
- **outputformat**: `HTML` | `XML`

### Example Calls

```
# Vitamin D fact sheet (Health Professional, contains DV/UL tables)
https://ods.od.nih.gov/api/index.aspx?resourcename=VitaminD&readinglevel=Health%20Professional&outputformat=HTML

# Magnesium fact sheet (Consumer)
https://ods.od.nih.gov/api/index.aspx?resourcename=Magnesium&readinglevel=Consumer&outputformat=HTML

# Zinc (Health Professional)
https://ods.od.nih.gov/api/index.aspx?resourcename=Zinc&readinglevel=Health%20Professional&outputformat=HTML
```

### Available Fact Sheets (Common Supplements)
Ashwagandha, Biotin, Calcium, Carnitine, Choline, Chromium, Copper, Fluoride, Folate, Iodine, Iron, Magnesium, Manganese, Molybdenum, Niacin, Omega3FattyAcids, PantothenicAcid, Phosphorus, Potassium, Probiotics, Riboflavin, Selenium, Thiamin, VitaminA, VitaminB6, VitaminB12, VitaminC, VitaminD, VitaminE, VitaminK, Zinc

### When to Use NIH ODS
- Getting authoritative Daily Value (DV) and Tolerable Upper Limit (UL) values
- Understanding nutrient deficiency thresholds
- Checking drug-nutrient interactions
- Verifying natural food sources of a nutrient
- Getting evidence summaries for health claims

## Cochrane Reviews (via PubMed)

Cochrane systematic reviews are indexed in PubMed. Search them with:

```
PubMed query: "{ingredient}" AND "Cochrane Database Syst Rev"[Journal]
```

Or use web search: `site:cochranelibrary.com {ingredient} {condition}`

### When to Use Cochrane
- When you need the strongest possible evidence summary (systematic review)
- For comparing multiple RCTs on the same ingredient/outcome
- When evidence quality rating needs to be "Strong"

## Workflow: Biomarker Research

### Step 1 — Identify the Biomarker

Use the Suppevo API to retrieve biomarker details:
- Get reference ranges (normal, optimal, concerning levels)
- Identify currently linked ingredients
- Note any existing evidence links

### Step 2 — Multi-Source Literature Search

For each ingredient linked to the biomarker:

**PubMed (primary):**
1. Search: `"{ingredient}" AND "{biomarker}" AND (supplement OR dietary)`
2. Filter for human clinical trials when possible
3. Prioritize meta-analyses and systematic reviews
4. Include studies from the last 10 years preferentially

**ClinicalTrials.gov (supplementary):**
5. Search for completed interventional studies with the ingredient
6. Extract studied doses, durations, and populations
7. Note primary outcome measures related to the biomarker

**Cochrane (if strong evidence needed):**
8. Search PubMed: `"{ingredient}" AND "Cochrane Database Syst Rev"[Journal]`

**NIH ODS (for DV/UL context):**
9. Fetch the fact sheet for the ingredient (if vitamin/mineral)
10. Extract recommended intake, upper limits, and deficiency thresholds

### Step 3 — Verify Citations

For every article you plan to reference:
1. Use `fetch_article` to get full metadata
2. Use `verify_citation` to confirm PMID ↔ title match
3. Use `fetch_abstract` to confirm the study is relevant to the claim

### Step 4 — Report Findings

Structure your report as:

```
## [Biomarker Name]

**Reference Range:** [values and units]
**Daily Value (NIH ODS):** [if applicable]
**Upper Limit (NIH ODS):** [if applicable]

### Supporting Ingredients

#### [Ingredient Name]
- **Relationship:** [structure/function claim]
- **Evidence:** [brief summary of findings]
- **Study Type:** [meta-analysis / RCT / observational / in-vitro]
- **Reference:** [Title] (PMID: [number]) — https://pubmed.ncbi.nlm.nih.gov/[PMID]/
- **Effective Dose (from study):** [dose used in the cited study]
- **ClinicalTrials.gov:** [NCT number if relevant trial exists]
```

## Workflow: Evidence Link Creation

### Step 1 — Define the Relationship

Clearly state:
- The ingredient
- The biomarker or health benefit
- The proposed relationship (in DSHEA-compliant language)

### Step 2 — Find Supporting Literature

Search strategy:
1. `"{ingredient}" AND "{biomarker/benefit}" AND randomized controlled trial`
2. `"{ingredient}" AND "{biomarker/benefit}" AND meta-analysis`
3. `"{ingredient}" AND "{biomarker/benefit}" AND systematic review`
4. Broaden if needed: `"{ingredient}" AND "{biomarker/benefit}"`

### Step 3 — Evaluate Evidence Quality

Rate each piece of evidence:
- **Strong**: Meta-analysis or systematic review of RCTs
- **Moderate**: Individual RCT with adequate sample size (n > 50)
- **Preliminary**: Observational study, pilot study, or in-vitro research

### Step 4 — Verify and Create

1. Verify each PMID with `verify_citation`
2. Create the evidence link in Suppevo with:
   - Ingredient ID
   - Biomarker/benefit ID
   - PMID
   - Evidence strength rating
   - DSHEA-compliant summary statement

## Workflow: Ingredient-to-Product Mapping

### Step 1 — Research the Ingredient

1. Get ingredient details from Suppevo (dosing guide, interactions, alternatives)
2. Search PubMed for effective dose ranges
3. Note any safety considerations or upper limits
4. **Fetch NIH ODS fact sheet** (if vitamin/mineral) for authoritative DV and UL
5. **Search DSLD** for label data on products containing this ingredient

### Step 2 — Find Products

1. Search Suppevo products containing the ingredient
2. Check ingredient amounts against evidence-based dose ranges
3. Note the form of the ingredient (e.g., magnesium glycinate vs oxide)
4. **Cross-reference with DSLD** to verify label accuracy (serving size, amounts, %DV)

### Step 3 — Compliance Check

For each product:
- Verify label claims use structure/function language only
- Flag any potential disease claims
- Confirm no FDA-prohibited language is present

## Workflow: Label Verification via DSLD

Use this workflow to verify or enrich product data using the DSLD.

### Step 1 — Find the Product in DSLD

Try in this order:
1. Search by UPC: `https://api.ods.od.nih.gov/dsld/v9/search-filter?q=%22{UPC}%22`
2. Search by product name: `https://api.ods.od.nih.gov/dsld/v9/browse-products/?method=by_keyword&q={name}`
3. Search by brand + ingredient: `https://api.ods.od.nih.gov/dsld/v9/search-filter?q={brand}+{ingredient}`

### Step 2 — Extract Label Data

From the DSLD label response, extract:
- Serving size and servings per container
- All ingredients with amounts, units, and %DV
- Label claims and intended target group
- Product form (capsule, tablet, powder, etc.)

### Step 3 — Compare with Suppevo

Cross-reference DSLD data against the Suppevo product record:
- Flag discrepancies in serving size
- Flag discrepancies in ingredient amounts
- Update Suppevo product if DSLD data is more current/accurate

## Workflow: Clinical Trial Research

Use ClinicalTrials.gov to find dose, duration, and study design data.

### Step 1 — Search for Relevant Trials

```
https://clinicaltrials.gov/api/v2/studies?query.term={ingredient}+{condition}&filter.studyType=INTERVENTIONAL&filter.overallStatus=COMPLETED
```

### Step 2 — Extract Study Details

For relevant trials, note:
- Intervention dose and frequency
- Study duration
- Primary and secondary outcome measures
- Sample size and population demographics
- Results (if available)

### Step 3 — Use for Evidence Links

Clinical trial data supports evidence links by providing:
- Studied dose → `studied_dose` field
- Duration → `studied_duration` field
- Sample size → `sample_size` field
- Population → `population_studied` field

## Multi-Source Search Strategy

When researching an ingredient or biomarker, query sources in this order:

1. **Suppevo** (internal data) — Check what we already know
2. **PubMed** (primary literature) — Find and verify scientific evidence
3. **DSLD** (label data) — Verify product-level claims and amounts
4. **ClinicalTrials.gov** (trial registry) — Get dose/duration/population data
5. **NIH ODS** (reference values) — Get authoritative DV, UL, safety data
6. **Cochrane** (via PubMed) — For strongest evidence summaries
7. **Web search** (fallback) — For Examine.com summaries, recent news, emerging research

### Decision Matrix: Which Source to Use

| Question | Primary Source | Secondary Source |
|----------|---------------|------------------|
| What's the effective dose? | PubMed (RCTs) | ClinicalTrials.gov |
| What's the Daily Value? | NIH ODS Fact Sheet | DSLD (label %DV) |
| What's the Upper Limit? | NIH ODS Fact Sheet | PubMed (toxicology) |
| What's on the product label? | DSLD | Suppevo product data |
| Is there a clinical trial? | ClinicalTrials.gov | PubMed |
| What's the best evidence summary? | Cochrane (via PubMed) | PubMed meta-analyses |
| What does the product contain? | Suppevo + DSLD | Brand website |

## Search Query Templates

### Biomarker + Ingredient
```
"{ingredient}" AND "{biomarker}" AND (supplementation OR dietary supplement)
```

### Safety / Interactions
```
"{ingredient}" AND (adverse effects OR drug interactions OR safety) AND supplement
```

### Dose-Response
```
"{ingredient}" AND (dose-response OR dosing OR "dose finding") AND supplement
```

### Meta-analyses
```
"{ingredient}" AND "{benefit}" AND (meta-analysis OR systematic review)
```

## Output Format for Evidence Links

Every evidence link reported must include:

| Field | Required | Description |
|-------|----------|-------------|
| Ingredient | Yes | Name and Suppevo ID |
| Biomarker/Benefit | Yes | Name and Suppevo ID |
| Claim (DSHEA) | Yes | Structure/function statement |
| PMID | Yes | Verified PubMed ID |
| PubMed URL | Yes | `https://pubmed.ncbi.nlm.nih.gov/{PMID}/` |
| Article Title | Yes | Verified via `verify_citation` |
| Study Type | Yes | Meta-analysis, RCT, observational, etc. |
| Evidence Strength | Yes | Strong / Moderate / Preliminary |
| Key Finding | Yes | One-sentence summary of relevant result |
| Dose Used | If available | Dose from the cited study |

## Quality Checklist

Before finalizing any research output, verify:

- [ ] Every PMID has been verified with `verify_citation`
- [ ] Every claim uses DSHEA-compliant structure/function language
- [ ] No disease claims are present anywhere in the output
- [ ] PubMed URLs are correctly formatted
- [ ] Study types are accurately categorized
- [ ] Evidence strength ratings are justified
- [ ] Disclaimers are included where appropriate
- [ ] DV and UL values are sourced from NIH ODS (not estimated)
- [ ] Label data cross-referenced with DSLD when available
- [ ] Clinical trial doses noted with NCT numbers when applicable
