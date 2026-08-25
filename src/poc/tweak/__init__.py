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
    keyword matching and confidence scoring.

    Key exports:
    - SectionType: Enum of section types
    - SectionClassification: Result of classifying a markdown section
    - SectionClassifier: Main classifier with keyword-based logic
    - classify_section: Module-level convenience wrapper
"""

from src.poc.tweak.markdown_section_classifier import (
    SectionClassification,
    SectionClassifier,
    SectionType,
    classify_section,
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
    "SectionClassifier",
    "classify_section",
]
