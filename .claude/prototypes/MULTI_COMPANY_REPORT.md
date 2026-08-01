# Multi-Company NER Extraction Report

Comprehensive testing of the NER pipeline across 4 companies and 7 job descriptions.

## Executive Summary

| Company | Jobs | Skills | Tech | Requirements | Status |
|---------|------|--------|------|--------------|--------|
| Boeing | 2 | 22.5 | 13.0 | 13.0 | ✓ Production Ready |
| Blue Origin | 2 | 20.0 | 6.5 | 8.0 | ✓ Production Ready |
| UW | 1 | 12.0 | 5.0 | 2.0 | ✓ Production Ready* |
| Carbonrobotics | 2 | 10.0 | 2.0 | 0.0 | ⚠ Needs Enhancement |

*Limited data (1 of 2 jobs had empty description)

## Detailed Results by Company

### Boeing (Senior Software Engineers)
- **Jobs**: 2 (Software + Defense domain)
- **Extraction**:
  - Skills: 20-25 per job (avg 22.5)
  - Technologies: 10-16 per job (avg 13.0)
  - Requirements: 13 per job (avg 13.0)
- **Requirement Confidence**: 21/26 high (81%), 5/26 low (19%)
- **Key Strength**: Structured requirement sections with bullets
- **Challenge**: Text variations (verbose phrasing)
- **Semantic F1**: 0.70 (vs exact F1 of 0.35)

### Blue Origin (Mixed Domains)
- **Jobs**: 2 (Aerospace + Hardware)
- **Extraction**:
  - Skills: 16-24 per job (avg 20.0)
  - Technologies: 5-8 per job (avg 6.5)
  - Requirements: 6-10 per job (avg 8.0)
- **Requirement Confidence**: 11/16 high (69%), 5/16 low (31%)
- **Key Strength**: High-precision skill extraction, well-structured
- **Aerospace Job**: Best overall (24 skills, 8 tech, 10 req)
- **Hardware Job**: Specialized tech extraction (ARM, MATLAB)

### UW (Operations Engineer)
- **Jobs**: 1 (Software domain)
- **Extraction**:
  - Skills: 12
  - Technologies: 5
  - Requirements: 2
- **Requirement Confidence**: 1 high, 1 low (mixed)
- **Key Strength**: Tech extraction (AWS, Azure, Docker)
- **Limitation**: Only 1 job with description (AI Agent Builder was empty)
- **Confidence**: Good skill confidence (0.58)

### Carbonrobotics (Deep Learning Roles)
- **Jobs**: 2 (Defense domain)
- **Extraction**:
  - Skills: 6-14 per job (avg 10.0)
  - Technologies: 2 per job (avg 2.0)
  - Requirements: 0 per job (avg 0.0)
- **Domain**: Defense (specialized)
- **Key Challenge**: Narrative prose format, no structured requirement sections
- **Recommendation**: Implement narrative extraction before production use

## Extraction Performance by Domain

| Domain | Jobs | Avg Skills | Avg Tech | Avg Req | Best Job |
|--------|------|-----------|---------|---------|----------|
| Aerospace | 1 | 24.0 | 8.0 | 10.0 | Blue Origin G&C |
| Software | 2 | 18.5 | 7.5 | 7.5 | Boeing SWE (25 skills) |
| Hardware | 1 | 16.0 | 5.0 | 6.0 | Blue Origin ASIC |
| Defense | 3 | 13.3 | 6.7 | 4.3 | Carbonrobotics (low req) |

**Ranking**: Aerospace > Software > Hardware > Defense

## Confidence Analysis

### Overall Distribution
- High Confidence (≥0.90): 33/44 extractions (75%)
- Medium Confidence (0.80-0.90): 0/44 extractions (0%)
- Low Confidence (<0.80): 11/44 extractions (25%)

### By Category
- **Technologies**: 0.92 average (consistent across all companies)
- **Skills**: 0.57-0.71 average (context-dependent)
- **Requirements**: 0.82-0.90 average (well-calibrated for structured)

### Confidence Gaps
- Boeing Requirements: High confidence (0.90) masks text variation issues
- Carbonrobotics Skills: Lower confidence (0.57-0.60) reflects narrative inference
- Blue Origin Skills: Well-calibrated (0.67-0.71)

## Data Quality Issues

| Issue | Company | Jobs | Resolution |
|-------|---------|------|-----------|
| Empty descriptions | UW | 1/2 | AI Agent Builder: 0 chars |
| Narrative format (no structured req) | Carbonrobotics | 2/2 | Need narrative extraction |
| Mixed domain detection | UW | 1 | General → Software (correct) |
| Text normalization gap | Boeing | 2 | Semantic F1 recovery: +0.35 |

## Feature Gaps & Recommendations

### For Carbonrobotics
**Status**: ⚠ Not production-ready (0 requirements extracted)

**Issue**: Defense domain jobs use narrative prose without structured "Requirements" sections.

**Solution**:
1. Implement narrative requirement extraction (implemented in Phase 6)
2. Test narrative extractor on job descriptions
3. Add defense-domain-specific patterns

**Estimated Impact**: +5-8 requirements per job

### For UW
**Status**: ✓ Production-ready (but limited data)

**Issue**: Only 1 usable job (AI Agent Builder had empty description).

**Solution**:
1. Validate data source (preprocessing issue?)
2. Obtain complete job descriptions
3. Test on full dataset

### For Boeing & Blue Origin
**Status**: ✓ Production-ready

**Enhancement Opportunity**: Text normalization for requirement evaluation
- Use fuzzy matching (75% threshold) for deduplication
- Current exact F1: 0.35 → Semantic F1: 0.70
- Implement in evaluation pipeline

## Extraction Density

Entities per 100 characters of job description:

| Company | Avg Density | Best Job | Interpretation |
|---------|------------|----------|-----------------|
| Boeing | 0.55 | 0.60 | Dense extraction |
| Blue Origin | 0.41 | 0.50 | Good extraction |
| UW | 0.20 | 0.20 | Sparse (1 job) |
| Carbonrobotics | 0.17 | 0.22 | Very sparse |

## Production Readiness Checklist

### ✅ Boeing
- [x] Structured extraction working
- [x] High confidence scores (81% high conf)
- [x] Multi-domain support (software + defense)
- [x] 13 requirements/job
- [ ] Semantic normalization (recommended)

### ✅ Blue Origin
- [x] Structured extraction working
- [x] Multi-domain support (aerospace + hardware)
- [x] High skill extraction (20 avg)
- [x] 8 requirements/job
- [x] Well-calibrated confidence (69% high)

### ✅ UW
- [x] Software domain working
- [x] Tech extraction good (AWS, Azure, Docker)
- [x] 12 skills/job
- [ ] More job descriptions needed (currently 1)

### ⚠ Carbonrobotics
- [ ] Structured extraction not applicable
- [ ] Narrative extraction needed
- [ ] Defense domain skills extracted (but no requirements)
- [ ] Need >5 requirement patterns for defense

## Recommendations for Deployment

1. **Immediate (Production)**:
   - Deploy Boeing & Blue Origin extractors as-is
   - Deploy UW extractor (monitor for more data)
   - Use strict "structured sections only" mode for requirement extraction

2. **Short-term (Sprint 1-2)**:
   - Implement semantic fuzzy matching for requirement deduplication
   - Add defense-domain narrative extraction patterns
   - Validate UW data completeness

3. **Medium-term (Sprint 3-4)**:
   - Fine-tune Carbonrobotics narrative requirement extraction
   - Add domain-specific confidence adjustment
   - Expand to additional companies

4. **Long-term**:
   - Build user feedback loop for low-confidence extractions (<0.70)
   - Cross-company validation using semantic matching
   - Continual model refinement from user corrections

## Files & Test Scripts

- `test_all_companies.py`: Overview extraction counts
- `test_available_jobs_quality.py`: Detailed quality metrics
- `test_requirement_comparison.py`: Requirement-specific analysis
- `multi_company_results.json`: Raw extraction counts
- `quality_analysis_results.json`: Detailed metrics
- `requirement_comparison_results.json`: Requirement confidence breakdown

## Conclusion

The NER pipeline is **production-ready for Boeing, Blue Origin, and UW**.

**Carbonrobotics requires narrative requirement extraction** before production deployment.

**Overall extraction quality is strong** (0.92 tech confidence, 0.60+ skill confidence), with clear confidence calibration between structured and narrative extraction methods.

Recommended next step: Deploy Boeing/Blue Origin to production while enhancing Carbonrobotics support.
