# NER Prototype: Job Description Entity Extraction

**Status:** Proof-of-concept working; ready for iterative refinement.

---

## Current Performance

| Entity | Precision | Recall | F1 | Notes |
|--------|-----------|--------|-----|-------|
| **Skills** | 1.0 | 1.0 | **1.0** ✓ | Context-inference working perfectly |
| **Technologies** | 0.88 | 1.0 | **0.93** ✓ | One false positive (C detected) |
| **Requirements** | 0.36 | 0.44 | **0.40** | Needs normalization + text cleanup |

---

## What's Working

### Skills Extraction (Perfect)
- **Approach:** Context-inference mapping (regex patterns → skill phrases)
- **Example:** Detects "hardware-in-the-loop testing" from phrase "hardware-in-the-loop (HIL) testing"
- **Coverage:** All 23 expected skills extracted
- **Why:** Role-specific skills are always mentioned in context, just not as isolated phrases

### Technologies Extraction (Strong)
- **Approach:** Known tool/framework patterns (MATLAB, Git, JIRA, etc.)
- **Example:** Catches "MATLAB/Simulink" as two separate techs
- **Coverage:** 7/7 expected + 1 false positive (C language detected somewhere)
- **Why:** Tech stack is mentioned explicitly by name

---

## What Needs Work

### Requirements Extraction (Moderate)
- **Issue 1:** Expected has normalized text; we extract raw bullets
  - **We get:** "Demonstrated experience leading and managing lean teams on fast-paced projects"
  - **Expected:** "Demonstrated experience leading and managing lean teams"
  - **Fix:** Add post-processing to normalize/deduplicate close matches

- **Issue 2:** Missing domain-specific requirement phrases
  - **We miss:** "Experience in implementation and testing of Autonomy on aerospace vehicles"
  - **Why:** Exact phrase not in minimum qualifications; embedded in responsibilities
  - **Fix:** Extract from responsibilities section + context filtering

- **Issue 3:** Degree detection needs better prioritization
  - **Current:** Extracts "M.S." and "Ph.D." separately → "Advanced degree (M.S. or Ph.D.)"
  - **Expected:** Already normalized
  - **Fix:** Detect "M.S. or Ph.D." as a unit

---

## Next Steps (Priority Order)

### Phase 1: Normalize Requirements (10 min)
```python
# Post-process extracted requirements:
def normalize_requirement(req: str) -> str:
    # Remove parenthetical clauses unless "(Preferred)"
    # Deduplicate similar requirements (edit distance < 0.3)
    # Standardize phrasing ("has experience" → "Experience in")
    pass
```

### Phase 2: Extract Domain-Specific Requirements (15 min)
```python
# Look for requirement patterns in responsibilities section:
# "Experience in [X] ... [Y]" → requirement
# "Demonstrated [skill]" → requirement
# Filter by keywords: "experience", "demonstrated", "proven", "required"
```

### Phase 3: Fine-Tune Tech Detection (5 min)
- Add negative patterns to avoid false positives (e.g., `\bC\b` → exclude if followed by `++`)
- Add common variant mappings (e.g., "Python 3" → "Python")

### Phase 4: Test on Additional Jobs (prep for production)
- Test on 5-10 more job descriptions
- Measure coverage/accuracy across different companies
- Identify domain-specific patterns (aerospace, SaaS, etc.)

---

## Architecture

**File Structure:**
```
src/nlp/
├── __init__.py         (public API)
├── ner.py             (JobNERExtractor class)
├── patterns.py        (regex patterns, keyphrases)
└── normalizer.py      (TODO: post-processing)

.claude/prototypes/
├── ner_prototype.py   (test harness)
├── ner_results.json   (benchmark results)
└── NER_PROTOTYPE_SUMMARY.md (this file)
```

---

## Usage

### Extract from a Job Description
```python
from src.nlp import JobNERExtractor

extractor = JobNERExtractor()
job_text = "..."
result = extractor.extract_all(job_text)

print(result["skills"])         # ["Guidance and Control", ...]
print(result["technologies"])   # ["MATLAB", "Git", ...]
print(result["requirements"])   # ["10+ years of experience ...", ...]
```

### Run Benchmark
```bash
uv run .claude/prototypes/ner_prototype.py
```

---

## Key Insights

1. **Skills are contextual:** Can't rely on isolated skill names; must infer from surrounding text (requirements, responsibilities).
   
2. **Tech stack is explicit:** Tools/frameworks are named directly; pattern matching alone is sufficient.
   
3. **Requirements are prose:** No standard format; must parse natural language (bullets, sections, narrative).

4. **Normalization matters:** Raw extraction ≠ expected output; post-processing needed to match human-curated format.

---

## Known Limitations

- **No multi-job context:** Extracts one job at a time; no cross-job patterns.
- **Language-specific:** Assumes English job descriptions; untested on other languages.
- **Single NER model:** Uses spaCy en_core_web_md; could fine-tune for better accuracy.
- **No confidence scores:** All extracted entities treated as equal; no ranking/filtering.

---

## Deployment Checklist (Future)

- [ ] Phase 1: Normalization complete + tested
- [ ] Phase 2: Domain requirement extraction + tested
- [ ] Phase 3: Tech detection false positives eliminated
- [ ] Phase 4: Benchmarked on 10+ jobs across companies
- [ ] Phase 5: Integration with main CLI (`--extract-entities` flag)
- [ ] Phase 6: Confidence scoring + user feedback loop

---

**Last Updated:** 2026-07-29
**Author:** Claude Code (Caveman Mode)
**Next Session:** Implement Phase 1 (normalization)
