#!/usr/bin/env python3
"""Debug missing requirement."""

import json
import re
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.nlp.ner import JobNERExtractor

# Load job
with open(project_root / "data/extracted_jobs/blue origin_jobs.json") as f:
    jobs = json.load(f)
    desc = jobs[1]["description"]

# Get raw bullets
min_qual_match = re.search(
    r"(?:##\s+)?(?:minimum|required)\s+(?:qualifications?|experience)[\s\n:]*(.+?)(?=\n##|Preferred|---|\Z)",
    desc,
    re.IGNORECASE | re.DOTALL,
)

print("=== RAW BULLETS ===")
if min_qual_match:
    qual_text = min_qual_match.group(1)
    bullets = re.findall(r"[\*•\-]\s+(.+?)(?:\n|$)", qual_text)
    for i, b in enumerate(bullets, 1):
        if "Autonomy" in b or "implementation" in b.lower():
            print(f"{i}. {b}")

# Extract via extractor
extractor = JobNERExtractor()
reqs = extractor.extract_requirements(desc)

print("\n=== EXTRACTED ===")
for req in sorted(reqs):
    if "implementation" in req.lower() or "autonomy" in req.lower():
        print(f"  {req}")

print("\n=== EXPECTED ===")
with open(project_root / "data/extracted_jobs/expected_extractions.json") as f:
    exp = json.load(f)
for req in exp["requirements"]:
    if "implementation" in req.lower() or "autonomy" in req.lower():
        print(f"  {req}")
