#!/usr/bin/env python3
"""
Evidence Link Verification Script (MCP-based)

Uses the suppevo-data-mcp and suppevo-pubmed-mcp servers directly via
subprocess to verify all evidence links. No JWT token needed — the MCP
servers handle authentication.

Usage:
    # Dry run (report only, no deletions):
    python scripts/verify_evidence_links.py

    # Auto-delete invalid links (requires confirmation):
    python scripts/verify_evidence_links.py --delete

    # Resume from a specific biomarker slug:
    python scripts/verify_evidence_links.py --start-from hemoglobin-a1c

    # Skip already-verified ingredients (provide a file with IDs):
    python scripts/verify_evidence_links.py --skip-file scripts/verified_ingredients.txt

Environment Variables:
    NCBI_API_KEY  - Optional NCBI API key for higher PubMed rate limits
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================================================
# Configuration
# ============================================================================

NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")

# MCP server commands
SUPPEVO_MCP = ["uvx", "suppevo-data-mcp@latest"]
PUBMED_MCP = ["uvx", "suppevo-pubmed-mcp@latest"]

# Rate limiting for PubMed (NCBI)
NCBI_DELAY = 0.35 if NCBI_API_KEY else 1.0

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
class VerificationResult:
    evidence_id: str
    ingredient_id: str
    ingredient_name: str
    biomarker_name: str
    pmid: str
    expected_title: str
    actual_title: Optional[str] = None
    verified: bool = False
    similarity: float = 0.0
    action: str = "pending"  # "keep", "delete", "review"
    error: Optional[str] = None


@dataclass
class AuditReport:
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    total_links_scanned: int = 0
    verified_correct: int = 0
    fabricated_deleted: int = 0
    borderline: int = 0
    errors: int = 0
    results: list = field(default_factory=list)


# ============================================================================
# MCP Server Communication
# ============================================================================


def call_mcp_tool(server: str, tool: str, arguments: dict) -> dict:
    """
    Call an MCP tool via JSON-RPC over stdio.

    This sends a tools/call request to the MCP server process and reads
    the response.
    """
    if server == "pubmed":
        cmd = PUBMED_MCP
    elif server == "suppevo":
        cmd = SUPPEVO_MCP
    else:
        raise ValueError(f"Unknown server: {server}")

    # Build JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool,
            "arguments": arguments,
        },
    }

    env = os.environ.copy()
    if NCBI_API_KEY and server == "pubmed":
        env["NCBI_API_KEY"] = NCBI_API_KEY

    try:
        proc = subprocess.run(
            cmd + ["--oneshot"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        if proc.returncode != 0:
            # Try parsing stderr for useful info
            return {"error": f"Process exited with code {proc.returncode}: {proc.stderr[:200]}"}

        # Parse JSON-RPC response
        response = json.loads(proc.stdout)
        if "error" in response:
            return {"error": response["error"]}

        # Extract content from MCP response
        result = response.get("result", {})
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            return json.loads(content[0]["text"])

        return result

    except subprocess.TimeoutExpired:
        return {"error": "MCP call timed out"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# PubMed Verification (via NCBI E-utilities directly — faster than MCP)
# ============================================================================

import urllib.request
import xml.etree.ElementTree as ET


def fetch_pubmed_title_direct(pmid: str) -> Optional[str]:
    """Fetch the actual title for a given PMID directly from NCBI E-utilities."""
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"
    if NCBI_API_KEY:
        url += f"&api_key={NCBI_API_KEY}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read().decode("utf-8")

        # Parse XML to get ArticleTitle
        root = ET.fromstring(xml_data)
        article_title = root.find(".//ArticleTitle")
        if article_title is not None:
            # Get all text content including any child elements
            title = "".join(article_title.itertext()).strip().rstrip(".")
            return title
        return None
    except Exception as e:
        log.warning(f"  Failed to fetch PMID {pmid}: {e}")
        return None


# ============================================================================
# Suppevo API (via direct HTTP — MCP server handles auth internally)
# ============================================================================


def get_biomarkers_direct() -> list:
    """Get all biomarkers with ingredient_count > 0."""
    url = "https://api.dev.suppevo.com/public/biomarkers?limit=100"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        return [b for b in data.get("items", []) if b.get("ingredient_count", 0) > 0]
    except Exception as e:
        log.error(f"Failed to fetch biomarkers: {e}")
        return []


def get_biomarker_ingredients_direct(slug: str) -> list:
    """Get ingredients linked to a biomarker."""
    url = f"https://api.dev.suppevo.com/public/biomarkers/{slug}/ingredients?limit=100"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data.get("items", [])
    except Exception as e:
        log.warning(f"Failed to fetch ingredients for {slug}: {e}")
        return []


def get_ingredient_evidence_direct(ingredient_id: str) -> dict:
    """Get all evidence links for an ingredient."""
    url = f"https://api.dev.suppevo.com/public/ingredients/{ingredient_id}/evidence"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 500:
            return {"biomarkers": [], "error": "500_internal_error"}
        return {"biomarkers": [], "error": str(e)}
    except Exception as e:
        return {"biomarkers": [], "error": str(e)}


def delete_evidence_link_mcp(evidence_id: str, ingredient_id: str) -> bool:
    """Delete an evidence link using the MCP server (handles auth)."""
    result = call_mcp_tool("suppevo", "delete_evidence_link", {
        "evidence_id": evidence_id,
        "ingredient_id": ingredient_id,
    })
    return result.get("status") == "success" or result.get("status_code") == 204


# ============================================================================
# Verification Logic
# ============================================================================


def title_similarity(title1: str, title2: str) -> float:
    """Word-overlap Jaccard similarity between two titles."""
    if not title1 or not title2:
        return 0.0
    words1 = set(title1.lower().replace(".", "").replace(",", "").split())
    words2 = set(title2.lower().replace(".", "").replace(",", "").split())
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)


def verify_single_link(evidence: dict, ingredient_name: str, biomarker_name: str) -> VerificationResult:
    """Verify a single evidence link."""
    citation = evidence.get("citation", {})
    pmid = citation.get("pubmed_id", "")
    expected_title = citation.get("title", "").rstrip(".")

    result = VerificationResult(
        evidence_id=evidence["id"],
        ingredient_id=evidence["ingredient_id"],
        ingredient_name=ingredient_name,
        biomarker_name=biomarker_name,
        pmid=pmid,
        expected_title=expected_title,
    )

    if not pmid:
        result.error = "No PMID in citation"
        result.action = "delete"
        return result

    # Fetch actual title from PubMed
    time.sleep(NCBI_DELAY)
    actual_title = fetch_pubmed_title_direct(pmid)

    if actual_title is None:
        result.error = "PMID not found or fetch failed"
        result.action = "delete"
        return result

    result.actual_title = actual_title
    result.similarity = title_similarity(expected_title, actual_title)

    # Decision thresholds
    if result.similarity >= 0.4:
        result.verified = True
        result.action = "keep"
    elif result.similarity >= 0.25:
        result.action = "review"
    else:
        result.action = "delete"

    return result


# ============================================================================
# Main
# ============================================================================


def run_audit(args):
    report = AuditReport()
    skip_ingredients = set()

    if args.skip_file and Path(args.skip_file).exists():
        with open(args.skip_file) as f:
            skip_ingredients = {line.strip() for line in f if line.strip()}
        log.info(f"Loaded {len(skip_ingredients)} ingredient IDs to skip")

    log.info("Fetching biomarkers with evidence links...")
    biomarkers = get_biomarkers_direct()
    log.info(f"Found {len(biomarkers)} biomarkers with linked ingredients")

    started = not args.start_from
    processed_ingredients = set()

    for biomarker in biomarkers:
        slug = biomarker["slug"]

        if not started:
            if slug == args.start_from:
                started = True
            else:
                continue

        log.info(f"\n{'='*60}")
        log.info(f"Biomarker: {biomarker['name']} ({slug})")
        log.info(f"{'='*60}")

        ingredients = get_biomarker_ingredients_direct(slug)

        for ingredient in ingredients:
            ing_id = ingredient["ingredient_id"]
            ing_name = ingredient["ingredient_name"]

            if ing_id in processed_ingredients or ing_id in skip_ingredients:
                continue
            processed_ingredients.add(ing_id)

            log.info(f"\n  Ingredient: {ing_name}")

            evidence_data = get_ingredient_evidence_direct(ing_id)

            if evidence_data.get("error"):
                log.warning(f"    ⚠️ Error: {evidence_data['error']}")
                report.errors += 1
                continue

            for biomarker_group in evidence_data.get("biomarkers", []):
                bm_name = biomarker_group.get("biomarker_name", "")

                for link in biomarker_group.get("evidence_links", []):
                    report.total_links_scanned += 1
                    result = verify_single_link(link, ing_name, bm_name)
                    report.results.append(result)

                    if result.verified:
                        log.info(f"    ✅ [{bm_name}] PMID {result.pmid} (sim={result.similarity:.2f})")
                        report.verified_correct += 1
                    elif result.action == "review":
                        log.warning(f"    ⚠️  [{bm_name}] PMID {result.pmid} borderline (sim={result.similarity:.2f})")
                        report.borderline += 1
                    elif result.action == "delete":
                        log.error(f"    ❌ [{bm_name}] PMID {result.pmid} INVALID (sim={result.similarity:.2f})")
                        report.fabricated_deleted += 1

    # ========================================================================
    # Save Report
    # ========================================================================

    report_path = Path("scripts/verification_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "started_at": report.started_at,
        "completed_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_scanned": report.total_links_scanned,
            "verified_correct": report.verified_correct,
            "to_delete": report.fabricated_deleted,
            "borderline_review": report.borderline,
            "errors": report.errors,
        },
        "to_delete": [
            {
                "evidence_id": r.evidence_id,
                "ingredient_id": r.ingredient_id,
                "ingredient_name": r.ingredient_name,
                "biomarker": r.biomarker_name,
                "pmid": r.pmid,
                "expected_title": r.expected_title,
                "actual_title": r.actual_title,
                "similarity": r.similarity,
                "error": r.error,
            }
            for r in report.results
            if r.action == "delete"
        ],
        "borderline": [
            {
                "evidence_id": r.evidence_id,
                "ingredient_id": r.ingredient_id,
                "ingredient_name": r.ingredient_name,
                "biomarker": r.biomarker_name,
                "pmid": r.pmid,
                "expected_title": r.expected_title,
                "actual_title": r.actual_title,
                "similarity": r.similarity,
            }
            for r in report.results
            if r.action == "review"
        ],
        "verified": [
            {
                "evidence_id": r.evidence_id,
                "ingredient_id": r.ingredient_id,
                "ingredient_name": r.ingredient_name,
                "biomarker": r.biomarker_name,
                "pmid": r.pmid,
                "similarity": r.similarity,
            }
            for r in report.results
            if r.action == "keep"
        ],
    }

    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)

    log.info(f"\n{'='*60}")
    log.info("VERIFICATION COMPLETE")
    log.info(f"{'='*60}")
    log.info(f"Total scanned:      {report.total_links_scanned}")
    log.info(f"Verified correct:   {report.verified_correct} ✅")
    log.info(f"To delete:          {report.fabricated_deleted} ❌")
    log.info(f"Borderline review:  {report.borderline} ⚠️")
    log.info(f"Errors:             {report.errors}")
    log.info(f"Report saved to:    {report_path}")

    # ========================================================================
    # Deletion via MCP server (handles auth)
    # ========================================================================

    if args.delete:
        to_delete = [r for r in report.results if r.action == "delete"]
        if not to_delete:
            log.info("Nothing to delete.")
            return

        print(f"\n{'='*60}")
        print(f"⚠️  DELETION REVIEW")
        print(f"{'='*60}")
        print(f"\nAbout to delete {len(to_delete)} evidence links with invalid citations.")
        print(f"These links have PMIDs pointing to completely unrelated papers.")
        print(f"\nReport: scripts/verification_report.json")
        print(f"\nExamples of what will be deleted:")
        for r in to_delete[:5]:
            print(f"  • {r.ingredient_name} → {r.biomarker_name}")
            print(f"    PMID {r.pmid}: expected '{r.expected_title[:60]}...'")
            if r.actual_title:
                print(f"    Actually:  '{r.actual_title[:60]}...'")
            print()

        confirm = input("Type 'DELETE' to confirm deletion (uses MCP server for auth): ")

        if confirm.strip() == "DELETE":
            deleted = 0
            failed = 0
            for i, r in enumerate(to_delete):
                success = delete_evidence_link_mcp(r.evidence_id, r.ingredient_id)
                if success:
                    deleted += 1
                else:
                    failed += 1
                    log.warning(f"  Failed to delete {r.evidence_id}")

                if (i + 1) % 10 == 0:
                    log.info(f"  Progress: {i+1}/{len(to_delete)} ({deleted} deleted, {failed} failed)")

            log.info(f"\n✅ Deletion complete: {deleted} deleted, {failed} failed")
        else:
            log.info("Deletion cancelled. Review the report and run again with --delete when ready.")

    # Save processed ingredients for resume
    verified_path = Path("scripts/verified_ingredients.txt")
    with open(verified_path, "w") as f:
        for ing_id in sorted(processed_ingredients):
            f.write(f"{ing_id}\n")
    log.info(f"Processed ingredient IDs saved to: {verified_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Verify evidence link PubMed citations using MCP servers"
    )
    parser.add_argument(
        "--delete", action="store_true",
        help="Delete invalid links after review (uses MCP server, no token needed)"
    )
    parser.add_argument(
        "--start-from", type=str,
        help="Start from a specific biomarker slug (for resuming)"
    )
    parser.add_argument(
        "--skip-file", type=str,
        help="File with ingredient IDs to skip (one per line)"
    )
    args = parser.parse_args()

    run_audit(args)


if __name__ == "__main__":
    main()
