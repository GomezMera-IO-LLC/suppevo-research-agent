#!/usr/bin/env python3
"""
Product Data Validation Script

Audits the Suppevo datastore for product completeness, missing fields,
unlinked ingredients, duplicate detection, and brand coverage gaps.

Usage:
    # Full audit (all brands and products):
    python scripts/validate_product_data.py

    # Audit a specific brand by name:
    python scripts/validate_product_data.py --brand "Thorne"

    # Only check products with low completeness:
    python scripts/validate_product_data.py --min-score 80

    # Check for duplicates only:
    python scripts/validate_product_data.py --duplicates-only

    # Generate enrichment task list:
    python scripts/validate_product_data.py --generate-tasks

    # Export products missing images:
    python scripts/validate_product_data.py --missing-images

Environment Variables:
    SUPPEVO_API_BASE  - API base URL (default: https://api.dev.suppevo.com)
"""

import argparse
import json
import logging
import os
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================================================
# Configuration
# ============================================================================

API_BASE = os.environ.get("SUPPEVO_API_BASE", "https://api.dev.suppevo.com")
REQUEST_DELAY = 0.2  # seconds between API calls to avoid rate limiting

# ============================================================================
# Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ProductAudit:
    product_id: str
    name: str
    brand: str
    brand_id: Optional[str] = None
    category: Optional[str] = None
    form: Optional[str] = None
    has_image: bool = False
    has_ingredients: bool = False
    ingredient_count: int = 0
    ingredients_with_amounts: int = 0
    has_serving_size: bool = False
    has_servings_per_container: bool = False
    has_upc: bool = False
    has_asin: bool = False
    has_dosage: bool = False
    has_description: bool = False
    completeness_score: float = 0.0
    issues: list = field(default_factory=list)


@dataclass
class BrandAudit:
    brand_id: str
    name: str
    has_website: bool = False
    has_logo: bool = False
    has_location: bool = False
    has_founded_year: bool = False
    has_history: bool = False
    product_count: int = 0
    completeness_score: float = 0.0
    issues: list = field(default_factory=list)


@dataclass
class AuditReport:
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    total_brands: int = 0
    total_products: int = 0
    products_below_threshold: int = 0
    products_missing_images: int = 0
    products_missing_ingredients: int = 0
    products_missing_upc_asin: int = 0
    duplicate_candidates: int = 0
    unlinked_ingredient_count: int = 0
    brand_audits: list = field(default_factory=list)
    product_audits: list = field(default_factory=list)
    duplicates: list = field(default_factory=list)
    unlinked_ingredients: list = field(default_factory=list)


# ============================================================================
# API Helpers
# ============================================================================


def api_get(path: str, params: dict = None) -> dict:
    """Make a GET request to the Suppevo public API."""
    url = f"{API_BASE}{path}"
    if params:
        query_parts = []
        for k, v in params.items():
            if v is not None:
                query_parts.append(f"{k}={v}")
        if query_parts:
            url += "?" + "&".join(query_parts)

    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        log.warning(f"HTTP {e.code} for {url}")
        return {"error": f"HTTP {e.code}", "items": []}
    except Exception as e:
        log.warning(f"Request failed for {url}: {e}")
        return {"error": str(e), "items": []}


def paginate_all(path: str, params: dict = None, limit: int = 100) -> list:
    """Paginate through all results for a given endpoint."""
    all_items = []
    cursor = None
    page = 0

    while True:
        p = dict(params or {})
        p["limit"] = limit
        if cursor:
            p["cursor"] = cursor

        time.sleep(REQUEST_DELAY)
        data = api_get(path, p)

        items = data.get("items", [])
        all_items.extend(items)
        page += 1

        if page % 5 == 0:
            log.info(f"  ... fetched {len(all_items)} items so far (page {page})")

        cursor = data.get("cursor") or data.get("nextCursor")
        if not cursor or not items:
            break

    return all_items


# ============================================================================
# Audit Functions
# ============================================================================


def audit_brand(brand: dict) -> BrandAudit:
    """Audit a single brand for completeness."""
    audit = BrandAudit(
        brand_id=brand.get("id", ""),
        name=brand.get("name", "Unknown"),
    )

    audit.has_website = bool(brand.get("website"))
    audit.has_logo = bool(brand.get("logo_url"))
    audit.has_location = bool(
        brand.get("country") or brand.get("city") or brand.get("state")
    )
    audit.has_founded_year = bool(brand.get("founded_year"))
    audit.has_history = bool(brand.get("history"))

    # Calculate completeness
    score = 0.0
    if brand.get("name"):
        score += 15
    if audit.has_website:
        score += 15
    if audit.has_logo:
        score += 15
    if audit.has_location:
        score += 10
    if audit.has_founded_year:
        score += 10
    if brand.get("brand_type"):
        score += 10
    if brand.get("known_for"):
        score += 10
    if brand.get("badges"):
        score += 10
    if audit.has_history:
        score += 5

    audit.completeness_score = score

    # Identify issues
    if not audit.has_website:
        audit.issues.append("missing_website")
    if not audit.has_logo:
        audit.issues.append("missing_logo")
    if not audit.has_location:
        audit.issues.append("missing_location")
    if not audit.has_founded_year:
        audit.issues.append("missing_founded_year")

    return audit


def audit_product(product: dict) -> ProductAudit:
    """Audit a single product for completeness."""
    audit = ProductAudit(
        product_id=product.get("id", ""),
        name=product.get("name", "Unknown"),
        brand=product.get("brand", "Unknown"),
        brand_id=product.get("brand_id"),
        category=product.get("category"),
        form=product.get("form"),
    )

    # Check fields
    audit.has_image = bool(product.get("image_url") or product.get("imageUrl"))
    ingredients = product.get("ingredients", []) or []
    audit.has_ingredients = len(ingredients) > 0
    audit.ingredient_count = len(ingredients)
    audit.ingredients_with_amounts = sum(
        1 for ing in ingredients if ing.get("amount")
    )
    audit.has_serving_size = bool(product.get("serving_size"))
    audit.has_servings_per_container = bool(product.get("servings_per_container"))
    audit.has_upc = bool(product.get("upc"))
    audit.has_asin = bool(product.get("asin"))
    audit.has_dosage = bool(product.get("dosage"))
    audit.has_description = bool(product.get("description"))

    # Calculate completeness score
    score = 0.0
    if product.get("name"):
        score += 10
    if product.get("brand"):
        score += 10
    if product.get("category"):
        score += 5
    if product.get("form"):
        score += 5
    if audit.has_ingredients and audit.ingredients_with_amounts > 0:
        # Partial credit: full points if all ingredients have amounts
        if audit.ingredient_count > 0:
            ratio = audit.ingredients_with_amounts / audit.ingredient_count
            score += 25 * ratio
        else:
            score += 0
    elif audit.has_ingredients:
        score += 10  # Partial credit for names only
    if audit.has_image:
        score += 15
    if audit.has_serving_size:
        score += 5
    if audit.has_servings_per_container:
        score += 5
    if audit.has_upc or audit.has_asin:
        score += 10
    if audit.has_dosage:
        score += 5
    if audit.has_description:
        score += 5

    audit.completeness_score = round(score, 1)

    # Identify issues
    if not audit.has_image:
        audit.issues.append("missing_image")
    if not audit.has_ingredients:
        audit.issues.append("missing_ingredients")
    elif audit.ingredients_with_amounts == 0:
        audit.issues.append("ingredients_missing_amounts")
    elif audit.ingredients_with_amounts < audit.ingredient_count:
        audit.issues.append("some_ingredients_missing_amounts")
    if not audit.has_serving_size:
        audit.issues.append("missing_serving_size")
    if not audit.has_servings_per_container:
        audit.issues.append("missing_servings_per_container")
    if not audit.has_upc and not audit.has_asin:
        audit.issues.append("missing_upc_asin")
    if not audit.has_dosage:
        audit.issues.append("missing_dosage")
    if not product.get("category"):
        audit.issues.append("missing_category")
    if not product.get("form"):
        audit.issues.append("missing_form")

    return audit


def detect_duplicates(products: list) -> list:
    """Detect potential duplicate products by UPC and name similarity."""
    duplicates = []

    # Group by UPC
    upc_map = defaultdict(list)
    for p in products:
        upc = p.get("upc")
        if upc:
            upc_map[upc].append(p)

    for upc, prods in upc_map.items():
        if len(prods) > 1:
            duplicates.append({
                "type": "same_upc",
                "upc": upc,
                "products": [
                    {"id": p["id"], "name": p.get("name"), "brand": p.get("brand")}
                    for p in prods
                ],
            })

    # Group by normalized name + brand
    name_map = defaultdict(list)
    for p in products:
        name = (p.get("name") or "").lower().strip()
        brand = (p.get("brand") or "").lower().strip()
        key = f"{brand}::{name}"
        if name:
            name_map[key].append(p)

    for key, prods in name_map.items():
        if len(prods) > 1:
            duplicates.append({
                "type": "same_name_brand",
                "key": key,
                "products": [
                    {"id": p["id"], "name": p.get("name"), "brand": p.get("brand")}
                    for p in prods
                ],
            })

    return duplicates


# ============================================================================
# Main Audit
# ============================================================================


def run_audit(args):
    report = AuditReport()

    # ========================================================================
    # Brands
    # ========================================================================

    log.info("=" * 60)
    log.info("PHASE 1: Brand Audit")
    log.info("=" * 60)

    if args.brand:
        log.info(f"Filtering to brand: {args.brand}")
        # Search for specific brand
        brands_data = api_get("/public/brands/search", {"name": args.brand})
        brands = brands_data.get("items", [])
        if not brands:
            # Try text search
            brands_data = api_get("/public/brands/search", {"q": args.brand})
            brands = brands_data.get("items", [])
    else:
        log.info("Fetching all brands...")
        brands = paginate_all("/public/brands")

    log.info(f"Found {len(brands)} brands")
    report.total_brands = len(brands)

    for brand in brands:
        audit = audit_brand(brand)

        # Get product count for brand
        time.sleep(REQUEST_DELAY)
        brand_products = api_get(
            f"/public/brands/{brand['id']}/products", {"limit": 1}
        )
        # Estimate count from presence of cursor
        audit.product_count = len(brand_products.get("items", []))

        report.brand_audits.append(audit)

        if audit.issues:
            log.info(
                f"  {audit.name}: {audit.completeness_score}% "
                f"[issues: {', '.join(audit.issues)}]"
            )

    # ========================================================================
    # Products
    # ========================================================================

    log.info("")
    log.info("=" * 60)
    log.info("PHASE 2: Product Audit")
    log.info("=" * 60)

    if args.brand and brands:
        # Get products for the specific brand
        all_products = []
        for brand in brands:
            log.info(f"Fetching products for {brand['name']}...")
            brand_prods = paginate_all(f"/public/brands/{brand['id']}/products")
            all_products.extend(brand_prods)
    elif args.missing_images:
        log.info("Fetching all products to find those missing images...")
        all_products = paginate_all("/public/products/search")
    else:
        log.info("Fetching all products...")
        all_products = paginate_all("/public/products/search")

    log.info(f"Found {len(all_products)} products")
    report.total_products = len(all_products)

    for product in all_products:
        audit = audit_product(product)
        report.product_audits.append(audit)

        if audit.completeness_score < (args.min_score or 100):
            report.products_below_threshold += 1

        if not audit.has_image:
            report.products_missing_images += 1
        if not audit.has_ingredients:
            report.products_missing_ingredients += 1
        if not audit.has_upc and not audit.has_asin:
            report.products_missing_upc_asin += 1

    # ========================================================================
    # Duplicates
    # ========================================================================

    if not args.missing_images:
        log.info("")
        log.info("=" * 60)
        log.info("PHASE 3: Duplicate Detection")
        log.info("=" * 60)

        duplicates = detect_duplicates(all_products)
        report.duplicates = duplicates
        report.duplicate_candidates = len(duplicates)
        log.info(f"Found {len(duplicates)} potential duplicate groups")

        for dup in duplicates[:10]:
            log.info(
                f"  [{dup['type']}] "
                f"{', '.join(p['name'] or 'unnamed' for p in dup['products'])}"
            )

    # ========================================================================
    # Unlinked Ingredients
    # ========================================================================

    if not args.duplicates_only and not args.missing_images:
        log.info("")
        log.info("=" * 60)
        log.info("PHASE 4: Unlinked Ingredients Check")
        log.info("=" * 60)

        # This endpoint requires auth — try it, fall back gracefully
        unlinked_data = api_get("/ingredients/unlinked", {"limit": 100})
        if "error" not in unlinked_data:
            unlinked = unlinked_data.get("items", [])
            report.unlinked_ingredients = unlinked
            report.unlinked_ingredient_count = len(unlinked)
            log.info(f"Found {len(unlinked)} unlinked ingredient names")
            for item in unlinked[:10]:
                log.info(f"  - {item.get('name', 'unknown')} (in {item.get('product_count', '?')} products)")
        else:
            log.info("  Skipping unlinked ingredients (requires admin auth)")
            # Approximate by checking products with ingredients not linked
            unlinked_count = 0
            for product in all_products[:50]:  # Sample
                ingredients = product.get("ingredients", []) or []
                for ing in ingredients:
                    if not ing.get("ingredient_id"):
                        unlinked_count += 1
            if unlinked_count > 0:
                log.info(f"  Estimated ~{unlinked_count} unlinked ingredients in sampled products")
            report.unlinked_ingredient_count = unlinked_count

    # ========================================================================
    # Save Reports
    # ========================================================================

    log.info("")
    log.info("=" * 60)
    log.info("SAVING REPORTS")
    log.info("=" * 60)

    reports_dir = Path("scripts")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Main validation report
    validation_report = {
        "started_at": report.started_at,
        "completed_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_brands": report.total_brands,
            "total_products": report.total_products,
            "products_below_threshold": report.products_below_threshold,
            "products_missing_images": report.products_missing_images,
            "products_missing_ingredients": report.products_missing_ingredients,
            "products_missing_upc_asin": report.products_missing_upc_asin,
            "duplicate_candidates": report.duplicate_candidates,
            "unlinked_ingredient_count": report.unlinked_ingredient_count,
        },
        "threshold_used": args.min_score or 80,
    }

    report_path = reports_dir / "validation_report.json"
    with open(report_path, "w") as f:
        json.dump(validation_report, f, indent=2)
    log.info(f"Summary report: {report_path}")

    # Incomplete products detail
    incomplete = [
        {
            "product_id": a.product_id,
            "name": a.name,
            "brand": a.brand,
            "completeness_score": a.completeness_score,
            "issues": a.issues,
        }
        for a in report.product_audits
        if a.completeness_score < (args.min_score or 80)
    ]
    incomplete.sort(key=lambda x: x["completeness_score"])

    incomplete_path = reports_dir / "incomplete_products.json"
    with open(incomplete_path, "w") as f:
        json.dump(incomplete, f, indent=2)
    log.info(f"Incomplete products ({len(incomplete)}): {incomplete_path}")

    # Missing images list
    missing_images = [
        {
            "product_id": a.product_id,
            "name": a.name,
            "brand": a.brand,
            "brand_id": a.brand_id,
        }
        for a in report.product_audits
        if not a.has_image
    ]

    missing_images_path = reports_dir / "missing_images.json"
    with open(missing_images_path, "w") as f:
        json.dump(missing_images, f, indent=2)
    log.info(f"Missing images ({len(missing_images)}): {missing_images_path}")

    # Duplicates
    if report.duplicates:
        duplicates_path = reports_dir / "duplicates.json"
        with open(duplicates_path, "w") as f:
            json.dump(report.duplicates, f, indent=2)
        log.info(f"Duplicates ({len(report.duplicates)}): {duplicates_path}")

    # Brand gaps
    brand_gaps = [
        {
            "brand_id": a.brand_id,
            "name": a.name,
            "completeness_score": a.completeness_score,
            "issues": a.issues,
            "product_count": a.product_count,
        }
        for a in report.brand_audits
        if a.issues
    ]
    brand_gaps.sort(key=lambda x: x["completeness_score"])

    brand_gaps_path = reports_dir / "brand_gaps.json"
    with open(brand_gaps_path, "w") as f:
        json.dump(brand_gaps, f, indent=2)
    log.info(f"Brand gaps ({len(brand_gaps)}): {brand_gaps_path}")

    # ========================================================================
    # Generate enrichment tasks (optional)
    # ========================================================================

    if args.generate_tasks:
        tasks = []
        priority = 0

        # High priority: products with no ingredients
        for a in report.product_audits:
            if not a.has_ingredients:
                priority += 1
                tasks.append({
                    "priority": 1,
                    "type": "add_ingredients",
                    "product_id": a.product_id,
                    "product_name": a.name,
                    "brand": a.brand,
                    "action": "Extract supplement facts from brand website",
                })

        # Medium priority: products with no image
        for a in report.product_audits:
            if not a.has_image and a.has_ingredients:
                tasks.append({
                    "priority": 2,
                    "type": "add_image",
                    "product_id": a.product_id,
                    "product_name": a.name,
                    "brand": a.brand,
                    "action": "Find and upload product image",
                })

        # Lower priority: missing UPC/ASIN
        for a in report.product_audits:
            if not a.has_upc and not a.has_asin and a.has_ingredients:
                tasks.append({
                    "priority": 3,
                    "type": "add_identifier",
                    "product_id": a.product_id,
                    "product_name": a.name,
                    "brand": a.brand,
                    "action": "Find UPC or ASIN for product",
                })

        tasks.sort(key=lambda x: x["priority"])
        tasks_path = reports_dir / "enrichment_tasks.json"
        with open(tasks_path, "w") as f:
            json.dump(tasks, f, indent=2)
        log.info(f"Enrichment tasks ({len(tasks)}): {tasks_path}")

    # ========================================================================
    # Print Summary
    # ========================================================================

    log.info("")
    log.info("=" * 60)
    log.info("VALIDATION COMPLETE")
    log.info("=" * 60)
    log.info(f"Brands:                    {report.total_brands}")
    log.info(f"Products:                  {report.total_products}")
    log.info(f"Below {args.min_score or 80}% completeness: {report.products_below_threshold}")
    log.info(f"Missing images:            {report.products_missing_images}")
    log.info(f"Missing ingredients:       {report.products_missing_ingredients}")
    log.info(f"Missing UPC/ASIN:          {report.products_missing_upc_asin}")
    log.info(f"Duplicate candidates:      {report.duplicate_candidates}")
    log.info(f"Unlinked ingredients:      {report.unlinked_ingredient_count}")

    # Score distribution
    scores = [a.completeness_score for a in report.product_audits]
    if scores:
        avg_score = sum(scores) / len(scores)
        below_50 = sum(1 for s in scores if s < 50)
        between_50_80 = sum(1 for s in scores if 50 <= s < 80)
        above_80 = sum(1 for s in scores if s >= 80)
        log.info(f"\nScore distribution:")
        log.info(f"  Average:  {avg_score:.1f}%")
        log.info(f"  < 50%:    {below_50} products")
        log.info(f"  50-80%:   {between_50_80} products")
        log.info(f"  ≥ 80%:    {above_80} products")


def main():
    parser = argparse.ArgumentParser(
        description="Validate product data in the Suppevo datastore"
    )
    parser.add_argument(
        "--brand", type=str,
        help="Audit a specific brand by name"
    )
    parser.add_argument(
        "--min-score", type=int, default=80,
        help="Minimum completeness score threshold (default: 80)"
    )
    parser.add_argument(
        "--duplicates-only", action="store_true",
        help="Only run duplicate detection"
    )
    parser.add_argument(
        "--missing-images", action="store_true",
        help="Only list products missing images"
    )
    parser.add_argument(
        "--generate-tasks", action="store_true",
        help="Generate prioritized enrichment task list"
    )
    args = parser.parse_args()

    run_audit(args)


if __name__ == "__main__":
    main()
