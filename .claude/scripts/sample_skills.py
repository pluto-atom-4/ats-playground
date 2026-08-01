#!/usr/bin/env python
"""Show sample of extracted skills to verify quality."""

import json
from pathlib import Path


def main():
    """Display sample skills from preprocessed jobs."""
    jobs_file = Path("data/extracted_jobs/preprocessed_jobs.json")
    if not jobs_file.exists():
        print(f"❌ File not found: {jobs_file}")
        return

    with open(jobs_file) as f:
        jobs = json.load(f)

    print("=" * 100)
    print("SAMPLE SKILLS FROM PREPROCESSED JOBS")
    print("=" * 100)
    print()

    for job_idx, job in enumerate(jobs, 1):
        title = job.get("title", "Unknown")[:70]
        skills = job.get("skills", [])

        print(f"\n📌 Job {job_idx}: {title}")
        print(f"   Total skills: {len(skills)}")
        print("   Sample skills:")

        # Show first 10 skills
        for skill in sorted(skills)[:10]:
            print(f"     • {skill}")

        if len(skills) > 10:
            print(f"     ... and {len(skills) - 10} more")


if __name__ == "__main__":
    main()
