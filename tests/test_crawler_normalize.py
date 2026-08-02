"""Tests for HTML-to-Markdown description normalization in crawler.

Rewritten for Issue #195 / Phase 8: `_normalize_description` used to run
regex-based metadata-separator logic on raw concatenated text. It is now a
thin wrapper around the shared `html_to_markdown()` utility, since the
crawler extracts `inner_html()` (not `text_content()`) for job descriptions.
These tests assert markdown structure and absence of residual HTML tags,
rather than the old regex label-spacing behavior.
"""

import re

from src.browser.crawler import Crawler


class TestDescriptionNormalization:
    """Test HTML -> Markdown conversion of job descriptions."""

    def test_normalize_heading_and_paragraph(self):
        """Basic heading + paragraph HTML converts to markdown structure."""
        crawler = Crawler()
        html = "<h2>About the Role</h2><p>We build great software.</p>"
        result = crawler._normalize_description(html)

        assert result.startswith("#")
        assert "About the Role" in result
        assert "We build great software." in result

    def test_normalize_list_items(self):
        """Unordered list HTML converts to markdown list syntax."""
        crawler = Crawler()
        html = "<ul><li>Python</li><li>SQL</li><li>Docker</li></ul>"
        result = crawler._normalize_description(html)

        assert "Python" in result
        assert "SQL" in result
        assert "Docker" in result

    def test_normalize_no_residual_html_tags(self):
        """Converted output should not contain raw HTML tags."""
        crawler = Crawler()
        html = (
            "<div><h2>Requirements</h2>"
            "<ul><li>5+ years experience</li><li>Strong communication</li></ul>"
            "<p>Remote type: <strong>Hybrid</strong></p></div>"
        )
        result = crawler._normalize_description(html)

        assert not re.search(r"<[a-zA-Z/][^>]*>", result)
        assert "Requirements" in result
        assert "5+ years experience" in result
        assert "Hybrid" in result

    def test_normalize_workday_style_metadata(self):
        """Structured metadata table converts cleanly without concatenation."""
        crawler = Crawler()
        html = (
            "<table>"
            "<tr><td>remote type</td><td>Hybrid</td></tr>"
            "<tr><td>locations</td><td>Seattle, WA</td></tr>"
            "<tr><td>time type</td><td>Full time</td></tr>"
            "</table>"
        )
        result = crawler._normalize_description(html)

        assert "Hybrid" in result
        assert "Seattle" in result
        assert "Full time" in result

    def test_normalize_empty_description(self):
        """Handle empty string description."""
        crawler = Crawler()
        result = crawler._normalize_description("")
        assert result == ""

    def test_normalize_none_description(self):
        """Handle None description by returning empty string."""
        crawler = Crawler()
        result = crawler._normalize_description(None)
        assert result == ""

    def test_normalize_plain_text_passthrough(self):
        """Plain text with no HTML tags passes through largely unchanged."""
        crawler = Crawler()
        text = "Just a plain sentence with no markup at all."
        result = crawler._normalize_description(text)
        assert "Just a plain sentence with no markup at all." in result

    def test_normalize_malformed_html_does_not_raise(self):
        """Malformed/unclosed HTML should not raise."""
        crawler = Crawler()
        html = "<div><p>Unclosed paragraph and div"
        result = crawler._normalize_description(html)
        assert isinstance(result, str)
        assert "Unclosed paragraph and div" in result


class TestMarkdownSectionHeaderSynthesis:
    """Test synthesis of ## / ### section headers from keyword/bold/colon lines.

    Issue #196: when the source HTML lacks real <h2>/<h3> tags but uses
    bold-label or plain-colon conventions to signal section boundaries,
    `_normalize_description` now synthesizes Markdown headers so downstream
    section-aware preprocessing can recognize them.
    """

    def test_bold_qualifications_line_becomes_h2(self):
        """A bold-only 'Qualifications' line (no real <h2>) becomes '## Qualifications'."""
        crawler = Crawler()
        html = (
            "<p><strong>Qualifications</strong></p>"
            "<ul><li>5+ years experience</li><li>Bachelor's degree</li></ul>"
        )
        result = crawler._normalize_description(html)
        assert "## Qualifications" in result

    def test_plain_requirements_colon_paragraph_becomes_h2(self):
        """A plain 'Requirements:' paragraph (no real heading) becomes '## Requirements'."""
        crawler = Crawler()
        html = "<p>Requirements:</p><ul><li>Python</li><li>SQL</li></ul>"
        result = crawler._normalize_description(html)
        assert "## Requirements" in result

    def test_bold_subsection_followed_by_list_becomes_h3(self):
        """A bold standalone line followed by a bullet list becomes a '### Subsection'."""
        crawler = Crawler()
        html = (
            "<p><strong>Team Culture</strong></p>"
            "<ul><li>We value transparency</li><li>We move fast</li></ul>"
        )
        result = crawler._normalize_description(html)
        assert "### Team Culture" in result

    def test_trailing_colon_line_becomes_h3(self):
        """A generic trailing-colon line (e.g. 'Pay Range:') produces a '###' header.

        Note: the source orphan commit had three redundant if/elif/else
        branches here (pay-range/salary, hiring-practice/EOE, generic
        fallback) that all executed the identical transform. This is
        collapsed into a single branch, so we only assert that *a* '###'
        header is produced, not on the removed dead-branch behavior.
        """
        crawler = Crawler()
        html = "<p>Pay Range:</p><p>$100,000 - $150,000</p>"
        result = crawler._normalize_description(html)
        assert re.search(r"^### .+$", result, re.MULTILINE)

    def test_workday_style_metadata_table_unaffected(self):
        """Table-based metadata (no keyword/colon/bold lines) does not acquire headers.

        Regression guard for `test_normalize_workday_style_metadata`: header
        synthesis must not spuriously introduce '##'/'###' markers into
        structured table content.
        """
        crawler = Crawler()
        html = (
            "<table>"
            "<tr><td>remote type</td><td>Hybrid</td></tr>"
            "<tr><td>locations</td><td>Seattle, WA</td></tr>"
            "<tr><td>time type</td><td>Full time</td></tr>"
            "</table>"
        )
        result = crawler._normalize_description(html)
        assert "Hybrid" in result
        assert "Seattle" in result
        assert "Full time" in result
        assert "##" not in result
