"""Tests for `_build_preprocess_clean_text` (Issue #228).

Regression check that preprocess now runs HTML->Markdown normalization
(including synthesized section headers) as its first step, since crawl no
longer performs that transform.
"""

from src.cli import _build_preprocess_clean_text


class TestBuildPreprocessCleanText:
    def test_html_description_normalized_to_markdown(self):
        """A raw HTML description is converted to markdown, not left as HTML."""
        job = {
            "title": "Senior Python Developer",
            "location": "Remote",
            "description": "<h2>About the Role</h2><p>We build great software.</p>",
        }
        clean_text = _build_preprocess_clean_text(job)

        assert "Senior Python Developer" in clean_text
        assert "Remote" in clean_text
        assert "<h2>" not in clean_text
        assert "About the Role" in clean_text

    def test_keyword_only_section_gets_synthesized_header(self):
        """A bold-only 'Qualifications' line (no real <h2>) becomes '## Qualifications',
        matching the header-synthesis behavior the crawler used to run inline.
        """
        job = {
            "title": "Data Engineer",
            "description": "<p><strong>Qualifications</strong></p><ul><li>5+ years experience</li></ul>",
        }
        clean_text = _build_preprocess_clean_text(job)

        assert "## Qualifications" in clean_text

    def test_missing_description_omits_description_section(self):
        """No description field -> clean_text is just title (+ location if present)."""
        job = {"title": "Data Engineer", "location": "NYC"}
        clean_text = _build_preprocess_clean_text(job)

        assert clean_text == "Data Engineer\nNYC"
