#!/usr/bin/env python
"""Analyze problematic one-word skills: numbers, vague adjectives, artifacts."""

import json
import re
from collections import defaultdict
from pathlib import Path


def categorize_one_word(word: str) -> str:
    """Categorize problematic one-word items."""
    # Numbers
    if re.match(r"^\d+(\.\d+)?$", word):
        return "NUMBER"

    word_lower = word.lower()

    # Vague/meaningless adjectives
    vague_adjectives = {
        "qualified",
        "binary",
        "innovation",
        "intermediate",
        "specialized",
        "robust",
        "comprehensive",
        "thorough",
        "effective",
        "efficient",
        "practical",
        "strategic",
        "innovative",
        "adaptive",
        "dynamic",
        "progressive",
        "smart",
        "rigorous",
        "pragmatic",
        "proactive",
    }

    if word_lower in vague_adjectives:
        return "VAGUE_ADJ"

    # Acronyms/codes that are artifacts
    # Hardware/embedded systems: DSP, MMU, AXI, RAM, ROM, UART, SPI, I2C, CAN
    # Other tech: AWS, GCP, SQL, API, IOT, ROS, GPU, CPU, NVM, DDR, SoC, RTL
    known_tech_acronyms = {
        "AWS",
        "GCP",
        "SQL",
        "API",
        "IOT",
        "ROS",
        "GPU",
        "CPU",
        "DSP",
        "MMU",
        "AXI",
        "RAM",
        "ROM",
        "UART",
        "SPI",
        "I2C",
        "CAN",
        "NVM",
        "DDR",
        "SoC",
        "RTL",
    }
    if len(word) <= 3 and word.isupper() and word not in known_tech_acronyms:
        return "ARTIFACT_CODE"

    # Single letters (obvious artifacts)
    if len(word) == 1:
        return "SINGLE_CHAR"

    # Company/proper nouns (artifacts)
    if word in ("Google", "Facebook", "Amazon", "Microsoft", "Apple", "Tesla", "Netflix", "Forbes", "WSJ"):
        return "BRAND"

    # Partial words/fragments
    if word.endswith("ing") and len(word) < 8:
        return "GERUND_FRAGMENT"

    return "KEEP"


def main():
    """Analyze problematic one-word items."""
    jobs_file = Path("data/extracted_jobs/preprocessed_jobs.json")
    if not jobs_file.exists():
        print(f"❌ File not found: {jobs_file}")
        return

    with open(jobs_file) as f:
        jobs = json.load(f)

    print("=" * 100)
    print("PROBLEMATIC ONE-WORD ITEMS ANALYSIS")
    print("=" * 100)
    print()

    categories = defaultdict(lambda: defaultdict(int))
    all_items = {}
    total_one_word = 0

    for job_idx, job in enumerate(jobs, 1):
        skills = job.get("skills", [])
        requirements = job.get("requirements", [])

        for skill in skills + requirements:
            if " " not in skill:  # One-word
                total_one_word += 1
                category = categorize_one_word(skill)
                categories[category][skill] += 1
                all_items[skill] = category

    print("📊 SUMMARY")
    print("-" * 100)
    print(f"Total one-word items: {total_one_word}")
    print()

    problematic_categories = ["NUMBER", "VAGUE_ADJ", "ARTIFACT_CODE", "SINGLE_CHAR", "BRAND", "GERUND_FRAGMENT"]
    total_problematic = sum(len(items) for cat in problematic_categories for items in [categories[cat].values()])

    print(f"Problematic items: {total_problematic}")
    print(f"Quality: {(total_one_word - total_problematic) / total_one_word * 100:.1f}% good")
    print()

    for category in problematic_categories:
        if categories[category]:
            items = categories[category]
            print(f"\n🔴 {category} ({len(items)} unique items)")
            print("-" * 100)
            for item in sorted(items.keys(), key=lambda x: items[x], reverse=True)[:15]:
                count = items[item]
                print(f"  • {item:30} ({count} occurrences)")
            if len(items) > 15:
                print(f"  ... and {len(items) - 15} more")

    # Summary for filtering
    print()
    print("📋 FILTERING RECOMMENDATIONS")
    print("-" * 100)

    vague_adj = sorted(categories["VAGUE_ADJ"].keys())
    if vague_adj:
        print(f"\nVague adjectives to filter ({len(vague_adj)}):")
        for adj in vague_adj:
            print(f'    "{adj}",')

    print()
    print(f"Total items to filter: {sum(len(v) for k, v in categories.items() if k in problematic_categories)}")


if __name__ == "__main__":
    main()
