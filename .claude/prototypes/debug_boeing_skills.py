#!/usr/bin/env python3
"""Debug Boeing skill extraction."""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.nlp.ner import JobNERExtractor
from src.nlp.domains import detect_domain, get_keyphrases


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


def main():
    job = load_job("boeing", 1)
    expected = load_expected("expected_extractions-2.json")

    print("=== Boeing Skills Debug ===\n")

    # Detect domain
    domain = detect_domain(job["description"])
    print(f"Detected domain: {domain.value}")

    # Get keyphrases for this domain
    keyphrases = get_keyphrases(domain)
    print(f"Keyphrases available: {len(keyphrases)}\n")

    # Extract
    extractor = JobNERExtractor()
    result = extractor.extract_all(job["description"])
    extracted_skills = set(result["skills"])
    expected_skills = set(expected["skills"])

    # Compare
    correct = extracted_skills & expected_skills
    missing = expected_skills - extracted_skills
    extra = extracted_skills - expected_skills

    print(f"Expected: {len(expected_skills)}")
    print(f"Extracted: {len(extracted_skills)}")
    print(f"Correct: {len(correct)}\n")

    print("=== CORRECT ===")
    for s in sorted(correct):
        print(f"  ✓ {s}")

    print("\n=== FIRST 10 MISSING ===")
    for s in sorted(missing)[:10]:
        print(f"  - {s}")

    print("\n=== KEYPHRASES IN TEXT (checking 10 expected) ===")
    text = job["description"].lower()
    for s in sorted(expected_skills)[:10]:
        in_kp = "✓ in keyphrases" if s.lower() in [kp.lower() for kp in keyphrases] else "✗ not in keyphrases"
        in_text = "✓ in text" if s.lower() in text else "✗ not in text"
        print(f"  {s}: {in_kp} | {in_text}")
