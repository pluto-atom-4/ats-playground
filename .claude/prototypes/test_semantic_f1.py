#!/usr/bin/env python3
"""Test F1 calculation with semantic matching."""

import json
import sys
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.nlp.ner import JobNERExtractor
from src.nlp.requirement_normalizer import RequirementNormalizer


def load_job(company: str, job_idx: int) -> Any:
    jobs_file = project_root / f"data/extracted_jobs/{company.lower()}_jobs.json"
    with open(jobs_file) as f:
        jobs = json.load(f)
    return jobs[job_idx]


def load_expected(file_name: str) -> Any:
    expected_file = project_root / f"data/extracted_jobs/{file_name}"
    with open(expected_file) as f:
        return json.load(f)


def calculate_semantic_f1(extracted_reqs, expected_reqs):
    """Calculate F1 using semantic matching instead of exact match.

    Uses fuzzy matching to find semantically equivalent requirements.
    """
    normalizer = RequirementNormalizer()

    # Track matches with confidence threshold
    matched_extracted = set()
    matched_expected = set()

    for expected in expected_reqs:
        best_match, score = normalizer.find_matching_requirement(
            expected, extracted_reqs, threshold=0.75
        )
        if best_match and score >= 0.75:
            matched_extracted.add(best_match)
            matched_expected.add(expected)

    correct = len(matched_expected)
    missing = len(expected_reqs) - correct
    extra = len(extracted_reqs) - len(matched_extracted)

    precision = len(matched_extracted) / len(extracted_reqs) if extracted_reqs else 0
    recall = correct / len(expected_reqs) if expected_reqs else 0
    f1 = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    return {
        "f1": round(f1, 2),
        "precision": round(precision, 2),
        "recall": round(recall, 2),
        "correct": correct,
        "missing": missing,
        "extra": extra,
        "matched_pairs": list(zip(sorted(matched_expected), sorted(matched_extracted)))
    }


def main():
    print("=" * 80)
    print("SEMANTIC F1 EVALUATION (Fuzzy Matching)")
    print("=" * 80)

    # Test Boeing
    print("\n\nBOEING - Senior Software Engineer")
    print("-" * 80)
    job_b = load_job("boeing", 0)
    expected_b = load_expected("expected_extractions-2.json")

    extractor_b = JobNERExtractor(company_name="boeing")
    result_b = extractor_b.extract_all_with_confidence(job_b["description"])

    extracted_reqs = set(item["value"] for item in result_b["requirements"])
    expected_reqs = set(expected_b["requirements"])

    # Exact match F1
    correct_exact = extracted_reqs & expected_reqs
    precision_exact = len(correct_exact) / len(extracted_reqs) if extracted_reqs else 0
    recall_exact = len(correct_exact) / len(expected_reqs) if expected_reqs else 0
    f1_exact = (
        2 * (precision_exact * recall_exact) / (precision_exact + recall_exact)
        if (precision_exact + recall_exact) > 0
        else 0
    )

    # Semantic F1
    semantic_result = calculate_semantic_f1(extracted_reqs, expected_reqs)

    print(f"Exact Match:    F1={f1_exact:.2f} (P={precision_exact:.2f}, R={recall_exact:.2f})")
    print(f"Semantic Match: F1={semantic_result['f1']:.2f} (P={semantic_result['precision']:.2f}, R={semantic_result['recall']:.2f})")
    print(f"Improvement: +{(semantic_result['f1'] - f1_exact):.2f} F1 ({(semantic_result['correct'] - len(correct_exact))} more matched)")

    print("\nSemantic Matches:")
    for exp, ext in semantic_result["matched_pairs"][:5]:
        print(f"  ✓ Expected: {exp[:60]}")
        print(f"    Extracted: {ext[:60]}")

    print(f"\nRemaining Missing ({semantic_result['missing']}):")
    for req in sorted(expected_reqs - set(pair[0] for pair in semantic_result["matched_pairs"]))[:3]:
        print(f"  - {req[:70]}")

    # Same for Blue Origin
    print("\n\nBLUE ORIGIN - Director of Vehicle G&C")
    print("-" * 80)
    job_bo = load_job("blue origin", 1)
    expected_bo = load_expected("expected_extractions.json")

    extractor_bo = JobNERExtractor(company_name="blue origin")
    result_bo = extractor_bo.extract_all_with_confidence(job_bo["description"])

    extracted_reqs_bo = set(item["value"] for item in result_bo["requirements"])
    expected_reqs_bo = set(expected_bo["requirements"])

    # Exact match F1
    correct_exact_bo = extracted_reqs_bo & expected_reqs_bo
    precision_exact_bo = len(correct_exact_bo) / len(extracted_reqs_bo) if extracted_reqs_bo else 0
    recall_exact_bo = len(correct_exact_bo) / len(expected_reqs_bo) if expected_reqs_bo else 0
    f1_exact_bo = (
        2 * (precision_exact_bo * recall_exact_bo) / (precision_exact_bo + recall_exact_bo)
        if (precision_exact_bo + recall_exact_bo) > 0
        else 0
    )

    # Semantic F1
    semantic_result_bo = calculate_semantic_f1(extracted_reqs_bo, expected_reqs_bo)

    print(f"Exact Match:    F1={f1_exact_bo:.2f} (P={precision_exact_bo:.2f}, R={recall_exact_bo:.2f})")
    print(f"Semantic Match: F1={semantic_result_bo['f1']:.2f} (P={semantic_result_bo['precision']:.2f}, R={semantic_result_bo['recall']:.2f})")
    print(f"Improvement: +{(semantic_result_bo['f1'] - f1_exact_bo):.2f} F1 ({(semantic_result_bo['correct'] - len(correct_exact_bo))} more matched)")


if __name__ == "__main__":
    main()
