#!/usr/bin/env python
"""Verify that skills extracted don't contain items from skip sections."""

import json
from pathlib import Path


def get_skip_keywords():
    """Get all skip section keywords."""
    return {
        # Compensation & Benefits
        "benefit", "compensation", "salary", "pay range", "total reward",
        "401", "retirement", "insurance", "health", "dental", "vision",
        # Company Info
        "about", "company", "culture", "commitment",
        # Legal & Compliance
        "equal opportunity", "affirmative action", "disability",
        "background check", "export control", "security clearance", "visa",
        "right to work", "e-verify", "conflict of interest", "drug free",
        "union", "bargaining", "safety sensitive", "contingent", "award",
        "boeing participates",
        # Application & Work Details
        "apply", "posting date", "posted", "application close",
        "codevue", "technical assessment", "relocation",
        "shift", "location", "work location", "travel", "working condition",
        "fte", "temporary", "education",
    }


def check_skill_for_skip_keywords(skill, skip_keywords):
    """Check if skill contains any skip keywords."""
    skill_lower = skill.lower()
    found_keywords = []

    for skip_kw in skip_keywords:
        if skip_kw in skill_lower:
            found_keywords.append(skip_kw)

    return found_keywords


def main():
    """Verify no skip section content in skills."""

    print("=" * 80)
    print("VERIFICATION: Skills Extraction from Skip Sections")
    print("=" * 80)
    print()

    jobs_file = Path("data/extracted_jobs/preprocessed_jobs.json")
    if not jobs_file.exists():
        print("❌ File not found:", jobs_file)
        return

    with open(jobs_file) as f:
        jobs = json.load(f)

    skip_keywords = get_skip_keywords()
    issues_found = []

    print(f"Checking {len(jobs)} jobs for skip section keywords in skills...\n")

    for job_idx, job in enumerate(jobs, 1):
        title = job.get("title", "Unknown")[:50]
        skills = job.get("skills", [])

        job_issues = []
        for skill in skills:
            found_kws = check_skill_for_skip_keywords(skill, skip_keywords)
            if found_kws:
                job_issues.append({
                    "skill": skill,
                    "keywords": found_kws
                })

        if job_issues:
            issues_found.append({
                "job_idx": job_idx,
                "title": title,
                "issues": job_issues
            })

    # Report findings
    if issues_found:
        print(f"⚠️  FOUND {len(issues_found)} JOBS WITH SKIP SECTION CONTENT IN SKILLS:\n")
        for job_info in issues_found:
            print(f"Job {job_info['job_idx']}: {job_info['title']}")
            for issue in job_info["issues"]:
                print(f"  ❌ '{issue['skill']}'")
                print(f"     Matches: {', '.join(issue['keywords'])}")
            print()
    else:
        print("✅ VERIFICATION PASSED")
        print()
        print(f"All {len(jobs)} jobs checked:")
        for i, job in enumerate(jobs, 1):
            skills = job.get("skills", [])
            print(f"  Job {i}: {len(skills)} skills - all clean")
        print()
        print("✓ No skills extracted from skip sections")
        print("✓ CONTINGENT UPON AWARD PROGRAM - correctly skipped")
        print("✓ BOEING PARTICIPATES IN E-VERIFY - correctly skipped")


if __name__ == "__main__":
    main()
