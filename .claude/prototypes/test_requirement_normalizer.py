#!/usr/bin/env python3
"""Test requirement normalization and semantic matching."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from src.nlp.requirement_normalizer import RequirementNormalizer

# Test cases from Boeing extraction
test_cases = [
    (
        "2+ years of experience working with and/or interpreting engineering data or engineering drawings",
        "2+ years of experience interpreting engineering data or drawings",
        "verbose variant",
    ),
    (
        (
            "2+ years of experience performing quantitative or statistical analysis, "
            "data collection, preparation and interpretation"
        ),
        "2+ years of experience performing quantitative or statistical analysis",
        "truncated variant",
    ),
    (
        "9+ years of experience software development using either Java, C++, or Python",
        "9+ years of experience with software development using Java, C++, or Python",
        "missing 'with'",
    ),
    ("Bachelor's Degree", "Bachelor's Degree", "exact match"),
]

print("=" * 80)
print("REQUIREMENT NORMALIZER TEST")
print("=" * 80)

normalizer = RequirementNormalizer()

print("\n1. TEXT NORMALIZATION")
print("-" * 80)

for extracted, expected, desc in test_cases:
    norm_extracted = normalizer.normalize_requirement_for_comparison(extracted)
    norm_expected = normalizer.normalize_requirement_for_comparison(expected)
    match = norm_extracted.lower() == norm_expected.lower()

    print(f"\n{desc}:")
    print(f"  Extracted: {extracted}")
    print(f"  Expected:  {expected}")
    print(f"  Normalized match: {match}")
    if not match:
        print(f"    Norm extracted: {norm_extracted}")
        print(f"    Norm expected:  {norm_expected}")


print("\n\n2. SEMANTIC MATCHING")
print("-" * 80)

extracted_reqs = {
    ("2+ years of experience working with and/or interpreting engineering data or engineering drawings"),
    (
        "2+ years of experience performing quantitative or statistical analysis, "
        "data collection, preparation and interpretation"
    ),
    ("9+ years of experience software development using either Java, C++, or Python"),
    "Bachelor's Degree",
    "Deep experience with ARINC 429, ARINC 717, and ARINC 767 formats (Preferred)",
    "Hands-on experience with Apache Parquet, Apache ORC, HDF5, and Delta Lake (Preferred)",
}

expected_reqs = {
    "2+ years of experience interpreting engineering data or drawings",
    "2+ years of experience performing quantitative or statistical analysis",
    "9+ years of experience with software development using Java, C++, or Python",
    "Bachelor's Degree",
    "Hands-on experience with HDF5",
}

print(f"\nExtracted: {len(extracted_reqs)} requirements")
print(f"Expected: {len(expected_reqs)} requirements\n")

matched = 0
for expected in expected_reqs:
    best_match, score = normalizer.find_matching_requirement(expected, extracted_reqs, threshold=0.7)
    if best_match:
        matched += 1
        print(f"✓ [{score:.2f}] {expected}")
        print(f"         → {best_match}")
    else:
        print(f"✗ {expected}")

print(f"\nMatched: {matched}/{len(expected_reqs)}")


print("\n\n3. DEDUPLICATION")
print("-" * 80)

duplicates = {
    "2+ years of experience interpreting engineering data or drawings",
    "2+ years of experience working with and/or interpreting engineering data or engineering drawings",
    "experience with engineering data",
    "Bachelor's Degree",
    "Bachelor of Science Degree",
}

print(f"Input: {len(duplicates)} requirements")
deduplicated = normalizer.deduplicate_requirements(duplicates)
print(f"Output: {len(deduplicated)} unique requirements\n")

for req in sorted(deduplicated):
    print(f"  - {req}")
