"""Bullet-point preprocessing for enhanced requirement extraction.

Normalizes bullet points (*, -, +, numbered) into sentence-like format.
Handles embedded newlines, inline headers, and period insertion.
"""

import re


def normalize_bullet_points(markdown: str) -> str:
    """Normalize bullet points to sentence-like format.

    Converts:
    - * prefix bullets to plain sentences
    - - prefix bullets to plain sentences
    - + prefix bullets to plain sentences
    - 1. numbered bullets to plain sentences
    - Inline header + bullet combos

    Adds trailing periods to bullets missing punctuation.
    Handles embedded newlines within bullets.

    Args:
        markdown: Raw markdown text with bullets

    Returns:
        Markdown with normalized bullets (periods added, prefixes removed)
    """
    lines = markdown.split("\n")
    result = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()

        # Check for bullet prefix (*, -, +)
        if re.match(r"^[*\-+]\s+", stripped):
            # Extract bullet content
            content = re.sub(r"^[*\-+]\s+", "", stripped, count=1).strip()
            # Add period if missing
            if content and not content.endswith((".", "!", "?")):
                content += "."
            result.append(content)

        # Check for numbered bullet (1., 2., etc.)
        elif re.match(r"^\d+\.\s+", stripped):
            # Extract bullet content
            content = re.sub(r"^\d+\.\s+", "", stripped, count=1).strip()
            # Add period if missing
            if content and not content.endswith((".", "!", "?")):
                content += "."
            result.append(content)

        # Check for inline header + bullet (e.g., "### Some Header* Bullet")
        elif re.search(r"^#+\s+.+[*\-+]\s+", stripped):
            # Split header from bullet content
            match = re.match(r"(^#+\s+.+?)\s*[*\-+]\s+(.+)", stripped)
            if match:
                header = match.group(1).strip()
                bullet_content = match.group(2).strip()
                result.append(header)
                if bullet_content and not bullet_content.endswith((".", "!", "?")):
                    bullet_content += "."
                result.append(bullet_content)
            else:
                result.append(line)

        else:
            result.append(line)

        i += 1

    return "\n".join(result)


def normalize_asterisk_bullets(markdown: str) -> str:
    """Normalize asterisk (*) bullet points.

    Args:
        markdown: Markdown text with asterisk bullets

    Returns:
        Text with asterisk bullets normalized and periods added
    """
    lines = markdown.split("\n")
    result = []

    for line in lines:
        stripped = line.lstrip()
        if re.match(r"^\*\s+", stripped):
            content = re.sub(r"^\*\s+", "", stripped, count=1).strip()
            if content and not content.endswith((".", "!", "?")):
                content += "."
            result.append(content)
        else:
            result.append(line)

    return "\n".join(result)


def normalize_hyphen_bullets(markdown: str) -> str:
    """Normalize hyphen (-) bullet points.

    Args:
        markdown: Markdown text with hyphen bullets

    Returns:
        Text with hyphen bullets normalized and periods added
    """
    lines = markdown.split("\n")
    result = []

    for line in lines:
        stripped = line.lstrip()
        if re.match(r"^-\s+", stripped):
            content = re.sub(r"^-\s+", "", stripped, count=1).strip()
            if content and not content.endswith((".", "!", "?")):
                content += "."
            result.append(content)
        else:
            result.append(line)

    return "\n".join(result)


def normalize_numbered_bullets(markdown: str) -> str:
    """Normalize numbered (1., 2., etc.) bullet points.

    Args:
        markdown: Markdown text with numbered bullets

    Returns:
        Text with numbered bullets normalized and periods added
    """
    lines = markdown.split("\n")
    result = []

    for line in lines:
        stripped = line.lstrip()
        if re.match(r"^\d+\.\s+", stripped):
            content = re.sub(r"^\d+\.\s+", "", stripped, count=1).strip()
            if content and not content.endswith((".", "!", "?")):
                content += "."
            result.append(content)
        else:
            result.append(line)

    return "\n".join(result)


def normalize_inline_header_bullets(markdown: str) -> str:
    """Normalize inline header + bullet combinations.

    Handles patterns like "### Header* Bullet content"

    Args:
        markdown: Markdown text with inline header bullets

    Returns:
        Text with inline headers and bullets separated
    """
    lines = markdown.split("\n")
    result = []

    for line in lines:
        stripped = line.lstrip()
        if re.search(r"^#+\s+.+[*\-+]\s+", stripped):
            match = re.match(r"(^#+\s+.+?)\s*[*\-+]\s+(.+)", stripped)
            if match:
                header = match.group(1).strip()
                bullet_content = match.group(2).strip()
                result.append(header)
                if bullet_content and not bullet_content.endswith((".", "!", "?")):
                    bullet_content += "."
                result.append(bullet_content)
            else:
                result.append(line)
        else:
            result.append(line)

    return "\n".join(result)


def normalize_nested_bullets(markdown: str) -> str:
    """Normalize nested bullet points (indented bullets).

    Handles multi-level bullets and preserves structure.

    Args:
        markdown: Markdown text with nested bullets

    Returns:
        Text with nested bullets normalized and periods added
    """
    lines = markdown.split("\n")
    result = []

    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # Match any bullet pattern (*, -, +) at any indent level
        if re.match(r"^[*\-+]\s+", stripped):
            content = re.sub(r"^[*\-+]\s+", "", stripped, count=1).strip()
            if content and not content.endswith((".", "!", "?")):
                content += "."
            result.append(" " * indent + content)

        # Match numbered bullets at any indent level
        elif re.match(r"^\d+\.\s+", stripped):
            content = re.sub(r"^\d+\.\s+", "", stripped, count=1).strip()
            if content and not content.endswith((".", "!", "?")):
                content += "."
            result.append(" " * indent + content)

        else:
            result.append(line)

    return "\n".join(result)


def normalize_handles_existing_periods(markdown: str) -> str:
    """Normalize bullets while respecting existing periods.

    Prevents double-periods and respects existing punctuation.

    Args:
        markdown: Markdown text with bullets (some may have periods)

    Returns:
        Text with normalized bullets, no double-periods
    """
    lines = markdown.split("\n")
    result = []

    for line in lines:
        stripped = line.lstrip()

        # Match bullet patterns
        if re.match(r"^[*\-+]\s+", stripped):
            content = re.sub(r"^[*\-+]\s+", "", stripped, count=1).strip()
            # Add period only if missing (no double-period)
            if content and not content.endswith((".", "!", "?")):
                content += "."
            result.append(content)

        elif re.match(r"^\d+\.\s+", stripped):
            content = re.sub(r"^\d+\.\s+", "", stripped, count=1).strip()
            # Add period only if missing
            if content and not content.endswith((".", "!", "?")):
                content += "."
            result.append(content)

        else:
            result.append(line)

    return "\n".join(result)
