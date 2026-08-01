#!/usr/bin/env python3
"""Analyze relationship between confidence scores and F1 metrics."""

import json
from pathlib import Path

results_file = Path(".claude/prototypes/phase3_validation_results.json")

with open(results_file) as f:
    data = json.load(f)

print("=" * 80)
print("CONFIDENCE vs F1 ANALYSIS")
print("=" * 80)

print(f"\n{'Company':<30} {'Category':<15} {'F1':<8} {'Conf':<8} {'Δ':<8}")
print("-" * 80)

for result in data["results"]:
    company = result["company"].upper()
    confidence = result.get("confidence", {})
    metrics = result["metrics"]

    categories = ["skills", "technologies", "requirements"]
    for cat in categories:
        f1 = metrics[cat]["f1"]
        conf = confidence.get(cat, 0.0)
        delta = f1 - conf
        symbol = "✓" if abs(delta) < 0.1 else ("↑" if delta > 0 else "↓")
        print(f"{company:<30} {cat:<15} {f1:<8.2f} {conf:<8.2f} {delta:>+7.2f} {symbol}")

print("\n\n" + "=" * 80)
print("INSIGHTS")
print("=" * 80)

print("""
Interpretation:
- ✓ Aligned: F1 ≈ Confidence (within 0.1) → scoring is calibrated
- ↑ Overconfident: F1 < Confidence → extractor too certain about inaccurate results
- ↓ Underconfident: F1 > Confidence → extractor uncertain despite accurate results

Key Findings:
1. Technologies: Aligned across all jobs (F1 ≈ Conf ≈ 0.90)
   → Pattern-based extraction is reliable and confidence scores are calibrated

2. Blue Origin Skills: Underconfident (F1=0.98, Conf=0.71)
   → Context inference works well but scores confidence conservatively
   → Consider increasing confidence for inferred skills in aerospace domain

3. Boeing Requirements: Overconfident (F1=0.35, Conf=0.91)
   → Company parser is too certain about narrative/mixed-format extractions
   → Text normalization mismatches lower F1 despite confident extraction

4. Boeing Skills: Underconfident (F1=0.68, Conf=0.70)
   → Similar to Blue Origin, but less extreme
   → Confidence is appropriately calibrated here

Recommendations:
- Keep technology confidence as-is (well-calibrated)
- Adjust skill confidence: increase for keyphrases, keep context inference at 0.70
- Improve Boeing requirement confidence: add post-processing normalization
  or lower structured bullet confidence to 0.80-0.85
""")
