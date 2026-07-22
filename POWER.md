# Suppevo Biomedical Research Agent

A Kiro Power for biomedical research focused on dietary supplements. Identifies biomarkers, maps ingredients to supplement products, and verifies all scientific evidence through PubMed citations — while ensuring full DSHEA compliance.

## Overview

This power combines MCP servers with direct REST API access to multiple biomedical databases:

1. **suppevo-pubmed-mcp** — Search PubMed, fetch article metadata, verify citations, and find PMIDs.
2. **suppevo-data-mcp** — Access the Suppevo platform for products, ingredients, biomarkers, evidence links, and ingredient intelligence.
3. **wigolo** — Local-first web intelligence: search, fetch, crawl, extract, cache, and research. No API keys needed. **Primary web tool.**
4. **firecrawl-mcp** — Cloud scraping API with anti-bot bypass. **Fallback only** — use when Wigolo is blocked.
5. **DSLD API** (direct REST) — NIH Dietary Supplement Label Database for label-level product data.
6. **ClinicalTrials.gov API** (direct REST) — Clinical trial registry for dose, duration, and study design data.
7. **NIH ODS Fact Sheets** (direct REST) — Authoritative daily values, upper limits, and safety information.

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

This power uses three MCP servers:

### pubmed
- **Package:** `suppevo-pubmed-mcp`
- **Tools:** `search_pubmed`, `fetch_article`, `fetch_abstract`, `verify_citation`, `search_by_title`

#### Installation

Add to `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "pubmed": {
      "command": "uvx",
      "args": ["suppevo-pubmed-mcp@latest"],
      "env": {
        "NCBI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### Getting an NCBI API Key (optional but recommended)

An API key increases your rate limit from 3 requests/sec to 10 requests/sec.

1. Create a free account at https://www.ncbi.nlm.nih.gov/account/
2. Go to https://www.ncbi.nlm.nih.gov/account/settings/
3. Click "Create an API Key" under the API Key Management section
4. Copy the key and add it to your `~/.zshenv` as `export NCBI_API_KEY="your-key"`

Without an API key the server still works, just at a lower rate limit.

#### Tool Parameters

**search_pubmed**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | yes | — | PubMed search query |
| `max_results` | integer | no | 10 | Maximum results to return (1–50) |

**fetch_article**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pmid` | string | yes | PubMed ID (e.g. "30415628") |

**fetch_abstract**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pmid` | string | yes | PubMed ID |

**verify_citation**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pmid` | string | yes | PubMed ID to verify |
| `expected_title` | string | yes | The title you expect this PMID to correspond to |

**search_by_title**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | yes | The article title to search for |

#### Advanced Query Syntax

```
# Field-specific search
curcumin AND inflammation[Title]

# Author search
Prasad AS[Author] AND zinc

# Date range
omega-3 AND cardiovascular[Title] AND 2020:2024[dp]

# MeSH terms
"Zinc/therapeutic use"[MeSH]

# Cochrane systematic reviews
"Cochrane Database Syst Rev"[Journal] AND vitamin D
```

#### Troubleshooting

- **Server fails to connect:** Ensure `uvx` is installed (`uv --version`). Clear cache if upgraded: `uv cache clean suppevo-pubmed-mcp`
- **Rate limit errors:** Add `NCBI_API_KEY` to your environment
- **No results:** Try broader terms. Field tags are case-sensitive. Use `search_by_title` for exact title lookups.

#### Links

- PyPI: https://pypi.org/project/suppevo-pubmed-mcp/
- GitHub: https://github.com/GomezMera-IO-LLC/suppevo-pubmed-mcp
- NCBI E-utilities docs: https://www.ncbi.nlm.nih.gov/books/NBK25500/

### suppevo
- **Package:** `suppevo-mcp`
- **Tools:** 100+ tools for products, ingredients, biomarkers, evidence links, and more

#### Installation

Add to `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "suppevo": {
      "command": "python",
      "args": ["-m","suppevo_mcp.server"]
    }
  }
}
```

#### Credentials

Add your Suppevo credentials to `~/.zshenv`:

```bash
export SUPPEVO_API_TOKEN="your-jwt-token-here"
export SUPPEVO_REFRESH_TOKEN="your-refresh-token-here"
export SUPPEVO_CLIENT_ID="your-cognito-client-id"
export SUPPEVO_API_BASE_URL="https://api.dev.suppevo.com/"
export SUPPEVO_COGNITO_REGION="us-east-1"
```

The server auto-refreshes expired tokens if `SUPPEVO_REFRESH_TOKEN` and `SUPPEVO_CLIENT_ID` are provided.

#### Tool Groups

**User Tools (authenticated)**

| Tool Group | What you can do |
|------------|-----------------|
| **Profile** | Get/create/update your user profile and preferences |
| **Supplements** | Add, view, update, remove supplements from your tracking list |
| **Schedules** | Create dosing schedules with frequency, time-of-day, and reminders |
| **Doses** | Log doses, view history, get summaries over date ranges |
| **Reviews** | Write reviews for products and brands |
| **Rewards** | Check points balance, badges, streaks, and active challenges |
| **Stack Analysis** | Analyze your full supplement stack for overlaps, gaps, warnings, and recommendations |
| **Suggestions** | Submit data corrections or improvements |

**Discovery Tools (public, no auth needed)**

| Tool Group | What you can do |
|------------|-----------------|
| **Product Search** | Search by name, category, brand, ingredient, UPC, or tag |
| **Brand Search** | Find brands by name, location, or text search |
| **Ingredient Search** | Browse and search the ingredient database |
| **Ingredient Intelligence** | Get alternatives, interactions, dosing guides, effectiveness data |
| **Benefits** | Browse health benefit categories and ranked ingredients |
| **Biomarkers** | View biomarker reference ranges and supporting ingredients |
| **News** | Browse the supplement industry news feed |
| **Scoring** | Get product ingredient scores and compare products |

**Admin Tools (admin token required)**

| Tool Group | What you can do |
|------------|-----------------|
| **Products** | Create, update, delete, bulk operations |
| **Brands** | Create, update, delete brands |
| **Ingredients** | Create, update, delete, bulk ops, merge, auto-link |
| **Reviews** | Moderate (approve/reject/flag) |
| **News** | Create, update, delete news items |
| **Users** | List users, manage groups, assign brand ownership |
| **Benefits** | Create/update benefit categories, rebuild rankings |
| **Biomarkers** | Create, update, delete biomarkers |
| **Evidence Links** | Create, update, delete scientific evidence |
| **Suggestions** | Review and approve/reject user suggestions |
| **Exports** | Generate data exports |

#### Example Prompts

```
# Supplement tracking
"Show my current supplement stack"
"Add Vitamin D 5000 IU to my supplements"
"Log a dose of magnesium — 400mg taken this morning"

# Product discovery
"Search for magnesium glycinate supplements"
"Compare these two products: [id1] vs [id2]"
"Find products with ashwagandha"

# Ingredient intelligence
"What are the interactions for Vitamin D?"
"Show me the dosing guide for magnesium"
"What are the top ingredients for sleep?"

# Admin operations
"Create a new product called 'Omega-3 Fish Oil' in the heart category"
"Bulk create these 10 ingredients"
"Show the moderation queue"
```

#### Links

- PyPI: https://pypi.org/project/suppevo-mcp/
- GitHub: https://github.com/GomezMera-IO-LLC/suppevo-data-mcp

### wigolo
- **Package:** `wigolo` (via npx)
- **Description:** Local-first web intelligence for AI agents — search, fetch, crawl, extract, cache, and research without API keys.
- **Tools:** `search`, `fetch`, `crawl`, `extract`, `find_similar`, `cache`, `diff`, `watch`, `research`, `agent`
- **Use for:** Web research during evidence gathering, fetching product pages, crawling brand sites, extracting structured supplement facts, monitoring product page changes, and multi-step research synthesis.
- **Priority:** Primary web tool. Always try Wigolo first for any web-related task.

### firecrawl-mcp (fallback only)
- **Package:** `firecrawl-mcp` (via npx)
- **Description:** Cloud-based scraping API with strong anti-bot bypass capabilities. Metered usage — costs per page scraped.
- **Tools:** `firecrawl_scrape`, `firecrawl_map`, `firecrawl_crawl`, `firecrawl_extract`, `firecrawl_interact`, `firecrawl_interact_stop`
- **Use for:** Scraping sites that block Wigolo (anti-bot protection, Cloudflare challenges, JS-heavy SPAs that fail to render locally).
- **IMPORTANT — Fallback only:** Only use Firecrawl when Wigolo fails to retrieve content due to bot prevention, rendering failures, or access blocks. Always attempt with Wigolo first. If Wigolo returns empty/blocked content or a fetch error indicating bot detection, then retry with Firecrawl.

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
- Wigolo: No setup required — runs locally via `npx -y wigolo`
- Firecrawl MCP: Requires `FIRECRAWL_API_KEY` env variable (get from https://firecrawl.dev)
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
