#!/usr/bin/env python3
"""Test NER on first job (Principal ASIC Design Engineer)."""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.nlp.ner import JobNERExtractor


def load_job_data(job_idx: int = 0) -> dict:
    """Load job from extracted_jobs JSON."""
    jobs_file = project_root / "data/extracted_jobs/blue origin_jobs.json"
    with open(jobs_file) as f:
        jobs = json.load(f)
    return jobs[job_idx]


def main():
    print("=== Testing First Job ===\n")

    job = load_job_data(job_idx=0)

    print(f"Job: {job['title']}")
    print(f"Company: {job['company']}")
    print(f"Description length: {len(job['description'])} chars\n")

    # Extract
    extractor = JobNERExtractor()
    extracted = extractor.extract_all(job["description"])

    # Display
    print("SKILLS:")
    for skill in extracted["skills"]:
        print(f"  - {skill}")

    print(f"\nTECHNOLOGIES:")
    for tech in extracted["technologies"]:
        print(f"  - {tech}")

    print(f"\nREQUIREMENTS:")
    for req in extracted["requirements"]:
        print(f"  - {req}")

    # Save results
    output_file = project_root / ".claude/prototypes/ner_results_job0.json"
    with open(output_file, "w") as f:
        json.dump(
            {
                "job_title": job["title"],
                "extracted": extracted,
            },
            f,
            indent=2,
        )
    print(f"\n\nResults saved to {output_file}")


if __name__ == "__main__":
    main()
