#!/usr/bin/env python3
"""Test correct Boeing job (index 0)."""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.nlp.ner import JobNERExtractor
from src.nlp.domains import detect_domain


def load_job(company: str, job_idx: int) -> dict:
    """Load job description."""
    jobs_file = project_root / f"data/extracted_jobs/{company.lower()}_jobs.json"
    with open(jobs_file) as f:
        jobs = json.load(f)
    return jobs[job_idx]


def load_expected(file_name: str) -> dict:
    """Load expected extractions."""
    expected_file = project_root / f"data/extracted_jobs/{file_name}"
    with open(expected_file) as f:
        return json.load(f)


def compare_f1(extracted: dict, expected: dict) -> dict:
    """Calculate F1 scores."""
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
        }

    return results


def main():
    print("=== Boeing Job Correction Test ===\n")

    # Test Blue Origin (baseline)
    print("Blue Origin - Director of Vehicle G&C (Job 1, Aerospace)")
    print("-" * 60)
    job_bo = load_job("blue origin", 1)
    domain_bo = detect_domain(job_bo["description"])
    extractor_bo = JobNERExtractor()
    result_bo = extractor_bo.extract_all(job_bo["description"])
    expected_bo = load_expected("expected_extractions.json")
    metrics_bo = compare_f1(result_bo, expected_bo)

    print(f"Domain: {domain_bo.value}")
    print(f"Skills:  F1={metrics_bo['skills']['f1']} | Tech: F1={metrics_bo['technologies']['f1']} | Req: F1={metrics_bo['requirements']['f1']}")

    # Test Boeing CORRECT job
    print("\n\nBoeing - Senior Software Engineer / Boeing Translation Engine (Job 0, Aerospace/Sensor)")
    print("-" * 60)
    job_b = load_job("boeing", 0)
    domain_b = detect_domain(job_b["description"])
    extractor_b = JobNERExtractor()
    result_b = extractor_b.extract_all(job_b["description"])
    expected_b = load_expected("expected_extractions-2.json")
    metrics_b = compare_f1(result_b, expected_b)

    print(f"Domain: {domain_b.value}")
    print(f"Skills:  F1={metrics_b['skills']['f1']} | Tech: F1={metrics_b['technologies']['f1']} | Req: F1={metrics_b['requirements']['f1']}")

    # Summary
    print("\n\n=== SUMMARY ===")
    print(f"{'Job':<50} {'Skills':<10} {'Tech':<10} {'Req':<10}")
    print("-" * 80)
    print(f"{'Blue Origin (Aerospace)':<50} {metrics_bo['skills']['f1']:<10} {metrics_bo['technologies']['f1']:<10} {metrics_bo['requirements']['f1']:<10}")
    print(f"{'Boeing (BTE - Sensor/ARINC)':<50} {metrics_b['skills']['f1']:<10} {metrics_b['technologies']['f1']:<10} {metrics_b['requirements']['f1']:<10}")


if __name__ == "__main__":
    main()
