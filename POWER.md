# Suppevo Biomedical Research Agent

A Kiro Power for biomedical research focused on dietary supplements. Identifies biomarkers, maps ingredients to supplement products, and verifies all scientific evidence through PubMed citations — while ensuring full DSHEA compliance.

## Overview

This power combines two MCP servers:

1. **suppevo-pubmed-mcp** — Search PubMed, fetch article metadata, verify citations, and find PMIDs.
2. **suppevo-data-mcp** — Access the Suppevo platform for products, ingredients, biomarkers, evidence links, and ingredient intelligence.

Together they enable a research workflow where every claim is backed by a verifiable PubMed reference and every ingredient-to-product mapping complies with DSHEA regulations.

## Keywords

biomedical, research, biomarkers, ingredients, evidence, pubmed, supplements, DSHEA, FDA, compliance, citations, nutrition, health claims, structure-function claims, dietary supplements

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

## MCP Servers

This power uses two MCP servers:

### pubmed
- **Package:** `suppevo-pubmed-mcp`
- **Tools:** `search_pubmed`, `fetch_article`, `fetch_abstract`, `verify_citation`, `search_by_title`

### suppevo
- **Package:** `suppevo-data-mcp`
- **Tools:** 100+ tools for products, ingredients, biomarkers, evidence links, and more

## Setup

See the individual server documentation:
- PubMed MCP: Requires optional NCBI API key for higher rate limits
- Suppevo MCP: Requires Suppevo API credentials (JWT token)

## Important Rules

1. **Every evidence link must have a verified PubMed reference.** No exceptions.
2. **Never make disease claims.** Only structure/function claims are permitted.
3. **Always verify citations before reporting.** Use `verify_citation` to confirm PMID accuracy.
4. **Use qualifying language.** "May support", "helps maintain", "plays a role in" — not "prevents", "treats", "cures".
5. **Include disclaimers when appropriate.** "These statements have not been evaluated by the FDA. This product is not intended to diagnose, treat, cure, or prevent any disease."
