#!/usr/bin/env python3
"""Test Phase 6: Narrative requirement extraction."""

import json
import sys
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import spacy

from src.nlp.narrative import NarrativeRequirementExtractor
from src.nlp.ner import JobNERExtractor


def load_job(company: str, job_idx: int) -> Any:
    jobs_file = project_root / f"data/extracted_jobs/{company.lower()}_jobs.json"
    with open(jobs_file) as f:
        jobs = json.load(f)
    return jobs[job_idx]


def load_expected(file_name: str) -> Any:
    expected_file = project_root / f"data/extracted_jobs/{file_name}"
    with open(expected_file) as f:
        return json.load(f)


def main():
    print("=" * 80)
    print("PHASE 6: NARRATIVE REQUIREMENT EXTRACTION TEST")
    print("=" * 80)

    # Load Boeing job
    job_b = load_job("boeing", 0)
    expected_b = load_expected("expected_extractions-2.json")
    desc = job_b["description"]

    # Test narrative extractor directly
    nlp = spacy.load("en_core_web_md")
    narrative_extractor = NarrativeRequirementExtractor(nlp)

    print("\n\n1. NARRATIVE REQUIREMENT EXTRACTION (Direct)")
    print("-" * 80)

    narrative_reqs = narrative_extractor.extract_narrative_requirements(desc)
    print(f"Narrative requirements found: {len(narrative_reqs)}\n")
    for req in sorted(narrative_reqs)[:10]:
        print(f"  - {req}")
    if len(narrative_reqs) > 10:
        print(f"  ... and {len(narrative_reqs) - 10} more")

    # Test integrated extraction with confidence
    print("\n\n2. INTEGRATED EXTRACTION (Structured + Narrative)")
    print("-" * 80)

    extractor_b = JobNERExtractor(company_name="boeing")
    result_b = extractor_b.extract_all_with_confidence(job_b["description"])

    print(f"Requirements found: {len(result_b['requirements'])}\n")

    # Compare with expected
    extracted_reqs = set(item["value"] for item in result_b["requirements"])
    expected_reqs = set(expected_b["requirements"])

    correct = extracted_reqs & expected_reqs
    missing = expected_reqs - extracted_reqs
    extra = extracted_reqs - expected_reqs

    print(f"Correct: {len(correct)}/{len(expected_reqs)}")
    print(f"Missing: {len(missing)}")
    print(f"Extra: {len(extra)}\n")

    # Calculate F1
    precision = len(correct) / len(extracted_reqs) if extracted_reqs else 0
    recall = len(correct) / len(expected_reqs) if expected_reqs else 0
    f1 = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    print(f"F1 Score: {f1:.2f} (Precision: {precision:.2f}, Recall: {recall:.2f})")

    # Show extracted requirements with confidence
    print("\n\nExtracted Requirements (with confidence):")
    for item in sorted(result_b["requirements"], key=lambda x: x["confidence"], reverse=True)[:10]:
        marker = "✓" if item["value"] in correct else ("?" if item["value"] in extra else " ")
        print(f"  [{marker}] [{item['confidence']:.2f}] {item['value'][:70]}")

    print("\n\nMissing Requirements (expected but not extracted):")
    for req in sorted(missing)[:5]:
        print(f"  - {req[:70]}")

    # Test narrative skills extraction
    print("\n\n3. NARRATIVE SKILLS EXTRACTION")
    print("-" * 80)

    narrative_skills = narrative_extractor.extract_skill_requirements(desc)
    print(f"Skills from narrative: {len(narrative_skills)}\n")
    for skill in sorted(narrative_skills)[:10]:
        print(f"  - {skill}")


if __name__ == "__main__":
    main()
