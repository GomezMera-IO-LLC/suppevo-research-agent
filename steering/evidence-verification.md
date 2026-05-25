---
inclusion: auto
---

# Evidence Verification Protocol

This steering file defines the mandatory verification process for all scientific evidence referenced by this research agent.

## Golden Rule

**No evidence link is valid without a verified PubMed reference.**

If a PMID cannot be verified, the evidence link MUST NOT be reported as confirmed. Mark it as "unverified" and attempt to find the correct PMID.

## Verification Steps

### 1. Obtain the PMID

If you have an article title but no PMID:
- Use `search_by_title` with the exact title
- If no match, try with a shortened version of the title
- If still no match, use `search_pubmed` with key terms from the title

### 2. Verify the Citation

Once you have a PMID:
- Call `verify_citation` with the PMID and expected title
- A similarity score ≥ 0.85 confirms the match
- A score between 0.60–0.84 requires manual review (fetch the abstract to confirm relevance)
- A score < 0.60 means the PMID does not match — find the correct one

### 3. Confirm Relevance

After PMID verification:
- Use `fetch_abstract` to read the abstract
- Confirm the study actually supports the claimed relationship
- Note the study population, intervention, and outcome

### 4. Format the Reference

Every verified reference must be formatted as:

```
**[Article Title]**
Authors (Year). Journal. Volume(Issue):Pages.
PMID: [number]
Link: https://pubmed.ncbi.nlm.nih.gov/[PMID]/
```

## Handling Unverifiable Citations

If a citation cannot be verified:

1. **Do not include it** in the final output as confirmed evidence
2. **Flag it** as "Citation could not be verified via PubMed"
3. **Search for alternatives** — there may be a more recent or better-cited study
4. **Document the attempt** — note what searches were tried

## Common Verification Issues

| Issue | Resolution |
|-------|-----------|
| PMID returns different title | The PMID may be wrong — use `search_by_title` to find the correct one |
| Article not in PubMed | Some journals aren't indexed — note this limitation and find an alternative source |
| Retracted article | Check the article status — do NOT cite retracted papers |
| Preprint only | Note it's a preprint, not peer-reviewed — lower evidence strength |

## Batch Verification

When verifying multiple evidence links:

1. Collect all PMIDs to verify
2. Run `verify_citation` for each
3. For any failures, attempt `search_by_title` to find correct PMIDs
4. Report a verification summary:
   - Total citations checked
   - Verified successfully
   - Required correction
   - Could not be verified

## Evidence Freshness

Prefer recent evidence:
- Meta-analyses: within last 5 years
- RCTs: within last 10 years
- Foundational research: any date if seminal

If only older evidence exists, note the date and whether newer research has superseded it.
