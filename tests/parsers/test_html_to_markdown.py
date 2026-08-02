"""Tests for src.parsers.html_to_markdown.html_to_markdown."""

import os
from unittest.mock import patch

import src.parsers.html_to_markdown as html_to_markdown_module
from src.parsers.html_cleaner import HTMLCleaner
from src.parsers.html_to_markdown import html_to_markdown


class TestHtmlToMarkdown:
    """Direct tests for the shared HTML -> Markdown converter."""

    def test_utf8_special_chars_preserved(self) -> None:
        """En-dash, em-dash, and curly quotes survive the round trip."""
        html = "<p>Range 2020–2024 — the “best” years</p>"
        result = html_to_markdown(html)

        assert "–" in result  # en-dash
        assert "—" in result  # em-dash
        assert "“" in result and "”" in result  # curly quotes

    def test_basic_heading_conversion(self) -> None:
        """A simple heading + paragraph converts to markdown structure."""
        html = "<h1>Senior Python Developer</h1><p>5+ years required.</p>"
        result = html_to_markdown(html)

        assert result.startswith("#")
        assert "Senior Python Developer" in result
        assert "5+ years required." in result

    def test_empty_input_returns_empty(self) -> None:
        """Empty string input short-circuits to an empty string."""
        assert html_to_markdown("") == ""

    def test_malformed_html_does_not_raise(self) -> None:
        """Unclosed tags / malformed markup should not raise."""
        html = "<div><p>unclosed paragraph and div"
        result = html_to_markdown(html)

        assert isinstance(result, str)
        assert "unclosed paragraph and div" in result

    def test_exception_fallback_returns_original_html(self) -> None:
        """If MarkItDown raises, the original HTML string is returned unchanged."""
        html = "<p>content that should survive on failure</p>"

        with patch.object(html_to_markdown_module, "MarkItDown") as mock_markitdown:
            mock_markitdown.return_value.convert.side_effect = RuntimeError("boom")
            result = html_to_markdown(html)

        assert result == html

    def test_temp_file_cleaned_up_on_success(self) -> None:
        """The temporary file created during conversion is removed afterward."""
        created_paths = []
        real_unlink = os.unlink

        def tracking_unlink(path: str) -> None:
            created_paths.append(path)
            real_unlink(path)

        with patch.object(html_to_markdown_module.os, "unlink", side_effect=tracking_unlink):
            html_to_markdown("<p>hello</p>")

        assert len(created_paths) == 1
        assert not os.path.exists(created_paths[0])

    def test_temp_file_cleaned_up_on_failure(self) -> None:
        """The temporary file is removed even when conversion raises."""
        created_paths = []
        real_unlink = os.unlink

        def tracking_unlink(path: str) -> None:
            created_paths.append(path)
            real_unlink(path)

        with (
            patch.object(html_to_markdown_module, "MarkItDown") as mock_markitdown,
            patch.object(html_to_markdown_module.os, "unlink", side_effect=tracking_unlink),
        ):
            mock_markitdown.return_value.convert.side_effect = RuntimeError("boom")
            html_to_markdown("<p>hello</p>")

        assert len(created_paths) == 1
        assert not os.path.exists(created_paths[0])


class TestHtmlCleanerMarkItDownIntegration:
    """Regression: HTMLCleaner now actually exercises MarkItDown."""

    def test_clean_produces_markdown_style_output(self) -> None:
        """HTMLCleaner().clean() should show markdown structure (leading '#'),
        not BeautifulSoup's flat concatenated text, now that MarkItDown
        is invoked correctly via the shared converter.
        """
        html = "<h1>Job Title</h1><p>Job description body text.</p>"
        cleaner = HTMLCleaner()

        result = cleaner.clean(html)

        assert result.startswith("#")
        assert "Job Title" in result
        assert "Job description body text." in result
