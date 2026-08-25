"""Markdown section classification with keyword matching and confidence scoring.

This module provides utilities for classifying markdown sections (extracted via
MarkdownSpanRuler) into semantic types: SKILLS, QUALIFICATIONS, RESPONSIBILITIES,
KNOWLEDGE, DESCRIPTION, SKIP, OTHER, or UNLABELED.

Uses keyword matching on section title and content to determine type and confidence.
Supports both titled sections (level 1-3 headers, bold markers) and untitled content
(level -2 sections without explicit headers).

Classes:
    SectionType: Enum of section types
    SectionClassification: Classification result with type, matched keywords, confidence
    SectionClassifier: Main classifier with keyword-based logic

Functions:
    classify_section: Module-level convenience wrapper for classifying a single section
"""

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Optional, Tuple

from src.poc.tweak.multi_line_paragraph import MarkdownSection

# ============================================================================
# Phase 1: Enums and Data Structures
# ============================================================================


class SectionType(Enum):
    """Semantic classification of a markdown section.

    Enum Values:
        SKILLS: Technical skills, abilities, competencies (e.g., "Skills", "Technical")
        QUALIFICATIONS: Required or desired qualifications (e.g., "Requirements", "Qualifications")
        RESPONSIBILITIES: Job duties and responsibilities (e.g., "Responsibilities", "Duties")
        KNOWLEDGE: Knowledge and experience (e.g., "Knowledge", "Experience")
        DESCRIPTION: General job or role description (e.g., "Description", "Summary")
        SKIP: Boilerplate sections to exclude (e.g., "Benefits", "Company Info", "Legal")
        OTHER: Sections that don't fit primary categories
        UNLABELED: Sections with no title and unclassifiable content
    """

    SKILLS = "skills"
    QUALIFICATIONS = "qualifications"
    RESPONSIBILITIES = "responsibilities"
    KNOWLEDGE = "knowledge"
    DESCRIPTION = "description"
    SKIP = "skip"
    OTHER = "other"
    UNLABELED = "unlabeled"


@dataclass(frozen=True)
class SectionClassification:
    """Result of classifying a markdown section.

    Attributes:
        section_type: Semantic type of the section (SectionType enum value)
        matched_keywords: Tuple of keywords from title/content that triggered classification
        confidence: Confidence score from 0.0 to 1.0
        is_skip: True if section should be excluded from processing
    """

    section_type: SectionType
    matched_keywords: Tuple[str, ...] = ()
    confidence: float = 0.0
    is_skip: bool = False

    def __post_init__(self) -> None:
        """Validate confidence is in [0.0, 1.0]."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")


# ============================================================================
# Phase 2: Keyword Definitions (copied from Preprocessor)
# ============================================================================


# Skip sections: benefits, legal/compliance, company info, hiring logistics
# Source: src/tokenization/preprocessor.py:29-80
SKIP_SECTIONS: FrozenSet[str] = frozenset(
    {
        "benefits",
        "compensation",
        "salary",
        "pay range",
        "401",
        "retirement",
        "insurance",
        "health",
        "dental",
        "vision",
        "pto",
        "vacation",
        "about",
        "company",
        "culture",
        "commitment",
        "team",
        "our",
        "equal opportunity",
        "eoe",
        "affirmative action",
        "disability",
        "background check",
        "export control",
        "security clearance",
        "visa",
        "apply",
        "posting date",
        "posted",
        "application close",
        "codevue",
        "shift",
        "location",
        "work location",
        "travel",
        "working condition",
        "fte",
        "temporary",
        "education:",
        "hiring practice",
        "bargaining",
        "conflict of interest",
        "drug free",
        "e-verify",
        "right to work",
        "safety sensitive",
        "technical assessment",
        "total rewards",
        "union",
        "contingent upon award",
    }
)

# Keywords indicating skills sections
# Source: src/tokenization/preprocessor.py:1557 & _classify_section_from_header (L1156)
SKILLS_KEYWORDS: Tuple[str, ...] = ("skill", "technical", "core", "competency", "ability", "expertise", "proficiency")

# Keywords indicating qualifications/requirements sections
# Source: _classify_section_from_header (L1154) - qualifications branch
QUALIFICATIONS_KEYWORDS: Tuple[str, ...] = ("requirement", "qualif", "essential")

# Keywords indicating responsibilities sections
# Source: _classify_section_from_header (L1160) - responsibilities branch
RESPONSIBILITIES_KEYWORDS: Tuple[str, ...] = ("respons", "duty", "what you")

# Keywords indicating knowledge/experience sections
# Source: _classify_section_from_header (L1158) - knowledge branch
KNOWLEDGE_KEYWORDS: Tuple[str, ...] = ("knowledge", "experience")

# Keywords indicating description/overview sections
DESCRIPTION_KEYWORDS: Tuple[str, ...] = ("description", "overview", "summary", "about", "intro")


# ============================================================================
# Phase 3: SectionClassifier Class
# ============================================================================


class SectionClassifier:
    """Classify markdown sections into semantic types via keyword matching.

    Uses title and content keywords to determine section type with confidence scoring.
    Supports optional custom skip keywords. Handles edge cases like untitled sections
    (level -2) by classifying from content.

    Attributes:
        skip_keywords: Frozen set of keywords indicating sections to skip/exclude

    Example:
        >>> classifier = SectionClassifier()
        >>> section = MarkdownSection(
        ...     title="Technical Skills",
        ...     content="Python, Java, SQL",
        ...     level=2,
        ...     start_line=0,
        ...     end_line=2,
        ...     word_count=4,
        ...     line_count=1,
        ...     has_list=False
        ... )
        >>> result = classifier.classify(section)
        >>> result.section_type
        <SectionType.SKILLS: 'skills'>
        >>> result.matched_keywords
        ('technical', 'skill')
        >>> result.confidence
        0.9
    """

    def __init__(self, skip_keywords: Optional[FrozenSet[str]] = None) -> None:
        """Initialize classifier with optional custom skip keywords.

        Args:
            skip_keywords: Optional frozenset of keywords indicating skip sections.
                          If None, uses default SKIP_SECTIONS.
        """
        self.skip_keywords = skip_keywords if skip_keywords is not None else SKIP_SECTIONS

    def classify(self, section: MarkdownSection) -> SectionClassification:
        """Classify a markdown section into a semantic type.

        Classification logic (in precedence order):
        1. Check title if present (level 1-3 or -1)
        2. If no title or level=-2, classify from content (first N words)
        3. Match keywords against SKIP, SKILLS, QUALIFICATIONS, RESPONSIBILITIES, KNOWLEDGE, DESCRIPTION
        4. Fall back to OTHER or UNLABELED based on content presence

        Args:
            section: MarkdownSection to classify

        Returns:
            SectionClassification with type, matched keywords, confidence, and is_skip flag

        Raises:
            ValueError: If section is None
        """
        if section is None:
            raise ValueError("section cannot be None")

        # Extract normalized text for classification
        title_text = self._normalize_text(section.title) if section.title else ""
        content_text = self._normalize_text(section.content) if section.content else ""

        # Prefer title-based classification; fall back to content if no title or level=-2
        if title_text and section.level != -2:
            return self._classify_from_title(title_text, content_text)
        else:
            # No title or untitled section: classify from content
            return self._classify_from_content(content_text)

    def _normalize_text(self, text: str) -> str:
        """Normalize text for keyword matching (lowercase, strip).

        Args:
            text: Text to normalize

        Returns:
            Normalized text (lowercase, stripped)
        """
        return text.lower().strip() if text else ""

    def _classify_from_title(self, title_text: str, content_text: str) -> SectionClassification:
        """Classify section based on its title.

        Checks title against skip keywords first, then semantic keywords
        in order: SKILLS → QUALIFICATIONS → RESPONSIBILITIES → KNOWLEDGE → DESCRIPTION → OTHER.

        Args:
            title_text: Normalized (lowercase) title text
            content_text: Normalized (lowercase) content text

        Returns:
            SectionClassification
        """
        # Check skip sections first (highest precedence)
        skip_matches = tuple(kw for kw in self.skip_keywords if kw in title_text)
        if skip_matches:
            return SectionClassification(
                section_type=SectionType.SKIP,
                matched_keywords=skip_matches,
                confidence=min(1.0, 0.5 + (len(skip_matches) * 0.25)),
                is_skip=True,
            )

        # Check skills keywords
        skills_matches = tuple(kw for kw in SKILLS_KEYWORDS if kw in title_text)
        if skills_matches:
            confidence = min(1.0, 0.6 + (len(skills_matches) * 0.2))
            return SectionClassification(
                section_type=SectionType.SKILLS,
                matched_keywords=skills_matches,
                confidence=confidence,
                is_skip=False,
            )

        # Check qualifications keywords
        qual_matches = tuple(kw for kw in QUALIFICATIONS_KEYWORDS if kw in title_text)
        if qual_matches:
            confidence = min(1.0, 0.6 + (len(qual_matches) * 0.2))
            return SectionClassification(
                section_type=SectionType.QUALIFICATIONS,
                matched_keywords=qual_matches,
                confidence=confidence,
                is_skip=False,
            )

        # Check responsibilities keywords
        resp_matches = tuple(kw for kw in RESPONSIBILITIES_KEYWORDS if kw in title_text)
        if resp_matches:
            confidence = min(1.0, 0.6 + (len(resp_matches) * 0.2))
            return SectionClassification(
                section_type=SectionType.RESPONSIBILITIES,
                matched_keywords=resp_matches,
                confidence=confidence,
                is_skip=False,
            )

        # Check knowledge keywords
        know_matches = tuple(kw for kw in KNOWLEDGE_KEYWORDS if kw in title_text)
        if know_matches:
            confidence = min(1.0, 0.6 + (len(know_matches) * 0.2))
            return SectionClassification(
                section_type=SectionType.KNOWLEDGE,
                matched_keywords=know_matches,
                confidence=confidence,
                is_skip=False,
            )

        # Check description keywords
        desc_matches = tuple(kw for kw in DESCRIPTION_KEYWORDS if kw in title_text)
        if desc_matches:
            confidence = min(1.0, 0.6 + (len(desc_matches) * 0.2))
            return SectionClassification(
                section_type=SectionType.DESCRIPTION,
                matched_keywords=desc_matches,
                confidence=confidence,
                is_skip=False,
            )

        # No keywords matched: return OTHER
        return SectionClassification(
            section_type=SectionType.OTHER,
            matched_keywords=(),
            confidence=0.3,
            is_skip=False,
        )

    def _classify_from_content(self, content_text: str) -> SectionClassification:
        """Classify section based on its content when no title is available.

        Uses first N words of content as pseudo-title for keyword matching.
        Falls back to DESCRIPTION, OTHER, or UNLABELED based on content presence.

        Args:
            content_text: Normalized (lowercase) content text

        Returns:
            SectionClassification
        """
        if not content_text:
            # Empty content: unlabeled
            return SectionClassification(
                section_type=SectionType.UNLABELED,
                matched_keywords=(),
                confidence=0.0,
                is_skip=False,
            )

        # Use first ~50 words as pseudo-title for matching
        first_words = " ".join(content_text.split()[:50])

        # Check skip keywords in content prefix
        skip_matches = tuple(kw for kw in self.skip_keywords if kw in first_words)
        if skip_matches:
            return SectionClassification(
                section_type=SectionType.SKIP,
                matched_keywords=skip_matches,
                confidence=min(1.0, 0.4 + (len(skip_matches) * 0.15)),
                is_skip=True,
            )

        # Check skills keywords in content prefix
        skills_matches = tuple(kw for kw in SKILLS_KEYWORDS if kw in first_words)
        if skills_matches:
            confidence = min(1.0, 0.5 + (len(skills_matches) * 0.15))
            return SectionClassification(
                section_type=SectionType.SKILLS,
                matched_keywords=skills_matches,
                confidence=confidence,
                is_skip=False,
            )

        # Check qualifications keywords in content prefix
        qual_matches = tuple(kw for kw in QUALIFICATIONS_KEYWORDS if kw in first_words)
        if qual_matches:
            confidence = min(1.0, 0.5 + (len(qual_matches) * 0.15))
            return SectionClassification(
                section_type=SectionType.QUALIFICATIONS,
                matched_keywords=qual_matches,
                confidence=confidence,
                is_skip=False,
            )

        # Check responsibilities keywords in content prefix
        resp_matches = tuple(kw for kw in RESPONSIBILITIES_KEYWORDS if kw in first_words)
        if resp_matches:
            confidence = min(1.0, 0.5 + (len(resp_matches) * 0.15))
            return SectionClassification(
                section_type=SectionType.RESPONSIBILITIES,
                matched_keywords=resp_matches,
                confidence=confidence,
                is_skip=False,
            )

        # Check knowledge keywords in content prefix
        know_matches = tuple(kw for kw in KNOWLEDGE_KEYWORDS if kw in first_words)
        if know_matches:
            confidence = min(1.0, 0.5 + (len(know_matches) * 0.15))
            return SectionClassification(
                section_type=SectionType.KNOWLEDGE,
                matched_keywords=know_matches,
                confidence=confidence,
                is_skip=False,
            )

        # Check description keywords in content prefix
        desc_matches = tuple(kw for kw in DESCRIPTION_KEYWORDS if kw in first_words)
        if desc_matches:
            confidence = min(1.0, 0.5 + (len(desc_matches) * 0.15))
            return SectionClassification(
                section_type=SectionType.DESCRIPTION,
                matched_keywords=desc_matches,
                confidence=confidence,
                is_skip=False,
            )

        # Content exists but no keywords matched: classify as DESCRIPTION
        # (default fallback for body text sections)
        return SectionClassification(
            section_type=SectionType.DESCRIPTION,
            matched_keywords=(),
            confidence=0.2,
            is_skip=False,
        )


# ============================================================================
# Phase 4: Module-Level Convenience Function
# ============================================================================


def classify_section(section: MarkdownSection, classifier: Optional[SectionClassifier] = None) -> SectionClassification:
    """Classify a markdown section using default or provided classifier.

    Convenience wrapper for single-section classification. If no classifier
    is provided, creates and uses a default SectionClassifier instance.

    Args:
        section: MarkdownSection to classify
        classifier: Optional SectionClassifier instance. If None, uses default.

    Returns:
        SectionClassification with type, matched keywords, confidence, and is_skip

    Raises:
        ValueError: If section is None

    Example:
        >>> section = MarkdownSection(
        ...     title="Requirements",
        ...     content="5+ years Python experience",
        ...     level=2,
        ...     start_line=5,
        ...     end_line=7,
        ...     word_count=5,
        ...     line_count=1,
        ...     has_list=False
        ... )
        >>> result = classify_section(section)
        >>> result.section_type
        <SectionType.QUALIFICATIONS: 'qualifications'>
    """
    if section is None:
        raise ValueError("section cannot be None")

    if classifier is None:
        classifier = SectionClassifier()

    return classifier.classify(section)
