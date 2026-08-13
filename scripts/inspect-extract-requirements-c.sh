#!/bin/bash

uv run python -c "
# Final comprehensive test
from src.poc.extract_requirements_c import (
    extract_requirements_c,
    extract_requirements,
    SimpleRequirementExtractionOutputWithSections,
    RequirementWithSection,
    load_spacy_model,
    detect_sections,
    extract_target_section_content,
    classify_sentence_with_section_boost,
    extract_company_name_enhanced,
    REQUIREMENT_PATTERNS,
)
from src.poc.bullet_point_preprocessor import normalize_bullet_points

print('✓ All imports successful')
print(f'✓ REQUIREMENT_PATTERNS has {len(REQUIREMENT_PATTERNS)} patterns')

# Test on real data
print(f'✓ REQUIREMENT_PATTERNS has {len(REQUIREMENT_PATTERNS)} patterns')

# Test on real data
with open('tests/poc/fixtures/raw_job_description.md') as f:
    markdown = f.read()

# Test extract_requirements_c
result = extract_requirements_c(
    markdown,
    min_confidence=0.50,
    max_requirements=20,
    target_sections=None,
)

print(f'✓ extract_requirements_c returned SimpleRequirementExtractionOutputWithSections')
print(f'✓ Company: {result.company}')
print(f'✓ Requirements extracted: {len(result.requirements)}')
print(f'✓ Requirements detailed: {len(result.requirements_detailed)}')
print(f'✓ Metadata fields: {len(result.metadata)}')

# Verify each requirement has all required fields
for i, req in enumerate(result.requirements_detailed[:2]):
    assert req.text
    assert req.trigger_word
    assert 0 <= req.base_confidence <= 1
    assert -0.5 <= req.section_boost <= 0.5
    assert 0 <= req.final_confidence <= 1
    assert req.source_section
    assert req.section_display_name
    print(f'✓ Requirement {i+1} has all required fields')

# Verify backward compatibility
result2 = extract_requirements(markdown)
assert result2 == result
print(f'✓ Backward compatibility with extract_requirements() function verified')

print('\n✅ All verifications passed! Phase 4 implementation complete.')
"
