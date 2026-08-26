"""POC package for HTML-to-Markdown tweaking and formatting.

This package provides utilities for refining HTML-to-Markdown conversions,
with a focus on paragraph formatting, JSON-based transformation, and
multi-line content handling.

Modules
-------
format_paragraph : Paragraph formatting utilities
    Provides tools for cleaning, normalizing, and formatting individual paragraphs
    during the HTML-to-Markdown conversion process.

format_paragraph_from_json : JSON-driven paragraph formatting
    Transforms JSON input structures into formatted Markdown output, enabling
    declarative specification of paragraph transformations.

multi_line_paragraph : Multi-line paragraph handling
    Utilities for managing paragraphs that span multiple lines, including
    boundary detection, line joining, and preserving semantic structure.

    Key exports:
    - MarkdownSpanRuler: Parse markdown into structured sections with metadata
    - MarkdownSection: Dataclass representing a markdown section

markdown_section_classifier : Markdown section classification
    Classifies markdown sections into semantic types (SKILLS, QUALIFICATIONS,
    RESPONSIBILITIES, KNOWLEDGE, DESCRIPTION, SKIP, OTHER, UNLABELED) using
    keyword matching and confidence scoring. Supports multi-type classification
    with atomic and compound requirement spans.

    Key exports:
    - SectionType: Enum of section types
    - SectionClassification: Result of classifying a markdown section with multi-type support
    - TypeClassification: Individual type classification result with confidence and keyword matches
    - KeywordMatch: Information about a matched keyword in classification
    - SectionClassifier: Main classifier with keyword-based logic
    - classify_section: Module-level convenience wrapper
    - calculate_confidence: Compute confidence score for a classification
    - fallback_confidence: Compute confidence using fallback heuristics when keywords not found
"""

from src.poc.tweak.markdown_section_classifier import (
    KeywordMatch,
    SectionClassification,
    SectionClassifier,
    SectionType,
    TypeClassification,
    calculate_confidence,
    classify_section,
    fallback_confidence,
)
from src.poc.tweak.multi_line_paragraph import (
    MarkdownSection,
    MarkdownSpanRuler,
    count_words,
    detect_has_list,
    extract_title,
    get_header_level,
)

__all__ = [
    "MarkdownSpanRuler",
    "MarkdownSection",
    "extract_title",
    "get_header_level",
    "count_words",
    "detect_has_list",
    "SectionType",
    "SectionClassification",
    "TypeClassification",
    "KeywordMatch",
    "SectionClassifier",
    "classify_section",
    "calculate_confidence",
    "fallback_confidence",
]
