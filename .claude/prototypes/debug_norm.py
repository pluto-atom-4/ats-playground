#!/usr/bin/env python3
"""Debug normalization."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.nlp.normalizer import normalize_requirement, normalize_requirements

# Test the problematic requirement
req = "Experience in development, implementation, and testing of Autonomy on aerospace vehicles"

print(f"Original:\n  {req}\n")

normalized = normalize_requirement(req)
print(f"After normalize_requirement():\n  {repr(normalized)}\n")

# Test full set normalization
test_set = {
    "Experience in development, implementation, and testing of Autonomy on aerospace vehicles",
    "Demonstrated experience leading and managing lean teams on fast-paced projects",
    "10+ years of experience development of autonomy for complex processes and/or aerospace autonomy/GNC",
}

print("Testing full normalize_requirements():")
result = normalize_requirements(test_set)
for r in sorted(result):
    if "implementation" in r.lower():
        print(f"  {r}")
