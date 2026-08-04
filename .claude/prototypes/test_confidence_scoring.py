#!/usr/bin/env python3
"""Test Phase 5: Confidence scoring system."""

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


def main():
    print("=" * 80)
    print("PHASE 5: CONFIDENCE SCORING SYSTEM TEST")
    print("=" * 80)

    # Test 1: Blue Origin with confidence
    print("\n\n1. BLUE ORIGIN - Director of Vehicle G&C (Job 1)")
    print("-" * 80)
    job_bo = load_job("blue origin", 1)
    extractor_bo = JobNERExtractor(company_name="blue origin")
    result_bo = extractor_bo.extract_all_with_confidence(job_bo["description"])

    print(f"Domain: {result_bo['detected_domain']}")
    print(f"\nSkills (avg confidence: {result_bo['metrics']['avg_skills_confidence']})")
    for item in result_bo["skills"][:5]:
        print(f"  [{item['confidence']:.2f}] {item['value']}")
    print(f"  ... and {len(result_bo['skills']) - 5} more")

    print(f"\nTechnologies (avg confidence: {result_bo['metrics']['avg_tech_confidence']})")
    for item in result_bo["technologies"][:5]:
        print(f"  [{item['confidence']:.2f}] {item['value']}")
    print(f"  ... and {len(result_bo['technologies']) - 5} more")

    print(f"\nRequirements (avg confidence: {result_bo['metrics']['avg_req_confidence']})")
    for item in result_bo["requirements"][:5]:
        print(f"  [{item['confidence']:.2f}] {item['value']}")

    # Test 2: Boeing with confidence
    print("\n\n2. BOEING - Senior Software Engineer / Boeing Translation Engine (Job 0)")
    print("-" * 80)
    job_b = load_job("boeing", 0)
    extractor_b = JobNERExtractor(company_name="boeing")
    result_b = extractor_b.extract_all_with_confidence(job_b["description"])

    print(f"Domain: {result_b['detected_domain']}")
    print(f"\nSkills (avg confidence: {result_b['metrics']['avg_skills_confidence']})")
    for item in result_b["skills"][:5]:
        print(f"  [{item['confidence']:.2f}] {item['value']}")
    print(f"  ... and {len(result_b['skills']) - 5} more")

    print(f"\nTechnologies (avg confidence: {result_b['metrics']['avg_tech_confidence']})")
    for item in result_b["technologies"][:5]:
        print(f"  [{item['confidence']:.2f}] {item['value']}")

    print(f"\nRequirements (avg confidence: {result_b['metrics']['avg_req_confidence']})")
    for item in result_b["requirements"][:5]:
        print(f"  [{item['confidence']:.2f}] {item['value']}")

    # Summary
    print("\n\n" + "=" * 80)
    print("CONFIDENCE SUMMARY")
    print("=" * 80)
    print(f"{'Company':<20} {'Skills':<15} {'Tech':<15} {'Req':<15}")
    print("-" * 80)
    print(
        f"{'Blue Origin':<20} {result_bo['metrics']['avg_skills_confidence']:<15} {result_bo['metrics']['avg_tech_confidence']:<15} {result_bo['metrics']['avg_req_confidence']:<15}"
    )
    print(
        f"{'Boeing':<20} {result_b['metrics']['avg_skills_confidence']:<15} {result_b['metrics']['avg_tech_confidence']:<15} {result_b['metrics']['avg_req_confidence']:<15}"
    )


if __name__ == "__main__":
    main()
