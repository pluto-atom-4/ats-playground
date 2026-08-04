#!/usr/bin/env python3
"""Test extraction on all available companies."""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.nlp.domains import detect_domain
from src.nlp.ner import JobNERExtractor


def load_jobs(company: str) -> Any:
    """Load all jobs from company."""
    jobs_file = project_root / f"data/extracted_jobs/{company}_jobs.json"
    with open(jobs_file) as f:
        return json.load(f)


def calculate_metrics(extracted: set, expected: set) -> Any:
    """Calculate precision, recall, F1."""
    correct = extracted & expected
    precision = len(correct) / len(extracted) if extracted else 0
    recall = len(correct) / len(expected) if expected else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    return {
        "f1": round(f1, 2),
        "precision": round(precision, 2),
        "recall": round(recall, 2),
        "correct": len(correct),
        "extracted": len(extracted),
        "expected": len(expected),
    }


def main():
    print("=" * 90)
    print("MULTI-COMPANY EXTRACTION TEST")
    print("=" * 90)

    companies = ["carbonrobotics", "uw", "blue origin", "boeing"]
    results_by_company = {}
    all_results = []

    for company in companies:
        jobs = load_jobs(company)
        print(f"\n\n{company.upper()} ({len(jobs)} jobs)")
        print("-" * 90)

        company_results = []

        for job_idx, job in enumerate(jobs):
            title = job.get("title", "N/A")[:60]
            description = job.get("description", "")

            # Extract
            extractor = JobNERExtractor(company_name=company)
            result = extractor.extract_all_with_confidence(description)

            # Detect domain
            domain = detect_domain(description).value

            # Convert to sets for metrics
            extracted_skills = set(item["value"] for item in result["skills"])
            extracted_techs = set(item["value"] for item in result["technologies"])
            extracted_reqs = set(item["value"] for item in result["requirements"])

            # For jobs without expected data, just report extraction counts
            print(f"\nJob {job_idx}: {title}")
            print(f"  Domain: {domain}")
            print(f"  Skills: {len(extracted_skills)} extracted")
            print(f"  Tech: {len(extracted_techs)} extracted")
            print(f"  Req: {len(extracted_reqs)} extracted")
            print(
                f"  Avg confidence: Skills={result['metrics']['avg_skills_confidence']:.2f}, Tech={result['metrics']['avg_tech_confidence']:.2f}, Req={result['metrics']['avg_req_confidence']:.2f}"
            )

            # Show top extractions
            if extracted_skills:
                print(f"  Top skills: {', '.join(sorted(extracted_skills)[:3])}")
            if extracted_techs:
                print(f"  Top tech: {', '.join(sorted(extracted_techs)[:3])}")

            company_results.append(
                {
                    "title": title,
                    "domain": domain,
                    "skills_count": len(extracted_skills),
                    "tech_count": len(extracted_techs),
                    "req_count": len(extracted_reqs),
                    "avg_skill_conf": result["metrics"]["avg_skills_confidence"],
                    "avg_tech_conf": result["metrics"]["avg_tech_confidence"],
                    "avg_req_conf": result["metrics"]["avg_req_confidence"],
                }
            )

        results_by_company[company] = company_results
        all_results.extend(company_results)

    # Summary statistics
    print("\n\n" + "=" * 90)
    print("SUMMARY STATISTICS")
    print("=" * 90)

    print(f"\n{'Company':<20} {'Jobs':<6} {'Avg Skills':<12} {'Avg Tech':<12} {'Avg Req':<12}")
    print("-" * 90)

    for company in companies:
        results = results_by_company[company]
        if results:
            avg_skills = sum(r["skills_count"] for r in results) / len(results)
            avg_tech = sum(r["tech_count"] for r in results) / len(results)
            avg_req = sum(r["req_count"] for r in results) / len(results)
            print(f"{company:<20} {len(results):<6} {avg_skills:<12.1f} {avg_tech:<12.1f} {avg_req:<12.1f}")

    # Domain distribution
    print(f"\n\n{'Company':<20} {'Domains':<50}")
    print("-" * 90)

    for company in companies:
        results = results_by_company[company]
        domains = defaultdict(int)
        for r in results:
            domains[r["domain"]] += 1
        domain_str = ", ".join(f"{d}({c})" for d, c in sorted(domains.items()))
        print(f"{company:<20} {domain_str:<50}")

    # Confidence distribution
    print(f"\n\n{'Category':<15} {'Average Confidence':<20} {'Range':<40}")
    print("-" * 90)

    for category, key in [
        ("Skills", "avg_skill_conf"),
        ("Technologies", "avg_tech_conf"),
        ("Requirements", "avg_req_conf"),
    ]:
        values = [r[key] for r in all_results]
        avg = sum(values) / len(values) if values else 0
        min_val = min(values) if values else 0
        max_val = max(values) if values else 0
        print(f"{category:<15} {avg:<20.2f} {min_val:.2f} - {max_val:.2f}")

    # Save detailed results
    output_file = project_root / ".claude/prototypes/multi_company_results.json"
    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": "2026-07-30",
                "companies_tested": companies,
                "jobs_tested": sum(len(results_by_company[c]) for c in companies),
                "results_by_company": results_by_company,
            },
            f,
            indent=2,
        )

    print(f"\n\nDetailed results saved to {output_file}")


if __name__ == "__main__":
    main()
