---
inclusion: auto
---

# Product & Brand Data Collection Workflow

This steering file defines the standard workflow for collecting, validating, and enriching supplement product data across multiple brands in the Suppevo platform.

## Core Principles

1. **Brand-first**: Always create/verify the brand entity before adding products.
2. **Deduplication**: Check UPC and name before creating — never create duplicates.
3. **Completeness-driven**: Every product should reach ≥80% completeness score.
4. **Ingredient linking**: After product creation, always run `auto_link_ingredients` to connect to ingredient entities.
5. **Image required**: Products without images are incomplete — always capture the primary product image.
6. **Validate existing data**: Before adding new products, audit what's already in the datastore.

## Data Sources (Priority Order)

1. **Brand official website** — Most authoritative for supplement facts, images, and claims.
2. **Amazon (ASIN)** — Standardized product data, images, UPC codes.
3. **Retailer sites** (iHerb, Vitacost, Thorne direct, etc.) — Good backup source.
4. **UPC databases** (Open Food Facts, UPC Item DB) — For cross-referencing.

## Workflow: Validate Existing Data

Before collecting new data, always audit what's already in the datastore.

### Step 1 — Brand Inventory

```
1. Use `public_list_brands` (paginate fully) to get all brands
2. For each brand, check:
   - Has website? → If not, flag for enrichment
   - Has logo? → If not, flag for enrichment
   - Has location (city, state, country)? → If not, research and update
3. Use `public_list_brand_products` to get product counts per brand
4. Identify brands with < 3 products (likely incomplete catalog)
```

### Step 2 — Product Completeness Audit

```
For each product in the datastore:
1. Use `public_get_product_completeness` to get score
2. Flag products with score < 80% for enrichment
3. Check for:
   - Missing image_url
   - Empty ingredients list
   - Missing serving_size or servings_per_container
   - Missing UPC or ASIN
   - Missing dosage instructions
   - Missing category or form
```

### Step 3 — Ingredient Linking Audit

```
1. Use `list_unlinked_ingredients` to find product ingredients not linked to entities
2. Attempt `auto_link_ingredients` to resolve obvious matches
3. For remaining unlinked:
   - Search ingredient database: `search_ingredients` with partial name
   - Decide if a new ingredient entity should be created
   - Or if it's a variant name of an existing ingredient → suggest merge
```

### Step 4 — Duplicate Detection

```
1. For each product with a UPC, use `find_product_by_upc` to check for duplicates
2. Search by exact product name + brand to find near-duplicates
3. Flag duplicates for merge or deletion
```

## Workflow: Collect New Brand + Products

### Step 1 — Create or Find Brand

```
1. Use `find_brand_by_name` to check if brand already exists
2. If exists → get brand_id, proceed to products
3. If not → research the brand:
   a. Brand name, website, logo URL
   b. Founded year, headquarters location (city, state, country)
   c. Parent company (if applicable)
   d. Brand type: independent | subsidiary | house_brand | white_label
   e. Known for (key categories)
   f. Quality badges: GMP, NSF, Non-GMO, etc.
4. Use `create_brand` with all available fields
5. Use `upload_brand_logo` to get presigned URL, upload logo
```

### Step 2 — Enumerate Brand Products

```
1. Visit brand website product catalog page
2. List ALL supplement products (not merchandise/apparel)
3. For each product, extract:
   - Product name (exact, as on label)
   - Category (sleep, energy, immunity, etc.)
   - Form (capsule, tablet, powder, gummy, liquid, softgel)
   - Serving size (e.g. "2 capsules")
   - Servings per container (numeric)
   - Recommended dosage (e.g. "Take 2 capsules daily with food")
   - UPC barcode (if visible)
   - ASIN (if sold on Amazon)
   - Product image URL (highest resolution available)
   - Description (1-2 sentences)
```

### Step 3 — Extract Supplement Facts

For each product, capture the full ingredient list:

```json
{
  "ingredients": [
    {
      "name": "Vitamin D3 (as Cholecalciferol)",
      "amount": "50",
      "unit": "mcg",
      "daily_value_percent": 250
    },
    {
      "name": "Magnesium (as Magnesium Glycinate)",
      "amount": "200",
      "unit": "mg",
      "daily_value_percent": 48
    }
  ]
}
```

Rules for ingredient extraction:
- Include the form in parentheses: "Vitamin D3 (as Cholecalciferol)"
- Use standard units: mcg, mg, g, IU, CFU, mL
- Include daily_value_percent when listed on label
- Include "Other Ingredients" in a description field, not in the ingredients array
- Proprietary blends: list total blend amount, then individual ingredients without amounts if not disclosed

### Step 4 — Create Products

```
1. Check `find_product_by_upc` for duplicates (if UPC available)
2. Search `public_search_products` by name + brand for near-duplicates
3. If no duplicate → use `create_product` or `bulk_create_products` (max 25/batch)
4. After creation → use `upload_product_image` to get presigned URL
5. Upload image via HTTP PUT to the presigned URL
6. Run `auto_link_ingredients` to link ingredient names to entities
```

### Step 5 — Post-Creation Validation

```
1. Use `public_get_product_completeness` for each new product
2. If score < 80% → identify and fill missing fields
3. Use `list_unlinked_ingredients` → resolve any remaining unlinked ingredients
4. Use `public_get_product` to verify all data looks correct
```

## Workflow: Enrich Existing Products

### Step 1 — Identify Gaps

Use the validation script (`scripts/validate_product_data.py`) to generate a gap report:
- Products missing images
- Products with empty or incomplete ingredient lists
- Products without UPC/ASIN
- Products with low completeness scores

### Step 2 — Research and Fill

For each incomplete product:
1. Find the product on the brand's website
2. Extract missing supplement facts data
3. Capture product image if missing
4. Use `update_product` to fill gaps
5. Re-run `public_get_product_completeness` to verify improvement

### Step 3 — Image Collection

```
1. Preferred image: front label showing product name and supplement facts
2. Format: WebP or PNG, minimum 500x500px
3. Use `upload_product_image` to get presigned S3 URL
4. PUT the image to the presigned URL
5. CDN URL is automatically attached to the product
```

## Quality Scoring

### Product Completeness Criteria

| Field | Weight | Required |
|-------|--------|----------|
| Name | 10% | Yes |
| Brand | 10% | Yes |
| Category | 5% | Yes |
| Form | 5% | Yes |
| Ingredients (with amounts) | 25% | Yes |
| Image | 15% | Yes |
| Serving size | 5% | Yes |
| Servings per container | 5% | Yes |
| UPC or ASIN | 10% | No |
| Dosage instructions | 5% | No |
| Description | 5% | No |

### Brand Completeness Criteria

| Field | Weight | Required |
|-------|--------|----------|
| Name | 15% | Yes |
| Website | 15% | Yes |
| Logo | 15% | Yes |
| Location (country at minimum) | 10% | Yes |
| Founded year | 10% | No |
| Brand type | 10% | No |
| Known for | 10% | No |
| Quality badges | 10% | No |
| History | 5% | No |

## Batch Processing Guidelines

### Bulk Create (up to 25/batch)

When processing many products:
1. Group products by brand
2. Validate all data BEFORE calling `bulk_create_products`
3. Check response for per-item errors
4. Log all created product IDs for subsequent image upload + validation
5. Run `auto_link_ingredients` after each batch

### Image Upload Pipeline

After bulk creation:
1. For each created product_id:
   a. Call `upload_product_image` → get presigned PUT URL
   b. Download image from source (brand website)
   c. PUT to presigned URL (Content-Type: image/webp or image/png)
   d. Verify product image_url is now set

## Category Mapping

Map product types to Suppevo categories:

| Product Type | Category |
|-------------|----------|
| Sleep aids, melatonin, magnesium for sleep | sleep |
| Probiotics, digestive enzymes, fiber | digestion |
| Ashwagandha, L-theanine, adaptogens | stress |
| B-vitamins, CoQ10, iron | energy |
| Glucosamine, collagen, turmeric for joints | joints |
| Vitamin C, elderberry, zinc for immune | immunity |
| Omega-3, CoQ10 for heart | heart |
| Lion's mane, phosphatidylserine, ginkgo | brain |
| Collagen, biotin, hyaluronic acid | beauty |
| CLA, green tea extract, fiber | weight |
| Prenatal multivitamins, folate, DHA | prenatal |
| Children's multivitamins, kids formulas | kids |
| Creatine, BCAAs, protein, pre-workout | sports |
| General multivitamins, mineral blends | general |

## Error Handling

- If a product create fails → log the error, skip, continue with next
- If image upload fails → flag product for retry later
- If ingredient linking fails → add to "unlinked" review queue
- If brand website is inaccessible → try Amazon/retailer as backup source
- Never silently drop data — always log what was skipped and why

## Output Artifacts

After a collection run, produce:
1. `scripts/collection_report.json` — Summary of what was created/updated
2. `scripts/incomplete_products.json` — Products needing enrichment
3. `scripts/unlinked_ingredients.json` — Ingredients needing manual mapping
