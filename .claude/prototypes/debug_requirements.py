#!/usr/bin/env python3
"""Debug requirements extraction."""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.nlp.ner import JobNERExtractor

# Load job
with open(project_root / "data/extracted_jobs/blue origin_jobs.json") as f:
    jobs = json.load(f)
    desc = jobs[1]["description"]  # Job 1

extractor = JobNERExtractor()

# Extract just requirements (no normalization)
import re
from src.nlp.patterns import extract_technologies

requirements = set()

# 1. Years of experience (from minimum qualifications section only)
min_qual_match = re.search(
    r"(?:##\s+)?(?:minimum|required)\s+(?:qualifications?|experience)[\s\n:]*(.+?)(?=\n##|Preferred|---|\Z)",
    desc,
    re.IGNORECASE | re.DOTALL,
)

print("=== YEARS OF EXPERIENCE EXTRACTION ===")
if min_qual_match:
    min_qual_section = min_qual_match.group(1)
    print(f"Section length: {len(min_qual_section)} chars")

    # Extract years from this section only
    years_pattern = r"(\d+)\+?\s+years\s+(?:of\s+)?experience(?:\s+(?:in|with|focused\s+on|involving|related\s+to)\s+([^\.\n]+))?"
    for match in re.finditer(years_pattern, min_qual_section, re.IGNORECASE):
        years = match.group(1)
        domain = match.group(2)
        print(f"Match: years={years}, domain={domain}")

        if domain:
            domain = domain.strip()
            # Remove trailing punctuation
            domain = re.sub(r"[\.,;]*$", "", domain)
            print(f"  Cleaned domain: {domain}")
            # Normalize specific domains
            if "autonomy" in domain.lower() and "aerospace" in domain.lower():
                domain = "autonomy or aerospace autonomy/GNC"
                print(f"  Normalized to: {domain}")
            elif "autonomy" in domain.lower():
                domain = "autonomy"
            requirements.add(f"{years}+ years of experience {domain}")

print(f"\nExtracted requirements (so far): {requirements}")

# Now extract all via extractor
full_reqs = extractor.extract_requirements(desc)
print(f"\n=== FULL EXTRACTION (with normalization) ===")
for req in sorted(full_reqs):
    print(f"  - {req}")

# Check expected
with open(project_root / "data/extracted_jobs/expected_extractions.json") as f:
    expected = json.load(f)

print(f"\n=== EXPECTED ===")
for req in expected["requirements"]:
    print(f"  - {req}")
