#!/usr/bin/env python3
"""Debug Boeing requirement extraction."""

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


def load_expected(file_name: str) -> Any:
    expected_file = project_root / f"data/extracted_jobs/{file_name}"
    with open(expected_file) as f:
        return json.load(f)


job = load_job("boeing", 0)
expected = load_expected("expected_extractions-2.json")

print("=== Boeing Requirements Debug ===\n")

extractor = JobNERExtractor()
result = extractor.extract_all(job["description"])

extracted_req = set(result.get("requirements", []))
expected_req = set(expected["requirements"])

print(f"Expected: {len(expected_req)}")
print(f"Extracted: {len(extracted_req)}\n")

if extracted_req:
    print("=== EXTRACTED ===")
    for req in sorted(extracted_req)[:5]:
        print(f"  {req}")
else:
    print("=== EXTRACTED ===")
    print("  (none)")

print("\n=== EXPECTED (first 10) ===")
for req in sorted(expected_req)[:10]:
    print(f"  {req}")

# Check text for requirement patterns
text = job["description"].lower()

print("\n=== PATTERN CHECKS ===")
print(f"'bachelor' in text: {'bachelor' in text}")
print(f"'security clearance' in text: {'security clearance' in text}")
print(f"'coding challenge' in text: {'coding challenge' in text or 'codevue' in text}")
print(f"'u.s. person' in text: {'u.s. person' in text}")
print(f"'drug test' in text: {'drug test' in text}")
