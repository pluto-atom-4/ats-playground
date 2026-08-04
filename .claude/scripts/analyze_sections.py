#!/usr/bin/env python
"""Analyze markdown sections and their contribution to skill extraction.

Dev tool: inspects the section structure of `data/extracted_jobs/*_jobs.json`
descriptions and reports, per section name, whether `Preprocessor` would
process it for skills/technologies/requirements extraction or skip it as
benefits/legal/hiring-process boilerplate.

Uses the real pipeline (`Preprocessor._extract_markdown_sections` and
`Preprocessor.SKIP_SECTIONS`) rather than a hand-rolled copy, so this report
stays accurate as the skip-list and section-extraction logic evolve --
no separate list to keep in sync (Issue #221).
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

# Run standalone (not via `python -m`), so the repo root -- needed for
# `Preprocessor`'s internal `from src.tokenization...` absolute imports --
# isn't on sys.path by default. Insert it before importing.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.tokenization.preprocessor import Preprocessor  # noqa: E402


def should_skip_section(section_name: str) -> bool:
    """Check if section should be skipped, using the real pipeline's denylist.

    Mirrors the substring-containment check in
    `Preprocessor._extract_entities_by_section` (section name normalized to
    lowercase with underscores treated as spaces before matching).
    """
    section_lower = section_name.lower().replace("_", " ")
    return any(skip_kw in section_lower for skip_kw in Preprocessor.SKIP_SECTIONS)


def main() -> None:
    """Analyze sections across all jobs."""
    print("=" * 80)
    print("MARKDOWN SECTION ANALYSIS FOR SKILL EXTRACTION")
    print("=" * 80)
    print()

    # Collect statistics
    section_stats: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "jobs": [], "skipped": False, "sample_content": ""}
    )

    job_files = list(Path("data/extracted_jobs").glob("*_jobs.json"))
    total_jobs = 0

    # `_extract_markdown_sections` doesn't touch spaCy state, but it's an
    # instance method, so a real Preprocessor (which loads the spaCy model)
    # is instantiated once and reused across all jobs below.
    preprocessor = Preprocessor()

    for job_file in sorted(job_files):
        if "preprocessed" in job_file.name:
            continue

        with open(job_file) as f:
            jobs = json.load(f)

        for job in jobs:
            total_jobs += 1
            desc = job.get("description", "")
            title = job.get("title", "Unknown")[:40]

            sections = preprocessor._extract_markdown_sections(desc)

            for section_name, content in sections.items():
                if section_name == "description":
                    continue

                section_lower = section_name.lower()
                stat = section_stats[section_lower]
                stat["count"] += 1
                stat["jobs"].append(title)
                stat["skipped"] = should_skip_section(section_name)

                if not stat["sample_content"] and len(content) > 50:
                    stat["sample_content"] = content[:100].replace("\n", " ")

    # Print sections to PROCESS (skills extraction)
    print(f"\n📋 SECTIONS TO PROCESS FOR SKILLS EXTRACTION ({total_jobs} jobs)")
    print("-" * 80)

    for section_name in sorted(section_stats.keys()):
        stat = section_stats[section_name]
        if not stat["skipped"]:
            print(f"\n✓ {section_name.upper()}")
            print(f"  Found in: {stat['count']} jobs")
            if stat["sample_content"]:
                print(f"  Sample: {stat['sample_content']}...")
            print(f"  Jobs: {', '.join(stat['jobs'][:2])}")

    # Print sections to SKIP (metadata)
    print("\n\n🚫 SECTIONS TO SKIP (METADATA, NOT SKILLS)")
    print("-" * 80)

    for section_name in sorted(section_stats.keys()):
        stat = section_stats[section_name]
        if stat["skipped"]:
            print(f"\n✗ {section_name.upper()}")
            print(f"  Found in: {stat['count']} jobs")
            if stat["sample_content"]:
                print(f"  Sample: {stat['sample_content']}...")

    # Summary
    print("\n\n📊 SUMMARY")
    print("-" * 80)
    process_count = sum(1 for s in section_stats.values() if not s["skipped"])
    skip_count = sum(1 for s in section_stats.values() if s["skipped"])
    print(f"Total unique section types: {len(section_stats)}")
    print(f"Sections to process: {process_count}")
    print(f"Sections to skip: {skip_count}")
    print(f"Total jobs analyzed: {total_jobs}")
    print(f"\nSkip-list size (Preprocessor.SKIP_SECTIONS): {len(Preprocessor.SKIP_SECTIONS)} entries")


if __name__ == "__main__":
    main()
