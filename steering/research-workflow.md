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

## Workflow: Biomarker Research

### Step 1 — Identify the Biomarker

Use the Suppevo API to retrieve biomarker details:
- Get reference ranges (normal, optimal, concerning levels)
- Identify currently linked ingredients
- Note any existing evidence links

### Step 2 — Literature Search

For each ingredient linked to the biomarker:
1. Search PubMed: `"{ingredient}" AND "{biomarker}" AND (supplement OR dietary)`
2. Filter for human clinical trials when possible
3. Prioritize meta-analyses and systematic reviews
4. Include studies from the last 10 years preferentially

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

### Supporting Ingredients

#### [Ingredient Name]
- **Relationship:** [structure/function claim]
- **Evidence:** [brief summary of findings]
- **Study Type:** [meta-analysis / RCT / observational / in-vitro]
- **Reference:** [Title] (PMID: [number]) — https://pubmed.ncbi.nlm.nih.gov/[PMID]/
- **Effective Dose (from study):** [dose used in the cited study]
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

### Step 2 — Find Products

1. Search Suppevo products containing the ingredient
2. Check ingredient amounts against evidence-based dose ranges
3. Note the form of the ingredient (e.g., magnesium glycinate vs oxide)

### Step 3 — Compliance Check

For each product:
- Verify label claims use structure/function language only
- Flag any potential disease claims
- Confirm no FDA-prohibited language is present

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
