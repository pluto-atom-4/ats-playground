#!/usr/bin/env python3
"""Phase 3: Cross-domain validation on all available jobs."""

import json
import sys
from collections import defaultdict
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.nlp.domains import detect_domain
from src.nlp.ner import JobNERExtractor


def load_all_jobs():
    """Load all available jobs from all sources."""
    jobs_data = []
    jobs_dir = project_root / "data/extracted_jobs"

    # Known job sources with indices and expected files
    sources = [
        ("blue origin", "expected_extractions.json", [1]),  # Job 1 (G&C)
        ("boeing", "expected_extractions-2.json", [0]),      # Job 0 (BTE)
    ]

    for company, expected_file, job_indices in sources:
        jobs_file = jobs_dir / f"{company}_jobs.json"
        expected_path = jobs_dir / expected_file

        if not jobs_file.exists() or not expected_path.exists():
            continue

        with open(jobs_file) as f:
            jobs = json.load(f)
        with open(expected_path) as f:
            expected = json.load(f)

        for idx in job_indices:
            if idx < len(jobs):
                jobs_data.append({
                    "company": company,
                    "job_idx": idx,
                    "title": jobs[idx]["title"],
                    "description": jobs[idx]["description"],
                    "expected": expected,
                })

    return jobs_data


def calculate_metrics(extracted: dict, expected: dict) -> dict:
    """Calculate precision, recall, F1 for each category."""
    metrics = {}

    for category in ["skills", "technologies", "requirements"]:
        extracted_set = set(extracted.get(category, []))
        expected_set = set(expected[category])

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

        metrics[category] = {
            "f1": round(f1, 2),
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "correct": len(correct),
            "missing": len(missing),
            "extra": len(extra),
        }

    return metrics


def main():
    print("=" * 80)
    print("PHASE 3: CROSS-DOMAIN VALIDATION")
    print("=" * 80)

    jobs = load_all_jobs()
    print(f"\nLoaded {len(jobs)} jobs for validation\n")

    # Test each job
    results = []
    domain_stats = defaultdict(lambda: {"skills": [], "technologies": [], "requirements": []})

    for job_data in jobs:
        company = job_data["company"]
        title = job_data["title"]
        description = job_data["description"]
        expected = job_data["expected"]

        print(f"\n{company.upper()} - {title}")
        print("-" * 80)

        # Detect domain
        domain = detect_domain(description)
        print(f"Domain: {domain.value}")

        # Extract (with company-specific parser and confidence scores)
        extractor = JobNERExtractor(company_name=company)
        extracted_with_conf = extractor.extract_all_with_confidence(description)

        # Convert for compatibility with existing metric calculation
        extracted = {
            "skills": [item["value"] for item in extracted_with_conf["skills"]],
            "technologies": [item["value"] for item in extracted_with_conf["technologies"]],
            "requirements": [item["value"] for item in extracted_with_conf["requirements"]],
            "detected_domain": extracted_with_conf["detected_domain"],
        }

        # Calculate metrics
        metrics = calculate_metrics(extracted, expected)

        # Get confidence metrics
        conf_skills = extracted_with_conf["metrics"]["avg_skills_confidence"]
        conf_tech = extracted_with_conf["metrics"]["avg_tech_confidence"]
        conf_req = extracted_with_conf["metrics"]["avg_req_confidence"]

        # Display metrics with confidence
        print(f"Skills:   F1={metrics['skills']['f1']:<5} (P={metrics['skills']['precision']}, R={metrics['skills']['recall']}) Conf={conf_skills:<5} [{metrics['skills']['correct']}/{len(expected['skills'])}]")
        print(f"Tech:     F1={metrics['technologies']['f1']:<5} (P={metrics['technologies']['precision']}, R={metrics['technologies']['recall']}) Conf={conf_tech:<5} [{metrics['technologies']['correct']}/{len(expected['technologies'])}]")
        print(f"Req:      F1={metrics['requirements']['f1']:<5} (P={metrics['requirements']['precision']}, R={metrics['requirements']['recall']}) Conf={conf_req:<5} [{metrics['requirements']['correct']}/{len(expected['requirements'])}]")

        # Track results
        results.append({
            "company": company,
            "title": title,
            "domain": domain.value,
            "metrics": metrics,
            "confidence": {
                "skills": conf_skills,
                "technologies": conf_tech,
                "requirements": conf_req,
            }
        })

        # Track domain stats
        for category in ["skills", "technologies", "requirements"]:
            domain_stats[domain.value][category].append(metrics[category]["f1"])

    # Summary by domain
    print("\n\n" + "=" * 80)
    print("DOMAIN SUMMARY")
    print("=" * 80)

    print(f"\n{'Domain':<15} {'Skills F1':<15} {'Tech F1':<15} {'Req F1':<15}")
    print("-" * 60)

    for domain in sorted(domain_stats.keys()):
        stats = domain_stats[domain]
        avg_skills = round(sum(stats["skills"]) / len(stats["skills"]), 2) if stats["skills"] else 0
        avg_tech = round(sum(stats["technologies"]) / len(stats["technologies"]), 2) if stats["technologies"] else 0
        avg_req = round(sum(stats["requirements"]) / len(stats["requirements"]), 2) if stats["requirements"] else 0

        print(f"{domain:<15} {avg_skills:<15} {avg_tech:<15} {avg_req:<15}")

    # Overall summary
    print("\n\n" + "=" * 80)
    print("OVERALL PERFORMANCE")
    print("=" * 80)

    all_skills_f1 = [r["metrics"]["skills"]["f1"] for r in results]
    all_tech_f1 = [r["metrics"]["technologies"]["f1"] for r in results]
    all_req_f1 = [r["metrics"]["requirements"]["f1"] for r in results]

    print(f"\nSkills:   Avg F1 = {sum(all_skills_f1)/len(all_skills_f1):.2f} (range: {min(all_skills_f1)}-{max(all_skills_f1)})")
    print(f"Tech:     Avg F1 = {sum(all_tech_f1)/len(all_tech_f1):.2f} (range: {min(all_tech_f1)}-{max(all_tech_f1)})")
    print(f"Req:      Avg F1 = {sum(all_req_f1)/len(all_req_f1):.2f} (range: {min(all_req_f1)}-{max(all_req_f1)})")

    # Save results
    output_file = project_root / ".claude/prototypes/phase3_validation_results.json"
    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": "2026-07-30",
                "jobs_tested": len(results),
                "results": results,
                "domain_stats": {k: {kk: [round(v, 2) for v in vv] for kk, vv in v.items()} for k, v in domain_stats.items()},
            },
            f,
            indent=2,
        )

    print(f"\n\nResults saved to {output_file}")


if __name__ == "__main__":
    main()
