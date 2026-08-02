"""Shared HTML-to-Markdown conversion utility.

MarkItDown's ``convert()`` treats its argument as a file path (or a stream),
not a literal HTML string. Passing raw HTML directly raises ``FileNotFoundError``.
This module works around that by writing the HTML to a temporary file first,
converting that file, and cleaning up afterward.
"""

import logging
import os
import tempfile

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
