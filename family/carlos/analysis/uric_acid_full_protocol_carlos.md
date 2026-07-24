# Uric Acid Management Protocol — Carlos Gomez

**Genome File:** genome_Carlos_Gomez_v5_Full_20250610170958.txt  
**Date:** July 2026  
**Current Prescriptions:** Rosuvastatin, Lisinopril, Omega-3  
**Current Supplements:** Vitamin C, Tart Cherry, Folate

---

## 1. Genetic Analysis Summary

Your genome reveals that **~85% of your genetic predisposition to elevated uric acid comes from impaired renal excretion** — your kidneys aggressively reabsorb uric acid back into the bloodstream rather than excreting it. A secondary (~10%) contribution comes from increased hepatic production via the GCKR fructose metabolism pathway.

### Primary Genetic Drivers

#### A. Renal Urate Reabsorption — SLC2A9 (GLUT9) | Chromosome 4
**Status: Very High Risk (homozygous at 7+ SNPs)**

| SNP | Genotype | Impact |
|-----|----------|--------|
| rs734553 | TT | Increased urate reabsorption |
| rs11942223 | TT | Increased urate reabsorption |
| rs12498742 | AA | Elevated serum urate |
| rs7442295 | AA | Elevated serum urate |
| rs6832439 | GG | Risk allele carrier |
| rs4481233 | CC | Higher urate |
| rs6449213 | TT | Higher urate |
| rs3775948 | CC | Higher urate |
| rs13129697 | TT | Risk allele |

SLC2A9 is the dominant urate transporter in the kidney proximal tubule. It reabsorbs uric acid from the tubular lumen back into the blood. Your homozygous risk status across this entire locus means your kidneys retain significantly more uric acid than average.

**References:**
- Mallamaci F et al. *J Hypertens.* 2014. [PMID: 24805955](https://pubmed.ncbi.nlm.nih.gov/24805955/)
- Testa A et al. *Clin J Am Soc Nephrol.* 2014. [PMID: 24742479](https://pubmed.ncbi.nlm.nih.gov/24742479/)

#### B. Renal Urate Secretion — SLC17A1/SLC17A3 | Chromosome 6
**Status: High Risk (homozygous)**

| SNP | Genotype | Impact |
|-----|----------|--------|
| rs1165196 | AA | Reduced urate secretion |
| rs1183201 | TT | Risk allele |
| rs1165205 | AA | Risk allele |

These transporters secrete urate into the tubular lumen for excretion. Your genotype suggests reduced secretion capacity — compounding the SLC2A9 reabsorption issue.

#### C. Renal Urate Reabsorption — SLC22A11 (OAT4) / SLC22A12 (URAT1) | Chromosome 11
**Status: High Risk (homozygous at 5 SNPs)**

| SNP | Genotype | Impact |
|-----|----------|--------|
| rs2078267 | CC | Higher urate |
| rs505802 | CC | Higher urate |
| rs17300741 | AA | Risk allele |
| rs11231825 | TT | Higher urate |
| rs478607 | AA | Risk allele |

URAT1 is the primary target of the gout drug lesinurad. Your genotypes suggest enhanced reabsorption activity at this locus.

#### D. Hepatic Urate Production — GCKR | Chromosome 2
**Status: Moderate Risk (heterozygous)**

| SNP | Genotype | Impact |
|-----|----------|--------|
| rs1260326 | CT | Increased urate production via fructose metabolism |
| rs780094 | CT | Increased urate production |

The T allele (P446L variant) weakens GCKR's ability to inhibit glucokinase. When fructose enters the liver, glucokinase runs unchecked, rapidly depleting ATP. The excess AMP is degraded through: AMP → IMP → Hypoxanthine → Xanthine → **Uric Acid**.

This means fructose/sugar intake has a direct, dose-dependent, genetically-amplified effect on your uric acid production.

**References:**
- Ho LJ et al. *Sci Rep.* 2022. [PMID: 35365700](https://pubmed.ncbi.nlm.nih.gov/35365700/)
- Yeh KH et al. *Genes.* 2022. [PMID: 35328045](https://pubmed.ncbi.nlm.nih.gov/35328045/)

#### E. Gut Urate Excretion — ABCG2 | Chromosome 4
**Status: Protective (wildtype)**

| SNP | Genotype | Impact |
|-----|----------|--------|
| rs2231142 | GG | Full ABCG2 transport function — gut excretion intact |

Your gut-based urate excretion pathway (~30% of total clearance) is working normally.

**Reference:** Asif MA et al. *Int J Mol Med.* 2026. [PMID: 42396658](https://pubmed.ncbi.nlm.nih.gov/42396658/)

---

### Genetic Risk Profile

| Pathway | Genetic Load | Contribution |
|---------|-------------|-------------|
| Renal reabsorption (SLC2A9) | Very High | ~50-60% |
| Renal secretion (SLC17A1/A3) | High | ~15-20% |
| Renal reabsorption (URAT1/OAT4) | High | ~15-20% |
| Hepatic production (GCKR) | Moderate | ~10% |
| Gut excretion (ABCG2) | None (protective) | 0% |

---

## 2. Drug Interaction Analysis

### Current Prescriptions vs. Uric Acid Supplements

| Supplement | Rosuvastatin | Lisinopril | Omega-3 |
|-----------|-------------|-----------|---------|
| Vitamin C | Safe | Safe | Safe |
| Tart Cherry | Safe | Safe | Safe |
| Folate | Safe | Safe | Safe |
| Quercetin | **Caution** | Safe | Safe |
| Potassium Citrate | Safe | **Caution** | Safe |
| Magnesium Citrate | Safe | Safe | Safe |

### Interaction Details

#### Quercetin + Rosuvastatin (OATP1B1 Inhibition)

Quercetin inhibits OATP1B1, the organic anion transporting polypeptide that carries rosuvastatin into hepatocytes. In a pharmacokinetic study, co-administration of quercetin nearly doubled rosuvastatin blood concentration (Cmax 67.3 → 122.2 ng/ml, p < 0.001). Higher statin blood levels increase risk of myopathy.

**Mitigation:** Separate by 4-6 hours. Take quercetin in the morning; rosuvastatin at bedtime. Consider starting at 250 mg quercetin rather than 500 mg. Monitor for muscle pain.

**Reference:** Bhimanwar RS et al. *Cardiovasc Hematol Agents Med Chem.* 2024. [PMID: 39431375](https://pubmed.ncbi.nlm.nih.gov/39431375/)

#### Potassium Citrate + Lisinopril (Hyperkalemia Risk)

ACE inhibitors reduce aldosterone secretion, which causes the kidneys to retain potassium. Adding supplemental potassium citrate increases the risk of hyperkalemia (high serum potassium), which can cause dangerous cardiac arrhythmias.

**Mitigation:** Use **magnesium citrate** as the primary alkalinizer instead. The citrate still converts to bicarbonate and alkalinizes urine, without adding potassium load. If potassium citrate is used, limit to 1 g/day maximum and monitor serum potassium levels.

**Reference:** Wouda RD et al. *Clin J Am Soc Nephrol.* 2023. [PMID: 37382933](https://pubmed.ncbi.nlm.nih.gov/37382933/)

---

## 3. Recommended Protocol

### Currently Taking (Continue)

| Supplement | Dose | Mechanism for Your Genotype | Timing |
|-----------|------|----------------------------|--------|
| **Vitamin C** | 500-1000 mg/day | Competes with urate for reabsorption at SLC2A9 — directly counters your primary genetic vulnerability | With any meal |
| **Tart Cherry Extract** | 500-1000 mg/day | Anthocyanins inhibit xanthine oxidase → reduced uric acid production; anti-inflammatory | With food |
| **Folate** | 400-800 mcg/day | Supports purine salvage pathway (recycles AMP rather than degrading to uric acid) | With food |

**Vitamin C Evidence:** Meta-analysis of RCTs showed oral vitamin C reduces serum uric acid by ~0.35 mg/dL. Liu XX et al. *Complement Ther Med.* 2021. [PMID: 34280483](https://pubmed.ncbi.nlm.nih.gov/34280483/)

**Tart Cherry Evidence:** Cochrane systematic review acknowledged potential for uric acid management. Andrés M et al. *Cochrane Database Syst Rev.* 2021. [PMID: 34767649](https://pubmed.ncbi.nlm.nih.gov/34767649/)

### Add to Protocol

| Supplement | Dose | Mechanism | Timing |
|-----------|------|-----------|--------|
| **Magnesium Citrate** | 200-400 mg elemental Mg/day (divided) | Citrate → bicarbonate alkalinizes urine (target pH 6.5-7.0); improves uric acid solubility for excretion. Safe with lisinopril (no potassium load). | Morning + evening with food |
| **Quercetin** | 250-500 mg/day | Inhibits xanthine oxidase (reduces production) + modulates renal urate transporters | Morning (separate from rosuvastatin by 6+ hours) |

**Quercetin Evidence:** Clinical studies demonstrate significant uric acid reduction in hyperuricemic subjects. Di Pierro F et al. *Front Nutr.* 2025. [PMID: 39990611](https://pubmed.ncbi.nlm.nih.gov/39990611/)

### Optional Support

| Supplement | Dose | Notes |
|-----------|------|-------|
| **Sodium bicarbonate** | 1/4 tsp in water, 1x/day | Quick alkalinizer if urine pH remains < 6.0; adds sodium so monitor BP |
| **Potassium citrate** | Max 1 g/day | Only if serum K+ is monitored; discuss with doctor given lisinopril |

---

## 4. Dietary Strategy (GCKR-Specific)

Your GCKR CT genotype means fructose metabolism directly and mechanistically generates uric acid through ATP depletion in the liver. This is not a general "sugar is bad" recommendation — it's a specific genetic pathway.

### Eliminate

| Category | Examples | Why |
|----------|----------|-----|
| High-fructose corn syrup (HFCS) | Soda, packaged sauces, flavored yogurts, many breads, candy | 55% free fructose → direct liver ATP depletion → uric acid |
| Sugary drinks | Juices, sports drinks, sweet tea | Concentrated fructose without fiber |
| Agave syrup | "Health" foods, smoothie bars | 70-90% fructose — worse than HFCS |
| Excess table sugar (sucrose) | Desserts, sweetened coffee | 50% fructose after cleavage |

### Minimize

| Category | Guideline |
|----------|-----------|
| Fruit juice | Replace with whole fruit (fiber slows absorption, prevents ATP crash) |
| Honey | Use sparingly (~40% fructose) |
| Dried fruit | Small portions only (concentrated fructose per gram) |
| Alcohol (especially beer) | Beer adds purines + alcohol competes for renal excretion |
| High-purine foods | Organ meats, shellfish, sardines, anchovies |

### Safe / Encouraged

| Category | Examples | Why |
|----------|----------|-----|
| Complex carbs (starch) | Rice, potatoes, oats, bread (no HFCS) | Glucose goes through phosphofructokinase regulation — doesn't bypass the brake |
| Whole fruit (moderate) | 2-3 servings/day; berries, citrus, stone fruit | Fiber prevents rapid ATP depletion |
| High-potassium vegetables | Spinach, avocado, sweet potato, chard | Natural alkalinizers (organic acids → bicarbonate) |
| Coffee | 3-4 cups/day | Independently lowers uric acid via XO modulation. Hutton J et al. *Arthritis Res Ther.* 2018. [PMID: 29976226](https://pubmed.ncbi.nlm.nih.gov/29976226/) |
| Non-caloric sweeteners | Stevia, monk fruit, erythritol | Zero fructose load |
| Cherries / berries | Fresh or frozen | XO inhibition + anti-inflammatory |
| Low-fat dairy | Milk, yogurt (unsweetened) | Orotic acid and casein promote renal urate excretion |

**The rule:** If HFCS, sugar, or agave is in the first 5 ingredients on a label, your liver will convert the fructose portion directly into uric acid at an accelerated rate that a normal GCKR genotype could buffer. Yours cannot.

---

## 5. Hydration & Urine Alkalinization Protocol

Your renal excretion defect means the uric acid that does reach the tubular lumen needs maximum solubility to pass through rather than crystallize.

### Daily Protocol

1. **Water:** 3-4 liters/day — dilutes tubular uric acid concentration, reducing the gradient that drives reabsorption
2. **Lemon water:** Squeeze 1/2 lemon into each glass — citric acid metabolizes to bicarbonate, alkalinizing urine
3. **Magnesium citrate:** 200 mg morning + 200 mg evening — citrate → bicarbonate pathway
4. **Monitor urine pH:** Use pH strips (pharmacy). Test first morning urine.
   - Target: **6.5 - 7.0**
   - Below 5.5: uric acid is precipitating (crystallizing) — increase alkalinization
   - Above 7.5: overshot — calcium phosphate stone risk — reduce alkalinization

### Avoid (Acidifies Urine)

- High animal protein meals without vegetables
- Excessive sodium
- Alcohol
- Cranberry juice (acidifies — opposite of what you need)

---

## 6. Lifestyle Factors

| Factor | Recommendation | Rationale |
|--------|---------------|-----------|
| **Body composition** | Maintain lean mass; reduce visceral fat | Visceral fat → insulin resistance → reduced renal urate clearance |
| **Exercise** | Moderate aerobic (walking, cycling, swimming) | Promotes renal blood flow. Avoid extreme exertion (acute ATP breakdown → urate spike) |
| **Coffee** | 3-4 cups/day if tolerated | Modulates xanthine oxidase independent of caffeine |
| **Sleep** | 7-8 hours | Dehydration during sleep concentrates urine; hydrate before bed |

---

## 7. Daily Supplement Schedule

| Time | Supplement | Dose | Notes |
|------|-----------|------|-------|
| **Morning (with breakfast)** | Vitamin C | 500 mg | — |
| | Quercetin | 250-500 mg | Take 6+ hours before rosuvastatin |
| | Magnesium Citrate | 200 mg | Alkalinizer |
| | Folate | 400 mcg | — |
| **Midday/Afternoon** | Tart Cherry Extract | 500 mg | With food |
| **Evening (with dinner)** | Magnesium Citrate | 200 mg | Alkalinizer; also supports sleep |
| | Omega-3 | Per prescription | — |
| **Bedtime** | Rosuvastatin | Per prescription | Maximum separation from quercetin |
| *Lisinopril* | Per prescription | Per doctor's guidance (typically morning) | — |

---

## 8. Monitoring Targets

| Marker | Target | Frequency | Why |
|--------|--------|-----------|-----|
| **Serum uric acid** | < 6.0 mg/dL (ideally < 5.5) | Quarterly until stable | Primary outcome |
| **Urine pH** | 6.5 - 7.0 | Daily (home strips) | Ensures alkalinization is working |
| **Serum potassium** | 3.5 - 5.0 mEq/L | Every 3-6 months | Lisinopril + any potassium intake |
| **eGFR** | > 60 mL/min | Annually | SLC2A9 variants associated with CKD progression |
| **CK (creatine kinase)** | Normal range | If muscle pain occurs | Monitor for statin + quercetin interaction |
| **Fasting insulin** | < 10 μIU/mL | Annually | Insulin resistance reduces renal urate clearance |
| **24-hour urine uric acid** | Confirm under-excretion pattern | Once (baseline) | Expected: low relative to serum levels |

---

## 9. Long-Term Implications Beyond Uric Acid

Your SLC2A9 risk genotypes are independently associated with:

- **Chronic kidney disease progression** — [PMID: 24742479](https://pubmed.ncbi.nlm.nih.gov/24742479/)
- **Hypertension** — [PMID: 24805955](https://pubmed.ncbi.nlm.nih.gov/24805955/) (your lisinopril addresses this)
- **Kidney stone formation** — [PMID: 36967798](https://pubmed.ncbi.nlm.nih.gov/36967798/)
- **Cardiovascular risk** via endothelial dysfunction

Managing uric acid proactively is a cardiovascular and renal protective strategy aligned with your existing rosuvastatin (lipids) and lisinopril (BP/renal) prescriptions. They're all working the same system.

---

## 10. Summary — The Core Logic

```
YOUR GENETIC ISSUE:
Kidneys reabsorb too much uric acid (SLC2A9 + URAT1 + OAT4)
+ Kidneys secrete too little (SLC17A1/A3)
+ Liver makes extra from fructose (GCKR)
= Chronically elevated serum uric acid

YOUR STRATEGY:
1. Remove the substrate     → Cut fructose/HFCS/sugar (GCKR pathway)
2. Reduce production        → Quercetin + Tart Cherry (XO inhibition)
3. Compete for reabsorption → Vitamin C (at SLC2A9)
4. Maximize what gets out   → Hydration + Magnesium Citrate (alkalinize)
5. Recycle purines          → Folate (salvage pathway)
6. Protect downstream       → Rosuvastatin (CV) + Lisinopril (renal/BP)
```

---

## 11. Home Testing Guide

### A. Urine pH Testing

The simplest way to monitor whether your alkalinization protocol is working.

#### What to buy

pH test strips that cover the 4.5–9.0 range with 0.5 increments:

- **Hydrion pH strips (Micro Essential Lab)** — the classic; available at any pharmacy or Amazon
- **pHion Balance strips** — marketed specifically for body pH testing
- **Any urinalysis dipstick strip** — multi-parameter ones (Nurse Hatty, Easy@Home, Bayer Multistix) include pH along with other markers

Cost: ~$8-12 for 100+ tests.

#### How to test

1. **When:** First morning urine (most consistent baseline). Optionally also test in the afternoon to see the effect of your magnesium citrate / lemon water throughout the day.
2. **How:** Dip the strip in midstream urine for 1-2 seconds, shake off excess, wait 15-30 seconds (per package instructions), then match the color to the chart.
3. **Record it:** Note the number in your phone or a simple log. You're looking for trends, not one-off readings.

#### Interpreting results

| Urine pH | Interpretation | Action |
|----------|---------------|--------|
| < 5.5 | **Too acidic** — uric acid is crystallizing/precipitating | Increase magnesium citrate, more lemon water, more vegetables |
| 5.5 – 6.0 | Suboptimal but common | Adjust up — you're close |
| **6.5 – 7.0** | **Your target zone** — uric acid is soluble, excretion is maximized | Maintain current protocol |
| 7.0 – 7.5 | Fine — still safe | No changes needed |
| > 7.5 | **Too alkaline** — calcium phosphate stone risk increases | Reduce alkalinization (cut back sodium bicarbonate if using) |

#### Tips

- First morning urine is usually the most acidic (overnight concentration + no food intake). Don't panic if it's 5.5-6.0 in the morning — the afternoon reading after lemon water and magnesium citrate should be closer to 6.5-7.0.
- Animal protein heavy meals will acidify. Vegetable-heavy meals alkalinize. You'll see this reflected within a few hours.
- Test daily for the first 2-3 weeks until you understand your baseline, then 2-3x/week.

---

### B. Blood Uric Acid Meters (Finger Prick)

These work like a glucose meter — prick your finger, apply a drop of blood to a test strip, get a reading in seconds.

#### Devices

| Device | Function | Approximate Cost |
|--------|----------|-----------------|
| **UASure** | Dedicated uric acid meter. Electrochemical biosensor strip. | ~$35-50 for meter + strips (~$0.50-1.00/strip) |
| **Benecheck Plus** | Multi-function (uric acid + glucose + cholesterol — separate strips for each) | ~$40-60 for meter, strips sold separately |
| **Easy Touch GCU** | Multi-function (glucose, cholesterol, uric acid) | ~$30-50 |

Available on Amazon. The UASure is the most popular dedicated uric acid meter and has decent correlation with lab results (within ~0.5 mg/dL typically).

#### How to use

1. Wash hands with warm water (improves blood flow + removes contaminants)
2. Insert uric acid test strip into meter
3. Prick side of fingertip with lancet
4. Touch blood drop to strip
5. Read result in 10-20 seconds (mg/dL)

#### When to test

- **Fasting morning** — most consistent baseline (matches lab conditions)
- **Same time of day** when comparing readings over weeks
- Don't test after heavy exercise, alcohol, or a purine-rich meal — those will spike acutely and don't reflect your baseline

#### Accuracy

Home meters are generally within ±0.5 mg/dL of lab venous draws. Good enough for tracking trends (is it going down?), but not precise enough to replace a quarterly lab draw. Use them to:

- Confirm your protocol is moving things in the right direction
- See how specific dietary choices affect you within 24-48 hours
- Catch spikes early before they become chronic

---

### C. Complete Home Testing Protocol

| Test | Device | Frequency | Target | Cost |
|------|--------|-----------|--------|------|
| **Urine pH** | pH strips | Daily (first 3 weeks), then 2-3x/week | 6.5 – 7.0 | ~$10 for 100+ strips |
| **Serum uric acid** | UASure or Benecheck | Weekly (first month), then biweekly | < 6.0 mg/dL | ~$40-50 meter + strips |
| **Lab serum uric acid** | Standard blood draw | Quarterly | < 6.0 mg/dL (gold standard) | Per insurance |

Total startup cost for home monitoring: ~$50-60, then ongoing strip refills.

---

*These statements have not been evaluated by the FDA. Supplements are not intended to diagnose, treat, cure, or prevent any disease. This analysis is for informational purposes. Consult your healthcare provider before making changes to your supplementation or medication regimen.*

---

**PubMed References:**
1. Asif MA et al. *Int J Mol Med.* 2026. [PMID: 42396658](https://pubmed.ncbi.nlm.nih.gov/42396658/)
2. Mallamaci F et al. *J Hypertens.* 2014. [PMID: 24805955](https://pubmed.ncbi.nlm.nih.gov/24805955/)
3. Testa A et al. *Clin J Am Soc Nephrol.* 2014. [PMID: 24742479](https://pubmed.ncbi.nlm.nih.gov/24742479/)
4. Ho LJ et al. *Sci Rep.* 2022. [PMID: 35365700](https://pubmed.ncbi.nlm.nih.gov/35365700/)
5. Yeh KH et al. *Genes.* 2022. [PMID: 35328045](https://pubmed.ncbi.nlm.nih.gov/35328045/)
6. Liu XX et al. *Complement Ther Med.* 2021. [PMID: 34280483](https://pubmed.ncbi.nlm.nih.gov/34280483/)
7. Andrés M et al. *Cochrane Database Syst Rev.* 2021. [PMID: 34767649](https://pubmed.ncbi.nlm.nih.gov/34767649/)
8. Di Pierro F et al. *Front Nutr.* 2025. [PMID: 39990611](https://pubmed.ncbi.nlm.nih.gov/39990611/)
9. Bhimanwar RS et al. *Cardiovasc Hematol Agents Med Chem.* 2024. [PMID: 39431375](https://pubmed.ncbi.nlm.nih.gov/39431375/)
10. Wouda RD et al. *Clin J Am Soc Nephrol.* 2023. [PMID: 37382933](https://pubmed.ncbi.nlm.nih.gov/37382933/)
11. Hutton J et al. *Arthritis Res Ther.* 2018. [PMID: 29976226](https://pubmed.ncbi.nlm.nih.gov/29976226/)
12. Clavijo-Cornejo D et al. *Mol Biol Rep.* 2025. [PMID: 41460367](https://pubmed.ncbi.nlm.nih.gov/41460367/)
13. Lin CT et al. *Front Endocrinol.* 2023. [PMID: 36967798](https://pubmed.ncbi.nlm.nih.gov/36967798/)
