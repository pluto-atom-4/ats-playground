#!/usr/bin/env python3
"""Test Phase 4: Company-specific parser integration."""

import json
import sys
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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


def compare_f1(extracted: dict, expected: dict) -> Any:
    results = {}
    for category in ["skills", "technologies", "requirements"]:
        extracted_set = set(extracted.get(category, []))
        expected_set = set(expected[category])

        correct = extracted_set & expected_set
        precision = len(correct) / len(extracted_set) if extracted_set else 0
        recall = len(correct) / len(expected_set) if expected_set else 0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        results[category] = {
            "f1": round(f1, 2),
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "correct": len(correct),
            "missing": len(expected_set - extracted_set),
            "extra": len(extracted_set - expected_set),
        }

    return results


def main():
    print("=" * 80)
    print("PHASE 4: COMPANY-SPECIFIC PARSER INTEGRATION TEST")
    print("=" * 80)

    # Test 1: Blue Origin (with company parser)
    print("\n\n1. BLUE ORIGIN - Director of Vehicle G&C (Job 1)")
    print("-" * 80)
    job_bo = load_job("blue origin", 1)
    expected_bo = load_expected("expected_extractions.json")

    extractor_bo = JobNERExtractor(company_name="blue origin")
    result_bo = extractor_bo.extract_all(job_bo["description"])
    metrics_bo = compare_f1(result_bo, expected_bo)

    print(f"Domain: {result_bo['detected_domain']}")
    print(f"Skills:       F1={metrics_bo['skills']['f1']:<5} (P={metrics_bo['skills']['precision']}, R={metrics_bo['skills']['recall']}) [correct={metrics_bo['skills']['correct']}, missing={metrics_bo['skills']['missing']}]")
    print(f"Technologies: F1={metrics_bo['technologies']['f1']:<5} (P={metrics_bo['technologies']['precision']}, R={metrics_bo['technologies']['recall']}) [correct={metrics_bo['technologies']['correct']}, missing={metrics_bo['technologies']['missing']}]")
    print(f"Requirements: F1={metrics_bo['requirements']['f1']:<5} (P={metrics_bo['requirements']['precision']}, R={metrics_bo['requirements']['recall']}) [correct={metrics_bo['requirements']['correct']}, missing={metrics_bo['requirements']['missing']}]")

    # Test 2: Boeing (with company parser)
    print("\n\n2. BOEING - Senior Software Engineer / Boeing Translation Engine (Job 0)")
    print("-" * 80)
    job_b = load_job("boeing", 0)
    expected_b = load_expected("expected_extractions-2.json")

    extractor_b = JobNERExtractor(company_name="boeing")
    result_b = extractor_b.extract_all(job_b["description"])
    metrics_b = compare_f1(result_b, expected_b)

    print(f"Domain: {result_b['detected_domain']}")
    print(f"Skills:       F1={metrics_b['skills']['f1']:<5} (P={metrics_b['skills']['precision']}, R={metrics_b['skills']['recall']}) [correct={metrics_b['skills']['correct']}, missing={metrics_b['skills']['missing']}]")
    print(f"Technologies: F1={metrics_b['technologies']['f1']:<5} (P={metrics_b['technologies']['precision']}, R={metrics_b['technologies']['recall']}) [correct={metrics_b['technologies']['correct']}, missing={metrics_b['technologies']['missing']}]")
    print(f"Requirements: F1={metrics_b['requirements']['f1']:<5} (P={metrics_b['requirements']['precision']}, R={metrics_b['requirements']['recall']}) [correct={metrics_b['requirements']['correct']}, missing={metrics_b['requirements']['missing']}]")

    # Summary comparison
    print("\n\n" + "=" * 80)
    print("SUMMARY: REQUIREMENTS F1 COMPARISON")
    print("=" * 80)
    print(f"{'Company':<20} {'Before (Generic)':<20} {'After (Company-Specific)':<25}")
    print("-" * 80)
    print(f"{'Blue Origin':<20} {'0.67':<20} {metrics_bo['requirements']['f1']:<25}")
    print(f"{'Boeing':<20} {'0.18':<20} {metrics_b['requirements']['f1']:<25}")

    # Detailed Boeing extractions
    print("\n\nBoeing Requirements (Extracted):")
    for req in sorted(result_b["requirements"])[:10]:
        print(f"  - {req}")

    print("\nBoeing Requirements (Expected - first 10):")
    for req in sorted(expected_b["requirements"])[:10]:
        print(f"  - {req}")


if __name__ == "__main__":
    main()
