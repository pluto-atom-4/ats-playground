#!/usr/bin/env python
"""Analyze requirements for inappropriate chunks."""

import json
import re
from pathlib import Path
from collections import defaultdict


def categorize_requirement(req: str) -> str:
    """Categorize requirement."""
    req_lower = req.lower()

    # Fragments
    if req in ("one", "Review", "review"):
        return "FRAGMENT"

    if req.endswith("'s") or req.endswith("'"):
        return "POSSESSIVE"

    if req.startswith(("each ", "a ", "an ", "the ")):
        return "FRAGMENT_START"

    if re.match(r"^[a-z]\s*$", req):  # Single letter
        return "FRAGMENT"

    if req in ("s of Service", "U.S. National", "Oversees"):
        return "FRAGMENT_INCOMPLETE"

    # Locations/proper nouns
    if req in ("Seattle", "Rocky", "Road Test"):
        return "LOCATION_PROPER"

    # Job titles
    if req in ("Design and Verification Engineer", "Software Lead", "Technical Leadership"):
        return "JOB_TITLE"

    # Generic categories (not specific requirements)
    generic_categories = {
        "software engineering", "software architecture and design",
        "software configuration management", "software life cycle management",
        "college of arts", "college of arts and sciences"
    }
    if req_lower in generic_categories:
        return "GENERIC_CATEGORY"

    # Regulations/policies/benefits
    if req in ("Federal Motor Carrier Safety Regulations", "Commercial Motor Vehicles",
               "Pre-IPO Stock Options", "Alcohol Testing"):
        return "POLICY_BENEFIT"

    # Responsibilities (action phrases)
    if req.startswith(("Optimize ", "Prepare ", "Technical oversight")):
        return "RESPONSIBILITY"

    # Abbreviations not clearly tech
    if req in ("HDHP",):
        return "UNCLEAR_ABBREV"

    return "VALID"


def main():
    """Analyze requirements."""
    jobs_file = Path("data/extracted_jobs/preprocessed_jobs.json")
    if not jobs_file.exists():
        print(f"❌ File not found: {jobs_file}")
        return

    with open(jobs_file) as f:
        jobs = json.load(f)

    print("=" * 100)
    print("REQUIREMENTS QUALITY ANALYSIS")
    print("=" * 100)
    print()

    all_reqs = []
    categories = defaultdict(list)

    for job in jobs:
        for req in job.get("requirements", []):
            all_reqs.append(req)
            category = categorize_requirement(req)
            categories[category].append(req)

    print(f"📊 SUMMARY")
    print("-" * 100)
    print(f"Total requirements: {len(all_reqs)}")
    print()

    problematic = ["FRAGMENT", "POSSESSIVE", "FRAGMENT_START", "FRAGMENT_INCOMPLETE",
                   "LOCATION_PROPER", "JOB_TITLE", "GENERIC_CATEGORY", "POLICY_BENEFIT",
                   "RESPONSIBILITY", "UNCLEAR_ABBREV"]

    total_problematic = sum(len(categories[cat]) for cat in problematic)
    print(f"Problematic items: {total_problematic} ({total_problematic/len(all_reqs)*100:.1f}%)")
    print(f"Valid items: {len(categories['VALID'])} ({len(categories['VALID'])/len(all_reqs)*100:.1f}%)")
    print()

    for category in problematic:
        if categories[category]:
            items = categories[category]
            print(f"\n🔴 {category} ({len(items)})")
            print("-" * 100)
            for item in sorted(set(items)):
                count = sum(1 for r in all_reqs if r == item)
                print(f"  • {item:50} ({count}x)")

    print()
    print("✅ VALID REQUIREMENTS")
    print("-" * 100)
    valid = sorted(set(categories["VALID"]))
    for item in valid:
        count = sum(1 for r in all_reqs if r == item)
        print(f"  • {item:50} ({count}x)")


if __name__ == "__main__":
    main()
