#!/usr/bin/env python3
"""Test domain detection and domain-specific extraction."""

import json
import sys
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.nlp.domains import detect_domain
from src.nlp.ner import JobNERExtractor


def load_job(company: str, job_idx: int) -> Any:
    """Load job description."""
    jobs_file = project_root / f"data/extracted_jobs/{company.lower()}_jobs.json"
    with open(jobs_file) as f:
        jobs = json.load(f)
    return jobs[job_idx]


def load_expected(file_name: str) -> Any:
    """Load expected extractions."""
    expected_file = project_root / f"data/extracted_jobs/{file_name}"
    with open(expected_file) as f:
        return json.load(f)


def compare_f1(extracted: dict, expected: dict) -> Any:
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
        }

    return results


def main():
    print("=== Domain Detection & Specific Keyphrase Testing ===\n")

    # Test 1: Blue Origin (Aerospace)
    print("TEST 1: Blue Origin - Director of Vehicle G&C (Aerospace)")
    print("-" * 60)
    job1 = load_job("blue origin", 1)
    domain1 = detect_domain(job1["description"])
    print(f"Detected domain: {domain1.value}")

    extractor1 = JobNERExtractor()
    result1 = extractor1.extract_all(job1["description"])
    expected1 = load_expected("expected_extractions.json")
    metrics1 = compare_f1(result1, expected1)

    print(f"Skills:   F1={metrics1['skills']['f1']} (P={metrics1['skills']['precision']}, R={metrics1['skills']['recall']})")
    print(f"Tech:     F1={metrics1['technologies']['f1']} (P={metrics1['technologies']['precision']}, R={metrics1['technologies']['recall']})")
    print(f"Req:      F1={metrics1['requirements']['f1']} (P={metrics1['requirements']['precision']}, R={metrics1['requirements']['recall']})")

    # Test 2: Boeing (Software)
    print("\n\nTEST 2: Boeing - Senior Software Engineer | Rocky Program (Software)")
    print("-" * 60)
    job2 = load_job("boeing", 1)
    domain2 = detect_domain(job2["description"])
    print(f"Detected domain: {domain2.value}")

    extractor2 = JobNERExtractor()
    result2 = extractor2.extract_all(job2["description"])
    expected2 = load_expected("expected_extractions-2.json")
    metrics2 = compare_f1(result2, expected2)

    print(f"Skills:   F1={metrics2['skills']['f1']} (P={metrics2['skills']['precision']}, R={metrics2['skills']['recall']})")
    print(f"Tech:     F1={metrics2['technologies']['f1']} (P={metrics2['technologies']['precision']}, R={metrics2['technologies']['recall']})")
    print(f"Req:      F1={metrics2['requirements']['f1']} (P={metrics2['requirements']['precision']}, R={metrics2['requirements']['recall']})")

    # Summary
    print("\n\n=== SUMMARY ===")
    print(f"{'Domain':<30} {'Skills':<15} {'Tech':<15} {'Req':<15}")
    print("-" * 75)
    print(f"{'Blue Origin (Aerospace)':<30} {metrics1['skills']['f1']:<15} {metrics1['technologies']['f1']:<15} {metrics1['requirements']['f1']:<15}")
    print(f"{'Boeing (Software)':<30} {metrics2['skills']['f1']:<15} {metrics2['technologies']['f1']:<15} {metrics2['requirements']['f1']:<15}")


if __name__ == "__main__":
    main()
