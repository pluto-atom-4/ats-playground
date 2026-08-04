"""Shared HTML-to-Markdown conversion utility.

MarkItDown's ``convert()`` treats its argument as a file path (or a stream),
not a literal HTML string. Passing raw HTML directly raises ``FileNotFoundError``.
This module works around that by writing the HTML to a temporary file first,
converting that file, and cleaning up afterward.

Also owns the section-header synthesis pass (``normalize_description`` /
``add_markdown_section_headers``) formerly on ``Crawler`` (see Issue #228):
when the source HTML lacked real heading tags, keyword/bold/colon-terminated
standalone lines are promoted to "## "/"### " headers so downstream chunking
and NER section-routing (``src/tokenization/preprocessor.py``) have structure
to work with.
"""

import logging
import os
import re
import tempfile
from typing import List, Optional

from markitdown import MarkItDown

logger = logging.getLogger(__name__)


def html_to_markdown(html: str) -> str:
    """
    Convert an HTML string to Markdown using MarkItDown.

    MarkItDown requires a file path, so ``html`` is written to a temporary
    ``.html`` file (UTF-8) before conversion. On any failure (I/O error,
    MarkItDown exception, etc.), the original ``html`` is returned unchanged
    so callers always get a usable string.

    Args:
        html: Raw HTML string to convert.

    Returns:
        Markdown-formatted string, or the original ``html`` on failure.
    """
    if not html:
        return html

    tmp_path: str = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".html",
            encoding="utf-8",
            delete=False,
        ) as tmp_file:
            tmp_file.write(html)
            tmp_path = tmp_file.name

        result = MarkItDown().convert(tmp_path)
        markdown: str = result.markdown
        return markdown
    except Exception as e:
        logger.warning(f"html_to_markdown failed: {e}, returning original HTML")
        return html
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# Standalone lines matching these phrases (case-insensitive, after
# stripping bold markers / trailing colon) are synthesized into
# "## " section headers when the source HTML lacks real heading tags.
_SECTION_HEADER_KEYWORDS = frozenset(
    {
        # qualifications
        "qualifications",
        "desired qualifications",
        "preferred qualifications",
        "minimum qualifications",
        "essential qualifications",
        # requirements
        "requirements",
        "must-have",
        "must haves",
        "must-haves",
        "nice-to-have",
        "nice-to-haves",
        "nice to have",
        "nice to haves",
        "needed",
        # skills
        "skills",
        "technical skills",
        "core skills",
        "competencies",
        # knowledge
        "knowledge",
        "understanding",
        # responsibilities
        "responsibilities",
        "what you'll do",
        "duties",
        "accountabilities",
        # experience
        "experience",
        "background",
        # education
        "education",
        # benefits / compensation
        "benefits",
        "compensation",
        # about-the-role variants
        "about the role",
        "about this role",
        "what we're looking for",
    }
)


def _extract_bold_label(text: str) -> Optional[str]:
    """Return the inner text of a bold-only standalone line, or None.

    Matches Markdown bold (``**label**``) and MarkItDown-escaped bold
    (``\\*\\*label\\*\\*``) wrapping the entire line.
    """
    match = re.match(r"^\\\*\\\*(.+?)\\\*\\\*$", text)
    if match:
        return match.group(1).strip()
    match = re.match(r"^\*\*(.+?)\*\*$", text)
    if match:
        return match.group(1).strip()
    return None


def _extract_standalone_label(text: str) -> Optional[str]:
    """Return the label of a standalone plain/bold line, or None.

    Excludes list items, headers, and table rows so only genuine
    heading-like lines are considered.
    """
    bold_label = _extract_bold_label(text)
    if bold_label is not None:
        return bold_label
    if text.startswith(("#", "-", "*", "+", ">", "|")) or re.match(r"^\d+\.\s", text):
        return None
    return text


def _synthesize_keyword_headers(lines: List[str]) -> None:
    """Step 1: standalone lines matching a known section keyword -> '## Header'.

    Mutates ``lines`` in place.
    """
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        label = _extract_standalone_label(stripped)
        if label is None:
            continue
        normalized = label.rstrip(":").strip()
        if normalized.replace("’", "'").lower() in _SECTION_HEADER_KEYWORDS:
            lines[i] = f"## {normalized}"


def _synthesize_bold_subsection_headers(lines: List[str]) -> None:
    """Step 2: bold-only line followed by non-empty, non-header content -> '### Subsection'.

    Mutates ``lines`` in place.
    """
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        label = _extract_bold_label(stripped)
        if label is None:
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j >= len(lines):
            continue
        next_stripped = lines[j].strip()
        if next_stripped and not next_stripped.startswith("#"):
            lines[i] = f"### {label.rstrip(':').strip()}"


def _synthesize_colon_subsection_headers(lines: List[str]) -> None:
    """Step 3: any remaining non-header line ending in ':' -> '### Subsection'.

    Mutates ``lines`` in place.
    """
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or not stripped.endswith(":"):
            continue
        label = stripped[:-1].strip()
        if not label:
            continue
        lines[i] = f"### {label}"


def _insert_section_dividers(lines: List[str]) -> List[str]:
    """Step 4: insert a blank line + '---' immediately before every
    synthesized header.

    Skips insertion if the header is the very first line of the
    document (nothing precedes it, so there's nothing to separate) or
    if the immediately preceding emitted line is already '---' or
    another header, to avoid doubled/redundant dividers on consecutive
    headers. Returns a new list (unlike the mutate-in-place synthesis
    passes) since insertion changes list length.
    """
    header_re = re.compile(r"^#{2,3}\s")
    result: List[str] = []
    for line in lines:
        if header_re.match(line) and result:
            prev_line = result[-1].strip()
            if prev_line != "---" and not header_re.match(prev_line):
                result.append("")
                result.append("---")
        result.append(line)
    return result


def add_markdown_section_headers(markdown: str) -> str:
    """
    Synthesize "## "/"### " section headers from keyword, bold, and
    colon-terminated standalone lines when the source HTML lacked real
    heading tags.

    Runs four passes in sequence:
    1. Standalone lines matching a known section keyword (plain, bold,
       or MarkItDown-escaped bold, with an optional trailing colon)
       become "## <Header>".
    2. Remaining bold-only standalone lines followed by non-empty,
       non-header content become "### <Subsection>".
    3. Remaining non-header lines ending in ":" become
       "### <Subsection>".
    4. A blank line + "---" divider is inserted immediately before
       every "##"/"###" header produced above (skipped when the header
       is the first line of the document, or immediately follows
       another header/divider), activating the preprocessor's
       divider-aware section splitting.
    """
    lines = markdown.split("\n")
    _synthesize_keyword_headers(lines)
    _synthesize_bold_subsection_headers(lines)
    _synthesize_colon_subsection_headers(lines)
    lines = _insert_section_dividers(lines)
    return "\n".join(lines)


def normalize_description(description: str) -> str:
    """
    Normalize a job description by converting HTML to Markdown and
    synthesizing section headers.

    Uses ``html_to_markdown()`` so that structural formatting (headings,
    lists, etc.) is preserved instead of collapsing into a flat, ambiguous
    run of text, then runs ``add_markdown_section_headers()`` to promote
    keyword/bold/colon-terminated standalone lines into real headers when
    the source HTML lacked heading tags.
    """
    if not description:
        return ""
    markdown = html_to_markdown(description)
    return add_markdown_section_headers(markdown) if markdown else markdown
