"""Markdown section classification with keyword matching and confidence scoring.

This module provides utilities for classifying markdown sections (extracted via
MarkdownSpanRuler) into semantic types: SKILLS, QUALIFICATIONS, RESPONSIBILITIES,
KNOWLEDGE, DESCRIPTION, SKIP, OTHER, or UNLABELED.

Uses keyword matching on section title and content to determine type and confidence.
Supports both titled sections (level 1-3 headers, bold markers) and untitled content
(level -2 sections without explicit headers).

Supports multi-type classification: a single section can match multiple semantic types
(e.g., 'Skills and Responsibilities' → both SKILLS and RESPONSIBILITIES in results).

Classes:
    SectionType: Enum of section types
    TypeClassification: Single section type with confidence
    KeywordMatch: Metadata for keyword occurrence (stub for future full integration)
    SectionClassification: Classification result with type, matched keywords, confidence
    SectionClassifier: Main classifier with keyword-based logic

Functions:
    calculate_confidence: Calculate confidence score for a matched classification
    fallback_confidence: Generate fallback classification when no keywords match
    classify_section: Module-level convenience wrapper for classifying a single section

Example (multi-type classification):
    Title: "Skills and Responsibilities"
    Result: all_types = (
        TypeClassification(SectionType.SKILLS, 0.85, ("skill", "technical")),
        TypeClassification(SectionType.RESPONSIBILITIES, 0.75, ("responsibility", "manage")),
    )
    labels = {SectionType.SKILLS, SectionType.RESPONSIBILITIES}
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet, List, Literal, Optional, Tuple

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
class TypeClassification:
    """Single section type with confidence.

    Represents a classification prediction for a markdown section type with an
    associated confidence score. Serves as a building block for multi-type
    classification systems (e.g., SectionClassification.all_types may contain
    multiple TypeClassification instances for scenarios requiring multiple type
    predictions).

    Attributes:
        section_type: The semantic type of the section (SectionType enum value)
        confidence: Confidence score for this classification, in range [0.0, 1.0].
                   0.0 means no confidence, 1.0 means complete confidence.
        matched_keywords: Tuple of keywords from section title or content that
                         contributed to this classification. Empty tuple if no
                         keywords matched.

    Example:
        Single keyword match with high confidence:
        >>> tc = TypeClassification(
        ...     section_type=SectionType.SKILLS,
        ...     confidence=0.9,
        ...     matched_keywords=("technical",)
        ... )
        >>> tc.section_type
        <SectionType.SKILLS: 'skills'>
        >>> tc.confidence
        0.9

        Multiple keywords increase confidence:
        >>> tc = TypeClassification(
        ...     section_type=SectionType.QUALIFICATIONS,
        ...     confidence=0.85,
        ...     matched_keywords=("requirement", "qualif", "essential")
        ... )
        >>> len(tc.matched_keywords)
        3
    """

    section_type: SectionType
    confidence: float
    matched_keywords: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate confidence is in [0.0, 1.0]."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")


@dataclass(frozen=True)
class KeywordMatch:
    """Metadata for keyword occurrence (stub for future full integration).

    This is a stub dataclass designed for future integration with full keyword
    matching capabilities. It captures metadata about each keyword match found
    during section classification, including which keyword matched, what section
    type it indicates, and where in the content it was found.

    The `position` field is intentionally set to -1 as a sentinel value, indicating
    that the position has not yet been computed. In a follow-up issue, the
    `_classify_from_title()` and `_classify_from_content()` methods will be enhanced
    to populate KeywordMatch instances with actual position data and to populate
    the `SectionClassification.keyword_matches` list (currently empty).

    Attributes:
        keyword: The keyword string that matched during classification
        section_type: The SectionType that this keyword indicates (from keyword definitions)
        source: Where the keyword was found ("title" or "content")
        position: Character position of keyword in source text (-1 = not yet computed)

    Example:
        Create a keyword match stub (position not computed):
        >>> km = KeywordMatch(
        ...     keyword="requirement",
        ...     section_type=SectionType.QUALIFICATIONS,
        ...     source="title",
        ...     position=-1
        ... )
        >>> km.keyword
        'requirement'
        >>> km.position
        -1

    Note:
        Position computation will be added in a follow-up issue when full keyword
        matching integration is complete. See SectionClassification.keyword_matches
        for how this will be used to track all matched keywords in a classification.
    """

    keyword: str
    section_type: SectionType
    source: Literal["title", "content"]
    position: int = -1


# ============================================================================
# Phase 2: Confidence Scoring Functions
# ============================================================================


def calculate_confidence(match_count: int, source: Literal["title", "content"], section_type: SectionType) -> float:
    """Calculate confidence score for a matched classification.

    Computes a confidence value based on the number of matching keywords, where
    the keyword was found (title vs. content), and the section type (SKIP sections
    use lower base confidence than other types, reflecting inherent uncertainty
    with boilerplate matching).

    The confidence calculation uses four distinct tiers:

    | Source  | Section Type | Base | Per-Match | Max |
    |---------|--------------|------|-----------|-----|
    | title   | SKIP         | 0.50 | +0.25     | 1.0 |
    | title   | Other*       | 0.60 | +0.20     | 1.0 |
    | content | SKIP         | 0.40 | +0.15     | 1.0 |
    | content | Other*       | 0.50 | +0.15     | 1.0 |

    * "Other" includes: SKILLS, QUALIFICATIONS, RESPONSIBILITIES, KNOWLEDGE, DESCRIPTION, OTHER, UNLABELED.

    **Tier Philosophy:**
    - Title-based matches are more reliable than content-based (higher base, faster growth)
    - SKIP sections carry lower confidence due to variable boilerplate patterns
    - Multiple matches incrementally increase confidence up to 1.0 (capped)

    Args:
        match_count: Number of keywords matched (must be >= 1; called only when matches exist)
        source: Source of the match ("title" or "content")
        section_type: The SectionType to classify as (determines if SKIP or Other)

    Returns:
        Confidence score in range [0.0, 1.0]

    Example:
        Title-based SKIP section with 1 match:
        >>> calculate_confidence(1, "title", SectionType.SKIP)
        0.75  # 0.5 + (1 * 0.25)

        Title-based SKILLS section with 3 matches:
        >>> calculate_confidence(3, "title", SectionType.SKILLS)
        1.0  # min(1.0, 0.6 + (3 * 0.2) = 1.2)

        Content-based QUALIFICATIONS section with 2 matches:
        >>> calculate_confidence(2, "content", SectionType.QUALIFICATIONS)
        0.8  # 0.5 + (2 * 0.15)

        Content-based SKIP section with 4 matches:
        >>> calculate_confidence(4, "content", SectionType.SKIP)
        1.0  # min(1.0, 0.4 + (4 * 0.15) = 1.0)

    Note:
        This function assumes match_count >= 1. For no matches, use fallback_confidence()
        instead. Returned confidence values are always in [0.0, 1.0].
    """
    if section_type == SectionType.SKIP:
        # SKIP sections: lower base confidence, slower growth
        if source == "title":
            return min(1.0, 0.5 + (match_count * 0.25))
        else:  # source == "content"
            return min(1.0, 0.4 + (match_count * 0.15))
    else:
        # All other section types: higher base, standard growth
        if source == "title":
            return min(1.0, 0.6 + (match_count * 0.2))
        else:  # source == "content"
            return min(1.0, 0.5 + (match_count * 0.15))


def fallback_confidence(source: Literal["title", "content"], has_content_text: bool) -> Tuple[SectionType, float]:
    """Generate fallback classification when no keywords match.

    When keyword matching fails to find any matches, this function returns a
    sensible default section type and low confidence score based on:
    - Source (title vs. content)
    - Whether content is actually present

    The three cases are:

    | Source  | Has Content | Return Type       | Confidence |
    |---------|-------------|-------------------|------------|
    | title   | (any)       | OTHER             | 0.30       |
    | content | true        | DESCRIPTION       | 0.20       |
    | content | false       | UNLABELED         | 0.00       |

    **Fallback Philosophy:**
    - Titled sections with no keyword match default to OTHER (generic fallback)
    - Content sections with text default to DESCRIPTION (body text is typically descriptive)
    - Empty content sections are UNLABELED (no information for classification)

    Args:
        source: Where we were attempting to classify from ("title" or "content")
        has_content_text: True if content is present and non-empty, False otherwise

    Returns:
        Tuple of (SectionType, confidence: float). Confidence is always in [0.0, 1.0].

    Example:
        Titled section with no keyword match:
        >>> fallback_confidence("title", True)
        (<SectionType.OTHER: 'other'>, 0.3)

        Content-based section with text but no keywords:
        >>> fallback_confidence("content", True)
        (<SectionType.DESCRIPTION: 'description'>, 0.2)

        Empty content section (untitled, no text):
        >>> fallback_confidence("content", False)
        (<SectionType.UNLABELED: 'unlabeled'>, 0.0)

    Note:
        This function is used internally by classification methods to handle
        no-match scenarios. It always returns a valid (SectionType, float) tuple
        where the float is in [0.0, 1.0].
    """
    if source == "title":
        # Title-based: no keywords matched, default to OTHER with low confidence
        return (SectionType.OTHER, 0.3)
    else:  # source == "content"
        # Content-based: depends on whether content is present
        if has_content_text:
            # Content exists, no keywords matched: default to DESCRIPTION
            # (body text is typically descriptive)
            return (SectionType.DESCRIPTION, 0.2)
        else:
            # No content at all: UNLABELED (no information for classification)
            return (SectionType.UNLABELED, 0.0)


@dataclass(frozen=True)
class SectionClassification:
    """Multi-type classification result with convenience labels field.

    Represents the classification of a markdown section supporting multiple section
    types per section (e.g., a title like "Skills and Responsibilities" can have
    both SKILLS and RESPONSIBILITIES types in all_types).

    Attributes:
        all_types: Tuple of TypeClassification instances, sorted by confidence
                  descending (highest confidence first). Each instance represents
                  a matched section type with its confidence and keywords.
        labels: Convenience FrozenSet of all matched SectionTypes, derived from
               all_types. Provides quick access to all matched types without
               iterating through all_types.
        is_skip: Boolean flag indicating whether this section should be excluded
                from processing (True if any type is SKIP, or explicitly marked).

    Example (single-type classification):
        >>> classifications = [
        ...     TypeClassification(SectionType.SKILLS, 0.85, ("skill",)),
        ... ]
        >>> result = SectionClassification.from_type_classifications(classifications)
        >>> result.all_types[0].section_type
        <SectionType.SKILLS: 'skills'>
        >>> result.labels
        frozenset({SectionType.SKILLS})
        >>> result.is_skip
        False

        Multi-type classification (e.g., "Skills and Responsibilities" title):
        >>> classifications = [
        ...     TypeClassification(SectionType.SKILLS, 0.85, ("skill",)),
        ...     TypeClassification(SectionType.RESPONSIBILITIES, 0.75, ("responsibility",)),
        ... ]
        >>> result = SectionClassification.from_type_classifications(classifications)
        >>> len(result.all_types)
        2
        >>> result.all_types[0].confidence  # Sorted by confidence descending
        0.85
        >>> result.labels
        frozenset({SectionType.SKILLS, SectionType.RESPONSIBILITIES})

    Note:
        Breaking Change (POC Phase): Old fields (section_type, matched_keywords,
        confidence) removed. Use all_types[0] to access primary type/confidence,
        or labels for all matched types. is_skip field remains.
    """

    all_types: Tuple[TypeClassification, ...] = ()
    labels: FrozenSet[SectionType] = field(default_factory=frozenset)
    is_skip: bool = False

    @classmethod
    def from_type_classifications(
        cls,
        type_classifications: List[TypeClassification],
        is_skip: bool = False,
    ) -> "SectionClassification":
        """Build SectionClassification from TypeClassification list.

        Sorts type_classifications by confidence descending.
        Derives labels (FrozenSet) from all section types.

        Args:
            type_classifications: List of TypeClassification instances to combine
            is_skip: Whether this section should be marked as SKIP category

        Returns:
            New SectionClassification with sorted all_types and computed labels

        Example:
            >>> classifications = [
            ...     TypeClassification(SectionType.SKILLS, 0.85, ("skill",)),
            ...     TypeClassification(SectionType.RESPONSIBILITIES, 0.75, ("responsibility",)),
            ... ]
            >>> result = SectionClassification.from_type_classifications(classifications)
            >>> result.all_types[0].section_type  # Highest confidence first
            <SectionType.SKILLS: 'skills'>
            >>> result.labels
            frozenset({SectionType.SKILLS, SectionType.RESPONSIBILITIES})
        """
        sorted_types = tuple(sorted(type_classifications, key=lambda tc: tc.confidence, reverse=True))
        labels = frozenset(tc.section_type for tc in sorted_types)
        return cls(all_types=sorted_types, labels=labels, is_skip=is_skip)


# ============================================================================
# Phase 3: Keyword Definitions (copied from Preprocessor)
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
# Phase 4: SectionClassifier Class
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
        >>> result.all_types[0].section_type
        <SectionType.SKILLS: 'skills'>
    """

    def __init__(self, skip_keywords: Optional[FrozenSet[str]] = None) -> None:
        """Initialize classifier with optional custom skip keywords.

        Args:
            skip_keywords: Optional frozenset of keywords indicating skip sections.
                          If None, uses default SKIP_SECTIONS.
        """
        self.skip_keywords = skip_keywords if skip_keywords is not None else SKIP_SECTIONS

    def classify(self, section: MarkdownSection) -> SectionClassification:
        """Classify a markdown section into semantic type(s).

        Returns SectionClassification with all matched types in all_types tuple,
        sorted by confidence descending. Supports multi-type classification: a single
        section can match multiple semantic types (e.g., 'Skills and Responsibilities').

        Classification logic (in precedence order):
        1. Check title if present (level 1-3 or -1)
        2. If no title or level=-2, classify from content (first N words)
        3. Collect ALL matching types (no short-circuit; no single-type precedence)
        4. Match keywords against SKIP, SKILLS, QUALIFICATIONS, RESPONSIBILITIES, KNOWLEDGE, DESCRIPTION
        5. Fall back to OTHER or UNLABELED based on content presence

        SKIP Behavior:
        SKIP is classified same as other types (no precedence override yet).
        If any matched type is SKIP, is_skip flag is set to True.
        See follow-up issues for enhanced SKIP logic tuning.

        Args:
            section: MarkdownSection to classify

        Returns:
            SectionClassification with:
            - all_types: Tuple of TypeClassification sorted by confidence descending
            - labels: FrozenSet of all matched SectionTypes
            - is_skip: True if any matched type is SKIP

        Raises:
            ValueError: If section is None

        Example (single-type):
            >>> section = MarkdownSection(
            ...     title="Technical Skills",
            ...     content="Python, Java",
            ...     level=2,
            ...     start_line=0,
            ...     end_line=1,
            ...     word_count=4,
            ...     line_count=1,
            ...     has_list=False
            ... )
            >>> result = classifier.classify(section)
            >>> result.all_types[0].section_type
            <SectionType.SKILLS: 'skills'>

            Multi-type (e.g., "Skills and Responsibilities" title):
            >>> section = MarkdownSection(
            ...     title="Skills and Responsibilities",
            ...     content="Manage Python projects",
            ...     level=2,
            ...     start_line=0,
            ...     end_line=1,
            ...     word_count=4,
            ...     line_count=1,
            ...     has_list=False
            ... )
            >>> result = classifier.classify(section)
            >>> len(result.all_types)
            2
            >>> result.labels
            frozenset({SectionType.SKILLS, SectionType.RESPONSIBILITIES})
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

        Collects ALL matching types (no short-circuit), unlike previous single-type design.
        Uses confidence functions to score each matched type. Falls back to OTHER for
        zero-match case. Returns via factory method.

        Args:
            title_text: Normalized (lowercase) title text
            content_text: Normalized (lowercase) content text

        Returns:
            SectionClassification with all_types sorted by confidence descending

        Example:
            Single-type title ("Technical Skills"):
            >>> result = classifier._classify_from_title("technical skills", "Python, Java")
            >>> len(result.all_types)
            1
            >>> result.all_types[0].section_type
            <SectionType.SKILLS: 'skills'>

            Compound title ("Skills and Responsibilities"):
            >>> result = classifier._classify_from_title("skills and responsibilities", "...")
            >>> len(result.all_types)
            2
            >>> {tc.section_type for tc in result.all_types}
            {<SectionType.SKILLS: 'skills'>, <SectionType.RESPONSIBILITIES: 'responsibilities'>}
        """
        # Initialize container for all matches
        all_matches: dict[SectionType, Tuple[str, ...]] = {}

        # Check all categories (NO EARLY RETURN)
        # SKIP sections
        skip_matches = tuple(kw for kw in self.skip_keywords if kw in title_text)
        if skip_matches:
            all_matches[SectionType.SKIP] = skip_matches

        # SKILLS sections
        skills_matches = tuple(kw for kw in SKILLS_KEYWORDS if kw in title_text)
        if skills_matches:
            all_matches[SectionType.SKILLS] = skills_matches

        # QUALIFICATIONS sections
        qual_matches = tuple(kw for kw in QUALIFICATIONS_KEYWORDS if kw in title_text)
        if qual_matches:
            all_matches[SectionType.QUALIFICATIONS] = qual_matches

        # RESPONSIBILITIES sections
        resp_matches = tuple(kw for kw in RESPONSIBILITIES_KEYWORDS if kw in title_text)
        if resp_matches:
            all_matches[SectionType.RESPONSIBILITIES] = resp_matches

        # KNOWLEDGE sections
        know_matches = tuple(kw for kw in KNOWLEDGE_KEYWORDS if kw in title_text)
        if know_matches:
            all_matches[SectionType.KNOWLEDGE] = know_matches

        # DESCRIPTION sections
        desc_matches = tuple(kw for kw in DESCRIPTION_KEYWORDS if kw in title_text)
        if desc_matches:
            all_matches[SectionType.DESCRIPTION] = desc_matches

        # Build TypeClassification for each matched type
        type_classifications: List[TypeClassification] = []
        for section_type, matched_kws in all_matches.items():
            confidence = calculate_confidence(match_count=len(matched_kws), source="title", section_type=section_type)
            tc = TypeClassification(section_type=section_type, confidence=confidence, matched_keywords=matched_kws)
            type_classifications.append(tc)

        # Handle zero-match case: use fallback
        if not type_classifications:
            fallback_type, fallback_conf = fallback_confidence("title", bool(content_text.strip()))
            type_classifications.append(TypeClassification(fallback_type, fallback_conf, ()))

        # Compute is_skip: True if SKIP is in matched types
        is_skip = SectionType.SKIP in {tc.section_type for tc in type_classifications}

        # Build and return via factory
        return SectionClassification.from_type_classifications(type_classifications, is_skip=is_skip)

    def _classify_from_content(self, content_text: str) -> SectionClassification:
        """Classify section based on its content when no title is available.

        Collects ALL matching types (no short-circuit) using first N words of content
        as pseudo-title for keyword matching. Falls back to DESCRIPTION, OTHER, or
        UNLABELED based on content presence.

        If content is empty, returns UNLABELED classification with 0.0 confidence.

        Args:
            content_text: Normalized (lowercase) content text

        Returns:
            SectionClassification with all_types sorted by confidence descending

        Example:
            Content-based classification (untitled section):
            >>> result = classifier._classify_from_content("requires 5+ years python")
            >>> result.all_types[0].section_type
            <SectionType.QUALIFICATIONS: 'qualifications'>

            Empty content (no title, no content):
            >>> result = classifier._classify_from_content("")
            >>> result.all_types[0].section_type
            <SectionType.UNLABELED: 'unlabeled'>
            >>> result.all_types[0].confidence
            0.0
        """
        # Initialize container for all matches
        all_matches: dict[SectionType, Tuple[str, ...]] = {}

        # If no content, return early with fallback
        if not content_text:
            fallback_type, fallback_conf = fallback_confidence("content", False)
            type_classifications = [TypeClassification(fallback_type, fallback_conf, ())]
            return SectionClassification.from_type_classifications(type_classifications, is_skip=False)

        # Use first ~50 words as pseudo-title for matching
        first_words = " ".join(content_text.split()[:50])

        # Check all categories (NO EARLY RETURN)
        # SKIP keywords in content prefix
        skip_matches = tuple(kw for kw in self.skip_keywords if kw in first_words)
        if skip_matches:
            all_matches[SectionType.SKIP] = skip_matches

        # SKILLS keywords in content prefix
        skills_matches = tuple(kw for kw in SKILLS_KEYWORDS if kw in first_words)
        if skills_matches:
            all_matches[SectionType.SKILLS] = skills_matches

        # QUALIFICATIONS keywords in content prefix
        qual_matches = tuple(kw for kw in QUALIFICATIONS_KEYWORDS if kw in first_words)
        if qual_matches:
            all_matches[SectionType.QUALIFICATIONS] = qual_matches

        # RESPONSIBILITIES keywords in content prefix
        resp_matches = tuple(kw for kw in RESPONSIBILITIES_KEYWORDS if kw in first_words)
        if resp_matches:
            all_matches[SectionType.RESPONSIBILITIES] = resp_matches

        # KNOWLEDGE keywords in content prefix
        know_matches = tuple(kw for kw in KNOWLEDGE_KEYWORDS if kw in first_words)
        if know_matches:
            all_matches[SectionType.KNOWLEDGE] = know_matches

        # DESCRIPTION keywords in content prefix
        desc_matches = tuple(kw for kw in DESCRIPTION_KEYWORDS if kw in first_words)
        if desc_matches:
            all_matches[SectionType.DESCRIPTION] = desc_matches

        # Build TypeClassification for each matched type
        result_classifications: List[TypeClassification] = []
        for section_type, matched_kws in all_matches.items():
            confidence = calculate_confidence(match_count=len(matched_kws), source="content", section_type=section_type)
            tc = TypeClassification(section_type=section_type, confidence=confidence, matched_keywords=matched_kws)
            result_classifications.append(tc)

        # Handle zero-match case: use fallback
        if not result_classifications:
            fallback_type, fallback_conf = fallback_confidence("content", bool(content_text.strip()))
            result_classifications.append(TypeClassification(fallback_type, fallback_conf, ()))

        # Compute is_skip: True if SKIP is in matched types
        is_skip = SectionType.SKIP in {tc.section_type for tc in result_classifications}

        # Build and return via factory
        return SectionClassification.from_type_classifications(result_classifications, is_skip=is_skip)


# ============================================================================
# Phase 5: Module-Level Convenience Function
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
        >>> result.all_types[0].section_type
        <SectionType.QUALIFICATIONS: 'qualifications'>
    """
    if section is None:
        raise ValueError("section cannot be None")

    if classifier is None:
        classifier = SectionClassifier()

    return classifier.classify(section)
