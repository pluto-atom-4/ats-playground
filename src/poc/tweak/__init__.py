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
    with keyword position tracking and atomic/compound requirement spans.

    Key exports:
    - SectionType: Enum of section types
    - SectionClassification: Result of classifying a markdown section with multi-type support
    - TypeClassification: Individual type classification result with confidence and keyword matches
    - KeywordMatch: Information about a matched keyword in classification with position
    - SectionClassifier: Main classifier with keyword-based logic
    - classify_section: Module-level convenience wrapper
    - calculate_confidence: Compute confidence score for a classification
    - fallback_confidence: Compute confidence using fallback heuristics when keywords not found
    - calculate_position: Calculate character position of keyword in source text

common : Shared utilities for crawler modules (Issue #309)
    Provides browser initialization, config loading, selector resolution, and logging setup.
    Used by crawl_list.py and crawl_details.py for independent crawler operation.

    Key exports:
    - init_browser, close_browser: Browser lifecycle management
    - retry_goto: Page navigation with exponential backoff retry
    - load_all_company_configs, resolve_company_selectors: Config management
    - setup_logging: Logging initialization

crawl_list : CLI for extracting job listings (Issue #309)
    Crawls company career pages, extracts job titles/locations/links.
    Writes per-company JSON files to data/work/ directory.
    Run: python -m src.poc.tweak.crawl_list --config-dir config_test --output-dir data/work

crawl_details : CLI for extracting job descriptions (Issue #309)
    Reads selected.json with job listings, fetches detail pages, extracts descriptions.
    Handles iframe vs direct-DOM extraction, writes enriched JSON to output file.
    Run: python -m src.poc.tweak.crawl_details --input data/work/selected.json --output data/work/details.json
"""

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
    "calculate_position",
]
