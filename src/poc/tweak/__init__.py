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
"""
