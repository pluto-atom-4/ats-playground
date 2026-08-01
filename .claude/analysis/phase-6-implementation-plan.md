# Phase 6: HTML Parsing Improvement - Implementation Plan

**Issue:** #193
**Objective:** Fix HTML parsing to eliminate corrupted/fragmented text before entity extraction
**Status:** Fresh start from origin/main (commit 8eb3ca9)
**Base:** Incorporates Issues #190, #191, #192 (merged)

---

## Problem Statement

Current HTML parsing produces corrupted/fragmented text:
- `may differCulture StatementDon't` (concatenation artifact)
- `computer science and years` (incomplete phrase)
- Similar issues across Blue Origin, Boeing, UW job postings

**Root Cause:** MarkItDown/BeautifulSoup concatenating HTML elements without proper whitespace/punctuation normalization.

**Impact:**
- Low signal-to-noise ratio (~45%)
- Entity extraction extracts noise alongside legitimate skills/requirements
- Reduces quality score below target

---

## Solution: Phased HTML Parsing Improvement

### Phase 1: Analysis & Baseline (1-2 hours)

**Goal:** Understand fragmentation patterns; establish metrics

**Tasks:**
1. Extract sample jobs with known fragmentation issues
2. Document parsing failures (before/after MarkItDown/BeautifulSoup)
3. Identify common HTML patterns causing artifacts:
   - Missing spaces between inline elements (`<span>word1</span><span>word2</span>`)
   - Nested div/p tags without newline separation
   - Pseudo-HTML from JavaScript rendering
4. Establish baseline metrics:
   - % of jobs with fragments (target: 0%)
   - Fragment count distribution
   - False positive rate before/after fix

**Deliverables:**
- `.claude/analysis/html_parsing_baseline.md` - patterns, metrics, sample jobs

### Phase 2: Enhance HTMLCleaner (2-3 hours)

**Goal:** Fix MarkItDown/BeautifulSoup fragmentation

**Tasks:**
1. **Improve BeautifulSoup path:**
   - Add space insertion before text extraction from block elements
   - Detect and fix concatenated words
   - Add normalization for HTML artifacts

2. **Enhance MarkItDown integration:**
   - Test MarkItDown markdown output for artifacts
   - Post-process if needed

3. **Add new cleanup patterns:**
   - Detect word boundaries (lowercase → uppercase mid-text)
   - Split on delimiters (`,`, `;`, `-`, `/`)
   - Normalize spacing around punctuation

4. **Add validation:**
   - "Senior Developer" doesn't become "SeniorDeveloper"
   - Multi-word phrases preserved correctly
   - Contractions preserved ("don't" not "don don t")

**Code Changes:**
- Modify `src/parsers/html_cleaner.py`:
  - Add `_fix_concatenated_words()` method
  - Add `_normalize_html_spacing()` method
  - Update `_clean_with_beautifulsoup()` with spacing fixes
  - Add unit tests for each fix

**Deliverables:**
- Updated `HTMLCleaner` with fragmentation fixes
- Tests for 10+ common fragmentation patterns

### Phase 3: Preprocessing Integration & Testing (1-2 hours)

**Goal:** Verify fixes work end-to-end; measure improvement

**Tasks:**
1. Test preprocessor with sample jobs
2. Compare outputs (old HTMLCleaner vs new implementation)
3. Check for remaining fragments
4. Run full test suite
5. Measure baseline improvement:
   - Fragment count: baseline → new
   - Signal-to-noise ratio: 45% → 55%+
   - No regressions in clean text

**Verification Commands:**
```bash
uv run python -m src.cli preprocess --show-estimates --limit 5
uv run pytest tests/ -v --cov=src/parsers
```

**Deliverables:**
- Comprehensive test suite for HTMLCleaner
- Benchmark report (before/after)

### Phase 4: Documentation & Finalization (0.5 hours)

**Goal:** Document solution; prepare for merge

**Tasks:**
1. Update `DESIGN.md` → parsing strategy
2. Update `.claude/rules/preprocess.md` → new HTML cleaning patterns
3. Document limitations (e.g., JavaScript-rendered content)
4. Add examples (fixed vs unfixed cases)

**Deliverables:**
- Documentation updates
- Ready for PR review

---

## Success Criteria

✅ **No multi-word fragments** in clean_text output
✅ **HTML structure preserved correctly** (headings, lists, etc.)
✅ **Text quality improved** (45% → 55%+ signal-to-noise ratio)
✅ **All tests passing** (pytest, coverage, lint)
✅ **Zero regressions** in existing preprocessing
✅ **Documentation updated** with new patterns

---

## Risk Mitigation (Lessons from #190/#191/#192)

| Risk | Mitigation |
|------|-----------|
| Over-aggressive cleanup removes valid content | Phase 1 analysis identifies exact patterns; unit tests per pattern |
| Word boundary detection issues (e.g., "API" vs "api") | Case sensitivity tests; preserve camelCase |
| Hidden regressions in full pipeline | Full preprocess test suite; before/after comparison per job |
| Over-specification → hard to maintain | Keep fixes minimal; document why each pattern needed |

---

## Dependencies

- ✅ Issue #190 (soft skills) – Merged
- ✅ Issue #191 (compounds) – Merged
- ✅ Issue #192 (keywords) – Merged

**No blocking dependencies.**

---

## Effort Estimate

| Phase | Effort | Cumulative |
|-------|--------|-----------|
| Phase 1 (Analysis) | 2h | 2h |
| Phase 2 (Implementation) | 3h | 5h |
| Phase 3 (Testing) | 2h | 7h |
| Phase 4 (Documentation) | 1h | 8h |
| **Total** | **8h** | **~1 dev day** |

---

## Workflow

1. **Analysis Phase:** Identify fragmentation patterns in current output
2. **Implementation Phase:** Fix HTMLCleaner with new methods
3. **Integration Phase:** Test preprocessor end-to-end
4. **Documentation Phase:** Update guides and finalize

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Multi-word fragments | Many | 0 |
| Signal-to-noise ratio | 45% | 55%+ |
| Test coverage (parsers) | ~60% | 90%+ |
| All tests passing | ✅ | ✅ |

---

## Next Phase

**Issue #194 (Phase 7):** Filter company names from skills/requirements

---

**Created:** 2026-08-01
**Status:** Ready for implementation
