# Phase 8: Requirement Trigger Patterns & Edge Cases

Specification for narrative requirement extraction from job descriptions. Defines trigger words, regex patterns, confidence scoring, and edge cases for semantic requirement identification.

**Status:** Design phase (patterns.md + test fixtures)
**Version:** 1.0
**Issue:** #248 (Requirement trigger pattern design)

---

## Overview

Narrative requirement extraction identifies must-have skills and qualifications within prose job descriptions. Trigger words signal requirement strength; regex patterns capture context; edge cases handle parentheticals, negations, and multi-line structures.

**Goals:**
- Identify requirements with 90%+ precision (false negatives OK; false positives costly)
- Handle English language variations ("must know", "required to have", "ability to")
- Support structured sections (Requirements, Qualifications, Responsibilities)
- Flag uncertain cases (e.g., "nice to have") with lower confidence

---

## Primary Trigger Words

**Tier 1 (Highest Confidence):** Clear requirement signals

1. **required** – "Python is required"
2. **must** – "Must have 5+ years experience"
3. **essential** – "Essential skills include..."
4. **mandatory** – "Mandatory background in AWS"
5. **ability to** – "Ability to write clean code"
6. **experience in** – "Experience in cloud platforms"
7. **experience with** – "Experience with Docker"
8. **proficiency** – "Proficiency in Java"
9. **knowledge of** – "Knowledge of SQL databases"
10. **understanding of** – "Understanding of Agile methodology"

**Tier 2 (Medium Confidence):** Softer requirement indicators

11. **should** – "Should know JavaScript" (directive, not absolute)
12. **prefer** – "We prefer candidates with..." (stated preference)
13. **seek** – "Seeking individuals with expertise in..."
14. **bachelor's degree** – "Bachelor's degree required/preferred"
15. **years of** – "3 years of software development"

**Tier 3 (Lower Confidence):** Nice-to-have, aspirational

16. **nice to have** – "Nice to have knowledge of..."
17. **ideal** – "Ideal candidate has..."
18. **bonus** – "Bonus points for ML experience"

---

## Regex Patterns

All patterns are case-insensitive. Capture groups extract the requirement span.

### Tier 1 Patterns

| Trigger | Regex | Example | Confidence |
|---------|-------|---------|------------|
| required | `(required\s+(?:to\s+)?[a-z\s]+(?:in\|with\|of)?\s+[\w\s-]+)` | "required to have Python" | 0.95 |
| must (have) | `(must\s+(?:have\s+)?[\w\s-]+(?:in\|with)?\s+[\w\s-]+)` | "must know SQL" | 0.93 |
| essential | `(essential\s+(?:to\s+)?(?:have\s+)?[\w\s-]+)` | "essential for success" | 0.90 |
| ability to | `(ability\s+to\s+[a-z\s-]+)` | "ability to manage teams" | 0.92 |
| experience in/with | `((?:experience\|background)\s+(?:with\|in)\s+[\w\s-]+)` | "experience with Python" | 0.88 |
| proficiency | `(proficiency\s+(?:in\|with)?\s+[\w\s-]+)` | "proficiency in Java" | 0.91 |
| knowledge of | `(knowledge\s+of\s+[\w\s-]+)` | "knowledge of cloud services" | 0.85 |
| understanding of | `(understanding\s+of\s+[\w\s-]+)` | "understanding of DevOps" | 0.83 |

### Tier 2 Patterns

| Trigger | Regex | Example | Confidence |
|---------|-------|---------|------------|
| should | `(should\s+(?:have\s+)?[\w\s-]+)` | "should have experience" | 0.70 |
| prefer | `((?:preferred\|prefer)\s+(?:candidate\s+)?[\w\s-]+)` | "preferred: 5+ years" | 0.65 |
| degree | `((?:bachelor's?\|master's?\|phd)\s+(?:degree\s+)?(?:in\|of)?\s+[\w\s-]+)` | "Bachelor's in CS" | 0.89 |
| years of | `([\d+]+\s+years?\s+of\s+[\w\s-]+)` | "5+ years of development" | 0.80 |

### Tier 3 Patterns

| Trigger | Regex | Example | Confidence |
|---------|-------|---------|------------|
| nice to have | `(nice\s+to\s+have\s+[\w\s-]+)` | "nice to have Docker" | 0.40 |
| ideal | `(ideal\s+(?:candidate\|[a-z]+)\s+[\w\s-]+)` | "ideal candidate knows..." | 0.55 |
| bonus | `(bonus\s+(?:points\|if\s+you)?\s+[\w\s-]+)` | "bonus: ML experience" | 0.45 |

---

## Edge Cases & Handling

### 1. Parenthetical Qualifications

**Pattern:** Requirement in parentheses (often secondary/optional)

```
Example: "Experience with Kubernetes (or equivalent container orchestration)"
Handling: Extract full phrase; lower confidence by 0.1 if parenthetical
Regex: (\([^)]*(?:require|must|experience|proficiency)[^)]*\))
Confidence adjustment: -0.10
```

### 2. Negative Forms ("No experience required")

**Pattern:** Negation reverses requirement

```
Example: "No experience with React required"
Handling: Skip requirement extraction; this is NOT a requirement
Regex: (?:no|not|don't|doesn't|didn't)\s+(?:prior\s+)?experience
Rule: If negation precedes trigger word, set confidence to 0.0
```

### 3. Multi-Line Requirements (Bullet Lists)

**Pattern:** Requirement spans multiple bullets, often indented

```
Example:
  - 5+ years of software development
  - Experience with Python, Java, or C++
  - Understanding of microservices architecture

Handling: Extract each bullet separately; link siblings if co-dependent
Approach: Split on newlines + bullets ("\n-", "\n*", "\n•"), apply regex to each
```

### 4. Compound Requirements (Comma-Separated)

**Pattern:** Multiple skills in one requirement

```
Example: "Knowledge of Python, Java, C++, and Go"
Handling: Extract as single requirement; tokenizer splits in downstream processing
Regex: Capture full phrase; split in entity normalization phase
Expected: One requirement span covering all technologies
```

### 5. Conditional Requirements ("If you...")

**Pattern:** Requirement contingent on prior condition

```
Example: "If you have experience with AWS, bonus points"
Handling: Lower confidence by 0.15; flag as "nice to have"
Confidence adjustment: -0.15
```

### 6. Abstract/Soft Skills Requirements

**Pattern:** Soft skill (teamwork, communication, leadership) instead of technical

```
Example: "Must be a strong communicator"
Handling: Extract with full confidence; categorize as "soft_skill" span type
Span type: "soft_skill" (not "technical")
```

### 7. Degree/Certification Requirements

**Pattern:** Educational requirement (Bachelor's, AWS Certified, etc.)

```
Example: "Bachelor's degree in Computer Science or equivalent"
Handling: Extract with 0.89 confidence; span type "education"
Span type: "education"
```

### 8. Years-of-Experience Requirements

**Pattern:** Explicit tenure requirement ("3+ years", "7 years minimum")

```
Example: "Minimum 5 years of cloud infrastructure experience"
Regex: ([\d+]+\s+years?\s+(?:of|in)\s+[\w\s-]+)
Handling: Extract digits + field; span type "experience_level"
Span type: "experience_level"
```

### 9. Preferred vs. Required Sections

**Pattern:** Same phrase appears in both sections, confidence differs

```
Context:
  Required: "Python programming"
  Preferred: "Python programming"
Handling: Extract twice with different confidence (0.95 vs 0.70)
Confidence rule: 0.95 if in "Required" section; 0.70 if in "Preferred"
```

### 10. Vendor/Brand-Specific Requirements

**Pattern:** "Experience with Company's proprietary tool XYZ"

```
Example: "Experience with Salesforce CRM"
Handling: Extract full phrase; flag as "vendor-specific"
Span type: "vendor_specific" (or "technology")
```

---

## JSON Schema (Pattern Definition)

```json
{
  "pattern": {
    "type": "object",
    "properties": {
      "id": {
        "type": "string",
        "description": "Unique pattern identifier (e.g., 'tier1_required')"
      },
      "trigger_word": {
        "type": "string",
        "description": "Primary trigger word (e.g., 'required', 'must')"
      },
      "regex": {
        "type": "string",
        "description": "Case-insensitive regex pattern with capture groups"
      },
      "base_confidence": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "description": "Confidence score (0.0-1.0) before adjustments"
      },
      "tier": {
        "type": "integer",
        "enum": [1, 2, 3],
        "description": "Confidence tier (1=high, 2=medium, 3=low)"
      },
      "span_type": {
        "type": "string",
        "enum": ["technical", "soft_skill", "education", "experience_level", "vendor_specific", "requirement"],
        "description": "Semantic category of requirement"
      },
      "edge_cases": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "case": {
              "type": "string",
              "description": "Edge case name (e.g., 'parenthetical', 'negation')"
            },
            "confidence_adjustment": {
              "type": "number",
              "description": "Adjustment to base_confidence for this case (e.g., -0.1)"
            },
            "example": {
              "type": "string",
              "description": "Example sentence illustrating the edge case"
            }
          },
          "required": ["case", "confidence_adjustment", "example"]
        }
      },
      "examples": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Example sentences matching this pattern"
      }
    },
    "required": ["id", "trigger_word", "regex", "base_confidence", "tier", "span_type"]
  }
}
```

---

## Confidence Adjustment Rules

**Base score** starts at pattern's `base_confidence`. Adjustments apply in order:

1. **Parenthetical context:** -0.10
2. **Negation:** Set to 0.0 (exclude entirely)
3. **Conditional ("if"):** -0.15
4. **"Nice to have" / "Preferred" section:** -0.25
5. **"Required" section:** +0.05
6. **Multiple occurrences in text:** +0.05 (per occurrence, max +0.15)

**Final confidence** = base_confidence + adjustments, clamped to [0.0, 1.0].

---

## Implementation Notes

- **Regex flags:** Always use case-insensitive flag (re.IGNORECASE)
- **Capture groups:** Use non-capturing groups `(?:...)` for lookaheads; numbered groups for spans
- **Multi-line:** Apply `re.MULTILINE | re.DOTALL` flags when processing full job text
- **Fallback:** If no trigger patterns match, skip requirement extraction (don't guess)
- **Tokenization:** Defer compound requirement splitting to downstream entity extraction phase

---

## Related

- **Issue #248:** Requirement trigger pattern design
- **Phase 8:** Narrative requirement extraction from job prose
- **Test fixtures:** `tests/preprocessing/fixtures/requirement_sentences.json`

---

**Last Updated:** 2026-08-10 (Task 8a.1)
**Status:** Design complete; awaiting 8a.2 (implementation)
