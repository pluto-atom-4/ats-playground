"""Unit tests for markdown_section_classifier.py (Phase D of Issue #293).

Tests cover all components of the markdown section classification system:
- SectionType enum (all 8 values)
- SectionClassification dataclass
- SectionClassifier initialization and classification logic
- Edge cases (empty sections, no title, mixed content, etc.)
- Confidence scoring and is_skip flag
- classify_section() convenience function

Run with:
    uv run pytest tests/poc/tweak/test_markdown_section_classifier.py -v
    uv run pytest tests/poc/tweak/test_markdown_section_classifier.py -v --cov=src/poc/tweak
"""

import pytest

from src.poc.tweak.markdown_section_classifier import (
    DESCRIPTION_KEYWORDS,
    KNOWLEDGE_KEYWORDS,
    QUALIFICATIONS_KEYWORDS,
    RESPONSIBILITIES_KEYWORDS,
    SKILLS_KEYWORDS,
    SKIP_SECTIONS,
    SectionClassification,
    SectionClassifier,
    SectionType,
    classify_section,
)
from src.poc.tweak.multi_line_paragraph import MarkdownSection

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
        clf = SectionClassification(
            section_type=SectionType.SKILLS,
            matched_keywords=("skill", "technical"),
            confidence=0.9,
            is_skip=False,
        )
        assert clf.section_type == SectionType.SKILLS
        assert clf.matched_keywords == ("skill", "technical")
        assert clf.confidence == 0.9
        assert clf.is_skip is False

    def test_classification_default_matched_keywords(self) -> None:
        """Test classification with default matched_keywords."""
        clf = SectionClassification(section_type=SectionType.OTHER)
        assert clf.matched_keywords == ()

    def test_classification_default_confidence(self) -> None:
        """Test classification with default confidence."""
        clf = SectionClassification(section_type=SectionType.OTHER)
        assert clf.confidence == 0.0

    def test_classification_default_is_skip(self) -> None:
        """Test classification with default is_skip."""
        clf = SectionClassification(section_type=SectionType.OTHER)
        assert clf.is_skip is False

    def test_classification_is_frozen(self) -> None:
        """Verify SectionClassification is immutable (frozen)."""
        clf = SectionClassification(section_type=SectionType.SKILLS)
        with pytest.raises(AttributeError):
            clf.section_type = SectionType.OTHER  # type: ignore

    def test_classification_confidence_validation_min(self) -> None:
        """Test confidence must be >= 0.0."""
        with pytest.raises(ValueError, match="confidence must be in"):
            SectionClassification(section_type=SectionType.SKILLS, confidence=-0.1)

    def test_classification_confidence_validation_max(self) -> None:
        """Test confidence must be <= 1.0."""
        with pytest.raises(ValueError, match="confidence must be in"):
            SectionClassification(section_type=SectionType.SKILLS, confidence=1.1)

    def test_classification_confidence_at_boundaries(self) -> None:
        """Test confidence accepts 0.0 and 1.0."""
        clf_min = SectionClassification(section_type=SectionType.SKILLS, confidence=0.0)
        assert clf_min.confidence == 0.0

        clf_max = SectionClassification(section_type=SectionType.SKILLS, confidence=1.0)
        assert clf_max.confidence == 1.0


# ============================================================================
# Phase 3: SectionClassifier Initialization Tests
# ============================================================================


class TestSectionClassifierInitialization:
    """Test SectionClassifier initialization and configuration."""

    def test_classifier_default_initialization(self) -> None:
        """Test classifier initializes with default skip keywords."""
        classifier = SectionClassifier()
        assert classifier.skip_keywords == SKIP_SECTIONS

    def test_classifier_custom_skip_keywords(self) -> None:
        """Test classifier accepts custom skip keywords."""
        custom_keywords = frozenset({"benefits", "salary"})
        classifier = SectionClassifier(skip_keywords=custom_keywords)
        assert classifier.skip_keywords == custom_keywords

    def test_classifier_custom_keywords_override_defaults(self) -> None:
        """Verify custom keywords override defaults."""
        custom_keywords = frozenset({"custom"})
        classifier = SectionClassifier(skip_keywords=custom_keywords)
        assert "benefits" not in classifier.skip_keywords
        assert "custom" in classifier.skip_keywords


# ============================================================================
# Phase 4: SectionClassifier.classify() - Basic Type Classification
# ============================================================================


class TestSectionClassifierBasicTypes:
    """Test classification of each section type."""

    @pytest.fixture
    def classifier(self) -> SectionClassifier:
        """Provide a default classifier instance."""
        return SectionClassifier()

    def test_classify_skills_from_title(self, classifier: SectionClassifier) -> None:
        """Test SKILLS classification from title."""
        section = MarkdownSection(
            title="Technical Skills",
            content="Python, Java, SQL",
            level=2,
            start_line=0,
            end_line=0,
            word_count=3,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.SKILLS
        assert "skill" in result.matched_keywords
        assert "technical" in result.matched_keywords
        assert result.is_skip is False

    def test_classify_qualifications_from_title(self, classifier: SectionClassifier) -> None:
        """Test QUALIFICATIONS classification from title."""
        section = MarkdownSection(
            title="Requirements",
            content="5+ years experience",
            level=2,
            start_line=0,
            end_line=0,
            word_count=3,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.QUALIFICATIONS
        assert "requirement" in result.matched_keywords
        assert result.is_skip is False

    def test_classify_responsibilities_from_title(self, classifier: SectionClassifier) -> None:
        """Test RESPONSIBILITIES classification from title."""
        section = MarkdownSection(
            title="Responsibilities",
            content="Lead team meetings, write code",
            level=2,
            start_line=0,
            end_line=0,
            word_count=4,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.RESPONSIBILITIES
        assert "respons" in result.matched_keywords
        assert result.is_skip is False

    def test_classify_knowledge_from_title(self, classifier: SectionClassifier) -> None:
        """Test KNOWLEDGE classification from title."""
        section = MarkdownSection(
            title="Knowledge and Experience",
            content="Background details",
            level=2,
            start_line=0,
            end_line=0,
            word_count=2,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.KNOWLEDGE
        assert "knowledge" in result.matched_keywords
        assert result.is_skip is False

    def test_classify_description_from_title(self, classifier: SectionClassifier) -> None:
        """Test DESCRIPTION classification from title."""
        section = MarkdownSection(
            title="Job Description",
            content="This is a great role",
            level=2,
            start_line=0,
            end_line=0,
            word_count=4,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.DESCRIPTION
        assert "description" in result.matched_keywords
        assert result.is_skip is False

    def test_classify_skip_from_title(self, classifier: SectionClassifier) -> None:
        """Test SKIP classification from title."""
        section = MarkdownSection(
            title="Benefits",
            content="Competitive salary and benefits",
            level=2,
            start_line=0,
            end_line=0,
            word_count=4,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.SKIP
        assert result.is_skip is True
        assert "benefits" in result.matched_keywords

    def test_classify_other_no_keywords(self, classifier: SectionClassifier) -> None:
        """Test OTHER classification when no keywords match."""
        section = MarkdownSection(
            title="Random Section",
            content="Some random content here",
            level=2,
            start_line=0,
            end_line=0,
            word_count=3,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.OTHER
        assert result.matched_keywords == ()
        assert result.is_skip is False


# ============================================================================
# Phase 5: Edge Cases
# ============================================================================


class TestSectionClassifierEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def classifier(self) -> SectionClassifier:
        """Provide a default classifier instance."""
        return SectionClassifier()

    def test_empty_section_content(self, classifier: SectionClassifier) -> None:
        """Test classification of section with empty content."""
        section = MarkdownSection(
            title="Empty Section",
            content="",
            level=2,
            start_line=0,
            end_line=0,
            word_count=0,
            line_count=0,
            has_list=False,
        )
        result = classifier.classify(section)
        # Empty content but has title -> classify from title
        assert result.section_type == SectionType.OTHER

    def test_no_title_with_content(self, classifier: SectionClassifier) -> None:
        """Test section with no title (None) and content."""
        section = MarkdownSection(
            title=None,
            content="Requirements: 5+ years Python experience",
            level=-2,
            start_line=0,
            end_line=0,
            word_count=6,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        # No title (None) -> classify from content
        assert result.section_type == SectionType.QUALIFICATIONS
        assert "requirement" in result.matched_keywords

    def test_empty_section_no_title(self, classifier: SectionClassifier) -> None:
        """Test section with no title and empty content."""
        section = MarkdownSection(
            title=None,
            content="",
            level=-2,
            start_line=0,
            end_line=0,
            word_count=0,
            line_count=0,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.UNLABELED
        assert result.matched_keywords == ()

    def test_level_minus_two_uses_content(self, classifier: SectionClassifier) -> None:
        """Test that level=-2 (unlabeled sections) use content for classification."""
        section = MarkdownSection(
            title="Some Title",  # Has title but level=-2
            content="Technical requirements include Python and Java",
            level=-2,
            start_line=0,
            end_line=0,
            word_count=7,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        # level=-2 overrides title -> classify from content
        assert result.section_type == SectionType.SKILLS
        assert "technical" in result.matched_keywords

    def test_case_insensitivity_uppercase(self, classifier: SectionClassifier) -> None:
        """Test case insensitivity with uppercase title."""
        section = MarkdownSection(
            title="TECHNICAL SKILLS",
            content="Python, Java",
            level=2,
            start_line=0,
            end_line=0,
            word_count=2,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.SKILLS

    def test_case_insensitivity_mixed(self, classifier: SectionClassifier) -> None:
        """Test case insensitivity with mixed case."""
        section = MarkdownSection(
            title="TeCHnIcAL SkILLs",
            content="Python, Java",
            level=2,
            start_line=0,
            end_line=0,
            word_count=2,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.SKILLS

    def test_partial_keyword_match(self, classifier: SectionClassifier) -> None:
        """Test that keywords match as substrings (partial matching)."""
        section = MarkdownSection(
            title="Skilled Developer",  # Contains 'skill' as substring
            content="Details here",
            level=2,
            start_line=0,
            end_line=0,
            word_count=2,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.SKILLS

    def test_list_items_with_skills(self, classifier: SectionClassifier) -> None:
        """Test classification of section with list items."""
        section = MarkdownSection(
            title="Core Competencies",
            content="* Python\n* Java\n* SQL",
            level=2,
            start_line=0,
            end_line=2,
            word_count=3,
            line_count=3,
            has_list=True,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.SKILLS
        assert result.matched_keywords  # Has matched keywords

    def test_very_long_content(self, classifier: SectionClassifier) -> None:
        """Test classification with very long content (1000+ tokens)."""
        long_content = "Python experience " * 100  # ~200 words
        section = MarkdownSection(
            title="Technical Skills",
            content=long_content,
            level=2,
            start_line=0,
            end_line=100,
            word_count=200,
            line_count=100,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.SKILLS

    def test_mixed_keywords_precedence(self, classifier: SectionClassifier) -> None:
        """Test precedence when multiple keyword types are present."""
        # SKIP > SKILLS > QUALIFICATIONS (etc.)
        section = MarkdownSection(
            title="Technical Skills and Requirements",
            content="Both skills and requirements keywords",
            level=2,
            start_line=0,
            end_line=0,
            word_count=5,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        # SKILLS should be matched first (comes before QUALIFICATIONS in precedence)
        assert result.section_type == SectionType.SKILLS


# ============================================================================
# Phase 6: Confidence Scoring
# ============================================================================


class TestConfidenceScoring:
    """Test confidence scoring logic."""

    @pytest.fixture
    def classifier(self) -> SectionClassifier:
        """Provide a default classifier instance."""
        return SectionClassifier()

    def test_no_keywords_confidence_low(self, classifier: SectionClassifier) -> None:
        """Test confidence is low when no keywords match."""
        section = MarkdownSection(
            title="Random Section",
            content="No keywords here",
            level=2,
            start_line=0,
            end_line=0,
            word_count=3,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.confidence < 0.5  # LOW confidence

    def test_single_keyword_match_confidence(self, classifier: SectionClassifier) -> None:
        """Test confidence with single keyword match."""
        section = MarkdownSection(
            title="Skills",
            content="Details here",
            level=2,
            start_line=0,
            end_line=0,
            word_count=2,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.confidence > 0.5  # MEDIUM confidence

    def test_multiple_keywords_higher_confidence(self, classifier: SectionClassifier) -> None:
        """Test confidence increases with multiple keyword matches."""
        section = MarkdownSection(
            title="Technical Skills and Core Competencies",
            content="Details here",
            level=2,
            start_line=0,
            end_line=0,
            word_count=2,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        # Multiple matches: 'technical', 'skill', 'core', 'competency'
        assert result.confidence >= 0.8  # HIGH confidence

    def test_confidence_capped_at_one(self, classifier: SectionClassifier) -> None:
        """Test confidence is capped at 1.0."""
        section = MarkdownSection(
            title="Technical Skills Core Competency Ability Expertise Proficiency",
            content="All skill keywords present",
            level=2,
            start_line=0,
            end_line=0,
            word_count=4,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.confidence <= 1.0

    def test_content_based_confidence_lower_than_title(self, classifier: SectionClassifier) -> None:
        """Test confidence from content-based classification is lower than title."""
        # Title-based classification
        section_title = MarkdownSection(
            title="Skills",
            content="Details",
            level=2,
            start_line=0,
            end_line=0,
            word_count=1,
            line_count=1,
            has_list=False,
        )
        result_title = classifier.classify(section_title)

        # Content-based classification (same keyword)
        section_content = MarkdownSection(
            title=None,
            content="Skills-based requirements here",
            level=-2,
            start_line=0,
            end_line=0,
            word_count=3,
            line_count=1,
            has_list=False,
        )
        result_content = classifier.classify(section_content)

        # Content-based confidence should be lower
        assert result_content.confidence < result_title.confidence


# ============================================================================
# Phase 7: is_skip Flag Testing
# ============================================================================


class TestIsSkipFlag:
    """Test is_skip flag for SKIP sections."""

    @pytest.fixture
    def classifier(self) -> SectionClassifier:
        """Provide a default classifier instance."""
        return SectionClassifier()

    def test_skip_flag_true_for_skip_sections(self, classifier: SectionClassifier) -> None:
        """Verify is_skip is True for SKIP sections."""
        for skip_keyword in ["benefits", "legal", "eoe", "union"]:
            section = MarkdownSection(
                title=f"Our {skip_keyword.title()}",
                content="Details",
                level=2,
                start_line=0,
                end_line=0,
                word_count=1,
                line_count=1,
                has_list=False,
            )
            result = classifier.classify(section)
            assert result.is_skip is True, f"Failed for keyword: {skip_keyword}"

    def test_skip_flag_false_for_non_skip(self, classifier: SectionClassifier) -> None:
        """Verify is_skip is False for non-SKIP sections."""
        for section_type, keyword in [
            (SectionType.SKILLS, "Skills"),
            (SectionType.QUALIFICATIONS, "Requirements"),
            (SectionType.RESPONSIBILITIES, "Responsibilities"),
        ]:
            section = MarkdownSection(
                title=keyword,
                content="Details",
                level=2,
                start_line=0,
                end_line=0,
                word_count=1,
                line_count=1,
                has_list=False,
            )
            result = classifier.classify(section)
            assert result.is_skip is False
            assert result.section_type == section_type


# ============================================================================
# Phase 8: matched_keywords Testing
# ============================================================================


class TestMatchedKeywords:
    """Test matched_keywords tuple."""

    @pytest.fixture
    def classifier(self) -> SectionClassifier:
        """Provide a default classifier instance."""
        return SectionClassifier()

    def test_empty_matched_keywords_for_unmatched(self, classifier: SectionClassifier) -> None:
        """Verify empty tuple for unmatched sections."""
        section = MarkdownSection(
            title="Random Title",
            content="No keywords",
            level=2,
            start_line=0,
            end_line=0,
            word_count=2,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.matched_keywords == ()

    def test_matched_keywords_single(self, classifier: SectionClassifier) -> None:
        """Test matched_keywords with single keyword."""
        section = MarkdownSection(
            title="Skills",
            content="Details",
            level=2,
            start_line=0,
            end_line=0,
            word_count=1,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert len(result.matched_keywords) == 1
        assert "skill" in result.matched_keywords

    def test_matched_keywords_multiple(self, classifier: SectionClassifier) -> None:
        """Test matched_keywords with multiple keywords."""
        section = MarkdownSection(
            title="Technical Skills and Core Competencies",
            content="Details",
            level=2,
            start_line=0,
            end_line=0,
            word_count=1,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert len(result.matched_keywords) > 1
        # All matched keywords should be from SKILLS_KEYWORDS
        for kw in result.matched_keywords:
            assert kw in SKILLS_KEYWORDS

    def test_matched_keywords_are_tuple(self, classifier: SectionClassifier) -> None:
        """Verify matched_keywords is a tuple (immutable)."""
        section = MarkdownSection(
            title="Technical Skills",
            content="Details",
            level=2,
            start_line=0,
            end_line=0,
            word_count=1,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert isinstance(result.matched_keywords, tuple)


# ============================================================================
# Phase 9: classify_section() Convenience Function
# ============================================================================


class TestClassifySectionFunction:
    """Test module-level classify_section() convenience function."""

    def test_classify_section_with_default_classifier(self) -> None:
        """Test classify_section without providing classifier."""
        section = MarkdownSection(
            title="Technical Skills",
            content="Python, Java",
            level=2,
            start_line=0,
            end_line=0,
            word_count=2,
            line_count=1,
            has_list=False,
        )
        result = classify_section(section)
        assert result.section_type == SectionType.SKILLS

    def test_classify_section_with_custom_classifier(self) -> None:
        """Test classify_section with custom classifier."""
        custom_keywords = frozenset({"custom"})
        classifier = SectionClassifier(skip_keywords=custom_keywords)

        section = MarkdownSection(
            title="Custom Skip",
            content="Details",
            level=2,
            start_line=0,
            end_line=0,
            word_count=1,
            line_count=1,
            has_list=False,
        )
        result = classify_section(section, classifier=classifier)
        assert result.section_type == SectionType.SKIP

    def test_classify_section_stateless(self) -> None:
        """Test classify_section is stateless (idempotent)."""
        section = MarkdownSection(
            title="Requirements",
            content="Details",
            level=2,
            start_line=0,
            end_line=0,
            word_count=1,
            line_count=1,
            has_list=False,
        )
        result1 = classify_section(section)
        result2 = classify_section(section)
        assert result1 == result2

    def test_classify_section_raises_on_none(self) -> None:
        """Test classify_section raises ValueError for None section."""
        with pytest.raises(ValueError, match="section cannot be None"):
            classify_section(None)  # type: ignore


# ============================================================================
# Phase 10: Parametrized Tests for Comprehensive Coverage
# ============================================================================


class TestParametrizedClassification:
    """Parametrized tests for comprehensive coverage."""

    @pytest.fixture
    def classifier(self) -> SectionClassifier:
        """Provide a default classifier instance."""
        return SectionClassifier()

    @pytest.mark.parametrize(
        "title,expected_type",
        [
            ("Technical Skills", SectionType.SKILLS),
            ("Skill Requirements", SectionType.SKILLS),
            ("Core Competencies", SectionType.SKILLS),
            ("Ability to Code", SectionType.SKILLS),
            ("Expertise Required", SectionType.SKILLS),
            ("Proficiency in Python", SectionType.SKILLS),
        ],
    )
    def test_all_skills_keywords(self, classifier: SectionClassifier, title: str, expected_type: SectionType) -> None:
        """Test all SKILLS_KEYWORDS trigger correct classification."""
        section = MarkdownSection(
            title=title,
            content="Details",
            level=2,
            start_line=0,
            end_line=0,
            word_count=1,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == expected_type

    @pytest.mark.parametrize(
        "title,expected_type",
        [
            ("Requirements", SectionType.QUALIFICATIONS),
            ("Qualification Requirements", SectionType.QUALIFICATIONS),
            ("Essential Qualifications", SectionType.QUALIFICATIONS),
        ],
    )
    def test_all_qualifications_keywords(
        self, classifier: SectionClassifier, title: str, expected_type: SectionType
    ) -> None:
        """Test all QUALIFICATIONS_KEYWORDS trigger correct classification."""
        section = MarkdownSection(
            title=title,
            content="Details",
            level=2,
            start_line=0,
            end_line=0,
            word_count=1,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == expected_type

    @pytest.mark.parametrize(
        "title,expected_type",
        [
            ("Responsibilities", SectionType.RESPONSIBILITIES),
            ("My Responsibilities", SectionType.RESPONSIBILITIES),
            ("What You'll Do", SectionType.RESPONSIBILITIES),
        ],
    )
    def test_all_responsibilities_keywords(
        self, classifier: SectionClassifier, title: str, expected_type: SectionType
    ) -> None:
        """Test all RESPONSIBILITIES_KEYWORDS trigger correct classification."""
        section = MarkdownSection(
            title=title,
            content="Details",
            level=2,
            start_line=0,
            end_line=0,
            word_count=1,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == expected_type

    @pytest.mark.parametrize(
        "title,expected_type",
        [
            ("Knowledge Required", SectionType.KNOWLEDGE),
            ("Experience Level", SectionType.KNOWLEDGE),
        ],
    )
    def test_all_knowledge_keywords(
        self, classifier: SectionClassifier, title: str, expected_type: SectionType
    ) -> None:
        """Test all KNOWLEDGE_KEYWORDS trigger correct classification."""
        section = MarkdownSection(
            title=title,
            content="Details",
            level=2,
            start_line=0,
            end_line=0,
            word_count=1,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == expected_type

    @pytest.mark.parametrize(
        "title,expected_type",
        [
            ("Job Description", SectionType.DESCRIPTION),
            ("Role Overview", SectionType.DESCRIPTION),
            ("Position Summary", SectionType.DESCRIPTION),
            ("Intro to Position", SectionType.DESCRIPTION),
        ],
    )
    def test_all_description_keywords(
        self, classifier: SectionClassifier, title: str, expected_type: SectionType
    ) -> None:
        """Test all DESCRIPTION_KEYWORDS trigger correct classification."""
        section = MarkdownSection(
            title=title,
            content="Details",
            level=2,
            start_line=0,
            end_line=0,
            word_count=1,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == expected_type

    @pytest.mark.parametrize("skip_keyword", list(SKIP_SECTIONS)[:10])
    def test_skip_keywords_subset(self, classifier: SectionClassifier, skip_keyword: str) -> None:
        """Test subset of SKIP_SECTIONS keywords."""
        section = MarkdownSection(
            title=f"Our {skip_keyword.title()}",
            content="Details",
            level=2,
            start_line=0,
            end_line=0,
            word_count=1,
            line_count=1,
            has_list=False,
        )
        result = classifier.classify(section)
        assert result.section_type == SectionType.SKIP
        assert result.is_skip is True


# ============================================================================
# Phase 11: Classifier with None Section Tests
# ============================================================================


class TestNoneSectionHandling:
    """Test handling of None and invalid sections."""

    def test_classify_raises_on_none_section(self) -> None:
        """Test SectionClassifier.classify raises ValueError for None."""
        classifier = SectionClassifier()
        with pytest.raises(ValueError, match="section cannot be None"):
            classifier.classify(None)  # type: ignore

    def test_classify_section_function_raises_on_none(self) -> None:
        """Test classify_section function raises ValueError for None."""
        with pytest.raises(ValueError, match="section cannot be None"):
            classify_section(None)  # type: ignore


# ============================================================================
# Run with: uv run pytest tests/poc/tweak/test_markdown_section_classifier.py -v
# ============================================================================
