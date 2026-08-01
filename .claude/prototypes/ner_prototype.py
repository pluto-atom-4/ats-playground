#!/usr/bin/env python3
"""NER prototype: Extract job entities and compare with expected output."""

import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.nlp.ner import JobNERExtractor


def load_job_data(job_idx: int = 1) -> Any:
    """Load job from extracted_jobs JSON."""
    jobs_file = project_root / "data/extracted_jobs/blue origin_jobs.json"
    with open(jobs_file) as f:
        jobs = json.load(f)
    return jobs[job_idx]


def load_expected() -> Any:
    """Load expected extractions."""
    expected_file = project_root / "data/extracted_jobs/expected_extractions.json"
    with open(expected_file) as f:
        return json.load(f)


def compare_extractions(extracted: dict, expected: dict) -> Any:
    """Compare extracted vs expected and report precision/recall."""
    results = {}

    for category in ["skills", "technologies", "requirements"]:
        extracted_set = set(extracted[category])
        expected_set = set(expected[category])

        # Exact matches
        correct = extracted_set & expected_set
        missing = expected_set - extracted_set
        extra = extracted_set - expected_set

        precision = len(correct) / len(extracted_set) if extracted_set else 0
        recall = len(correct) / len(expected_set) if expected_set else 0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        results[category] = {
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "f1": round(f1, 2),
            "correct": len(correct),
            "missing": len(missing),
            "extra": len(extra),
            "missing_examples": list(missing)[:3],
            "extra_examples": list(extra)[:3],
        }

    return results


def main():
    print("=== Job NER Extraction Prototype ===\n")

    # Load data
    job = load_job_data(job_idx=1)
    expected = load_expected()

    print(f"Job: {job['title']}")
    print(f"Description length: {len(job['description'])} chars\n")

    # Extract
    extractor = JobNERExtractor()
    extracted = extractor.extract_all(job["description"])

    # Compare
    comparison = compare_extractions(extracted, expected)

    # Report
    for category, metrics in comparison.items():
        print(f"\n{category.upper()}")
        print(f"  Precision: {metrics['precision']} | Recall: {metrics['recall']} | F1: {metrics['f1']}")
        print(f"  Correct: {metrics['correct']} | Missing: {metrics['missing']} | Extra: {metrics['extra']}")
        if metrics["missing_examples"]:
            print(f"  Missing (first 3): {metrics['missing_examples']}")
        if metrics["extra_examples"]:
            print(f"  Extra (first 3): {metrics['extra_examples']}")

    # Save results
    output_file = project_root / ".claude/prototypes/ner_results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(
            {
                "job_title": job["title"],
                "extracted": extracted,
                "expected": expected,
                "metrics": comparison,
            },
            f,
            indent=2,
        )
    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()
