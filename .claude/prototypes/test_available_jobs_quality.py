#!/usr/bin/env python3
"""Quality analysis of extraction across available job sources."""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.nlp.ner import JobNERExtractor
from src.nlp.domains import detect_domain
from src.nlp.requirement_normalizer import RequirementNormalizer


def load_jobs(company: str) -> list:
    """Load jobs from company, filter out empty descriptions."""
    jobs_file = project_root / f"data/extracted_jobs/{company}_jobs.json"
    with open(jobs_file) as f:
        jobs = json.load(f)
    # Filter jobs with actual descriptions
    return [j for j in jobs if j.get("description", "").strip()]


def main():
    print("=" * 90)
    print("EXTRACTION QUALITY ANALYSIS - AVAILABLE JOBS")
    print("=" * 90)

    companies = ["carbonrobotics", "uw", "blue origin", "boeing"]
    all_jobs = []

    for company in companies:
        jobs = load_jobs(company)
        if not jobs:
            print(f"\n{company.upper()}: No jobs with descriptions")
            continue

        print(f"\n\n{company.upper()} ({len(jobs)} jobs with descriptions)")
        print("-" * 90)

        for job_idx, job in enumerate(jobs):
            title = job.get("title", "N/A")[:60]
            desc_len = len(job.get("description", ""))
            domain = detect_domain(job.get("description", "")).value

            extractor = JobNERExtractor(company_name=company)
            result = extractor.extract_all_with_confidence(job.get("description", ""))

            # Extract counts
            skills_count = len(result["skills"])
            techs_count = len(result["technologies"])
            reqs_count = len(result["requirements"])

            # Confidence metrics
            avg_skill_conf = result["metrics"]["avg_skills_confidence"]
            avg_tech_conf = result["metrics"]["avg_tech_confidence"]
            avg_req_conf = result["metrics"]["avg_req_confidence"]

            # Extraction density
            total_extracted = skills_count + techs_count + reqs_count
            density = total_extracted / (desc_len / 100) if desc_len > 0 else 0

            print(f"\nJob {job_idx}: {title}")
            print(f"  Description: {desc_len:,} chars | Domain: {domain}")
            print(f"  Extracted: {skills_count} skills, {techs_count} tech, {reqs_count} requirements (density: {density:.1f}/100 chars)")
            print(f"  Confidence: Skills={avg_skill_conf:.2f}, Tech={avg_tech_conf:.2f}, Req={avg_req_conf:.2f}")

            # Show best extractions by confidence
            if result["skills"]:
                best_skills = sorted(result["skills"], key=lambda x: x["confidence"], reverse=True)[:2]
                skills_str = ", ".join(f"{s['value'][:30]}({s['confidence']:.2f})" for s in best_skills)
                print(f"  Top skills: {skills_str}")

            if result["technologies"]:
                best_techs = sorted(result["technologies"], key=lambda x: x["confidence"], reverse=True)[:2]
                techs_str = ", ".join(f"{t['value'][:20]}({t['confidence']:.2f})" for t in best_techs)
                print(f"  Top tech: {techs_str}")

            all_jobs.append({
                "company": company,
                "title": title,
                "domain": domain,
                "desc_len": desc_len,
                "skills": skills_count,
                "tech": techs_count,
                "req": reqs_count,
                "skill_conf": avg_skill_conf,
                "tech_conf": avg_tech_conf,
                "req_conf": avg_req_conf,
                "density": density,
            })

    # Summary
    print("\n\n" + "=" * 90)
    print("OVERALL STATISTICS")
    print("=" * 90)

    print(f"\n{'Company':<20} {'Jobs':<6} {'Avg Desc (chars)':<18} {'Skills':<10} {'Tech':<10} {'Req':<10} {'Density':<10}")
    print("-" * 90)

    by_company = {}
    for job in all_jobs:
        company = job["company"]
        if company not in by_company:
            by_company[company] = []
        by_company[company].append(job)

    for company in companies:
        if company not in by_company:
            continue
        jobs = by_company[company]
        avg_desc = sum(j["desc_len"] for j in jobs) / len(jobs)
        avg_skills = sum(j["skills"] for j in jobs) / len(jobs)
        avg_tech = sum(j["tech"] for j in jobs) / len(jobs)
        avg_req = sum(j["req"] for j in jobs) / len(jobs)
        avg_density = sum(j["density"] for j in jobs) / len(jobs)

        print(f"{company:<20} {len(jobs):<6} {avg_desc:<18.0f} {avg_skills:<10.1f} {avg_tech:<10.1f} {avg_req:<10.1f} {avg_density:<10.2f}")

    # Extraction capability by domain
    print("\n\nExtraction Capability by Domain:")
    print("-" * 90)

    by_domain = {}
    for job in all_jobs:
        domain = job["domain"]
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(job)

    print(f"{'Domain':<15} {'Jobs':<6} {'Avg Skills':<12} {'Avg Tech':<12} {'Avg Req':<12} {'Avg Skill Conf':<16}")
    for domain in sorted(by_domain.keys()):
        jobs = by_domain[domain]
        avg_skills = sum(j["skills"] for j in jobs) / len(jobs)
        avg_tech = sum(j["tech"] for j in jobs) / len(jobs)
        avg_req = sum(j["req"] for j in jobs) / len(jobs)
        avg_conf = sum(j["skill_conf"] for j in jobs) / len(jobs)
        print(f"{domain:<15} {len(jobs):<6} {avg_skills:<12.1f} {avg_tech:<12.1f} {avg_req:<12.1f} {avg_conf:<16.2f}")

    # Data quality assessment
    print("\n\nData Quality Assessment:")
    print("-" * 90)

    total_jobs = len(all_jobs)
    high_extraction = sum(1 for j in all_jobs if j["skills"] >= 15)
    low_extraction = sum(1 for j in all_jobs if j["skills"] < 5)
    empty_reqs = sum(1 for j in all_jobs if j["req"] == 0)

    print(f"Jobs with high extraction (15+ skills): {high_extraction}/{total_jobs} ({100*high_extraction/total_jobs:.0f}%)")
    print(f"Jobs with low extraction (<5 skills): {low_extraction}/{total_jobs} ({100*low_extraction/total_jobs:.0f}%)")
    print(f"Jobs with no requirements extracted: {empty_reqs}/{total_jobs} ({100*empty_reqs/total_jobs:.0f}%)")

    # Save results
    output_file = project_root / ".claude/prototypes/quality_analysis_results.json"
    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": "2026-07-30",
                "total_jobs": total_jobs,
                "jobs": all_jobs,
                "summary": {
                    "high_extraction_jobs": high_extraction,
                    "low_extraction_jobs": low_extraction,
                    "no_requirements_jobs": empty_reqs,
                }
            },
            f,
            indent=2,
        )

    print(f"\n\nResults saved to {output_file}")


if __name__ == "__main__":
    main()
