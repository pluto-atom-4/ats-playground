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

Issue #230: Unified HTML cleaning pipeline (clean_html) combining MarkItDown,
section header synthesis, boilerplate removal, and entity normalization.
"""

import logging
import os
import re
import tempfile
from typing import List, Optional, Set

from markitdown import MarkItDown

from src.parsers import _boilerplate_patterns

logger = logging.getLogger(__name__)


def html_to_markdown(html: str) -> str:
    """
    Convert an HTML string to clean text using a 3-tier fallback chain.

    Attempts conversion in this order:
    1. MarkItDown (primary) - preserves structure, handles rich content
    2. BeautifulSoup + lxml (fallback) - basic text extraction
    3. Original HTML (safe fallback) - never returns empty/None

    MarkItDown requires a file path, so ``html`` is written to a temporary
    ``.html`` file (UTF-8) before conversion. On any failure (I/O error,
    MarkItDown exception, etc.), falls back to BeautifulSoup. If both fail,
    returns the original ``html`` unchanged so callers always get a usable string.

    Args:
        html: Raw HTML string to convert.

    Returns:
        Clean text from MarkItDown/BeautifulSoup, or the original ``html`` on complete failure.
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
        logger.warning(f"html_to_markdown MarkItDown failed: {e}, trying BeautifulSoup fallback")
        try:
            return _html_to_markdown_via_beautifulsoup(html)
        except Exception as bs_error:
            logger.error(f"BeautifulSoup fallback also failed: {bs_error}, returning original HTML")
            return html
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def _html_to_markdown_via_beautifulsoup(html: str) -> str:
    """Convert HTML to text using BeautifulSoup + lxml (fallback).

    Used when MarkItDown is unavailable or fails. Returns normalized text
    suitable for downstream tokenization and chunking.

    Args:
        html: Raw HTML string to convert

    Returns:
        Cleaned text with script/style tags removed

    Raises:
        ImportError: If BeautifulSoup not available
        Exception: If BeautifulSoup parsing fails
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("BeautifulSoup not available for fallback")
        raise

    soup = BeautifulSoup(html, "lxml")

    # Remove script and style tags
    for script in soup(["script", "style"]):
        script.decompose()

    # Extract text
    text = soup.get_text()
    return _postprocess_markdown_text(text)


def _postprocess_markdown_text(text: str) -> str:
    """Normalize BeautifulSoup output to readable text.

    Collapse whitespace, remove extra newlines, normalize spacing.

    Args:
        text: Raw text from BeautifulSoup

    Returns:
        Cleaned and normalized text
    """
    # Strip and collapse lines
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)

    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


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


def clean_html(
    html: str | None,
    include_section_headers: bool = True,
    skip_boilerplate_categories: Optional[Set[str]] = None,
) -> str:
    """
    Unified HTML cleaning pipeline (Issue #230).

    Converts raw HTML to clean, readable text through a 6-step pipeline:
    1. ``html_to_markdown()`` – MarkItDown + BeautifulSoup fallback
    2. ``add_markdown_section_headers()`` – Synthesize missing headers (if enabled)
    3. ``_insert_section_dividers()`` – Add dividers before headers
    4. ``remove_boilerplate_fast()`` – Remove legal, section, company, salary, etc.
    5. ``remove_html_entities()`` – Normalize &nbsp;, &amp;, &#\\d+;, etc.
    6. ``_normalize_whitespace()`` – Collapse multi-space/newline to single

    Args:
        html: Raw HTML string to clean
        include_section_headers: If True, synthesize missing "##"/"###" headers
            from keyword/bold/colon-terminated lines (default: True)
        skip_boilerplate_categories: Optional set of category names to skip
            (e.g., {"section_headers", "time_references"}). Supported categories:
            "legal_compliance", "section_headers", "company_boilerplate",
            "time_references", "salary_benefits", "special_formatting", "navigation"

    Returns:
        Clean text content with boilerplate removed and entities normalized

    Examples:
        >>> html = '<h1>Senior Dev</h1><p>Equal Opportunity Employer.</p>'
        >>> clean_html(html)
        '# Senior Dev\\nSenior Dev'

        >>> html = '<p>Salary: $100K</p>'
        >>> clean_html(html, skip_boilerplate_categories={"salary_benefits"})
        'Salary: $100K'

        >>> html = ''  # Empty input
        >>> clean_html(html)
        ''
    """
    if not html or not isinstance(html, str):
        return ""

    # Step 1: Convert HTML to Markdown (MarkItDown + BeautifulSoup fallback)
    markdown = html_to_markdown(html)
    if not markdown:
        return ""

    # Step 2: Synthesize section headers (if enabled)
    if include_section_headers:
        markdown = add_markdown_section_headers(markdown)

    # Step 3: Insert section dividers (part of header synthesis)
    # (Already included in add_markdown_section_headers)

    # Step 4: Remove boilerplate using pre-compiled patterns
    cleaned = _boilerplate_patterns.remove_boilerplate_fast(markdown, skip_categories=skip_boilerplate_categories)

    # Step 5: Remove HTML entities
    cleaned = _boilerplate_patterns.remove_html_entities(cleaned)

    # Step 6: Normalize whitespace
    cleaned = _boilerplate_patterns._normalize_whitespace(cleaned)

    logger.debug(
        f"clean_html: {len(html)} chars → {len(cleaned)} chars "
        f"(reduction: {(len(html) - len(cleaned)) / len(html) * 100:.1f}%)"
    )

    return cleaned
