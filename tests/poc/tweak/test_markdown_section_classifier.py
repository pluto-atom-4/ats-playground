"""Unit tests for markdown_section_classifier.py (Phase D of Issue #293).

Tests cover all components of the markdown section classification system:
- SectionType enum (all 8 values)
- SectionClassification dataclass
- SectionClassifier initialization and classification logic
- Edge cases (empty sections, no title, mixed content, etc.)
- Confidence scoring and is_skip flag
- classify_section() convenience function
- calculate_position() function and keyword_matches tracking
- Position accuracy and keyword match aggregation

Run with:
    uv run pytest tests/poc/tweak/test_markdown_section_classifier.py -v
    uv run pytest tests/poc/tweak/test_markdown_section_classifier.py -v --cov=src/poc/tweak
"""

import pytest

from src.poc.tweak.markdown_section_classifier import (
    KeywordMatch,
    SectionClassification,
    SectionClassifier,
    SectionType,
    TypeClassification,
    calculate_confidence,
    calculate_position,
    classify_section,
    fallback_confidence,
)
from src.poc.tweak.multi_line_paragraph import MarkdownSection
from src.poc.tweak.patterns import (
    DESCRIPTION_KEYWORDS,
    KNOWLEDGE_KEYWORDS,
    QUALIFICATIONS_KEYWORDS,
    RESPONSIBILITIES_KEYWORDS,
    SKILLS_KEYWORDS,
    SKIP_SECTIONS,
)

# ============================================================================
# Phase 1: SectionType Enum Tests
# ============================================================================


class TestSectionTypeEnum:
    """Test SectionType enum values and properties."""

    def test_section_type_has_all_eight_values(self) -> None:
        """Verify SectionType enum has exactly 8 values."""
        assert len(SectionType) == 8

    def test_section_type_skills_value(self) -> None:
        """Verify SKILLS enum value."""
        assert SectionType.SKILLS.value == "skills"

    def test_section_type_qualifications_value(self) -> None:
        """Verify QUALIFICATIONS enum value."""
        assert SectionType.QUALIFICATIONS.value == "qualifications"

    def test_section_type_responsibilities_value(self) -> None:
        """Verify RESPONSIBILITIES enum value."""
        assert SectionType.RESPONSIBILITIES.value == "responsibilities"

    def test_section_type_knowledge_value(self) -> None:
        """Verify KNOWLEDGE enum value."""
        assert SectionType.KNOWLEDGE.value == "knowledge"

    def test_section_type_description_value(self) -> None:
        """Verify DESCRIPTION enum value."""
        assert SectionType.DESCRIPTION.value == "description"

    def test_section_type_skip_value(self) -> None:
        """Verify SKIP enum value."""
        assert SectionType.SKIP.value == "skip"

    def test_section_type_other_value(self) -> None:
        """Verify OTHER enum value."""
        assert SectionType.OTHER.value == "other"

    def test_section_type_unlabeled_value(self) -> None:
        """Verify UNLABELED enum value."""
        assert SectionType.UNLABELED.value == "unlabeled"


# ============================================================================
# Phase 2: SectionClassification Dataclass Tests
# ============================================================================


class TestSectionClassification:
    """Test SectionClassification dataclass."""

    def test_classification_with_all_fields(self) -> None:
        """Test creating classification with all fields."""
        type_clf = TypeClassification(
            section_type=SectionType.SKILLS,
            confidence=0.9,
            matched_keywords=("skill", "technical"),
        )
        clf = SectionClassification.from_type_classifications([type_clf])
        assert clf.all_types[0].section_type == SectionType.SKILLS
