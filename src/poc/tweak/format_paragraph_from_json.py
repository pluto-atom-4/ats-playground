import argparse
import json
import os
import re
import tempfile

from bs4 import BeautifulSoup
from markitdown import MarkItDown


def clean_and_convert(html_input):
    # --- 1. Pre-process HTML ---
    soup = BeautifulSoup(html_input, "html.parser")

    # Replace non-breaking spaces
    for text_node in soup.find_all(string=True):
        text_node.replace_with(text_node.replace("\xa0", " "))

    # --- 2. Convert to Markdown ---
    md_converter = MarkItDown()
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", encoding="utf-8", delete=False) as tf:
        tf.write(str(soup))
        temp_path = tf.name

    try:
        result = md_converter.convert(temp_path)
        md = result.text_content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # --- 3. The "Clean Rendering" Polisher ---

    # Step A: Standardize line endings and strip trailing/leading whitespace from every line
    # This prevents hidden spaces from breaking the regex patterns.
    lines = [line.strip() for line in md.splitlines()]
    md = "\n".join(lines)

    # Step B: Tighten Lists
    # Look for a line starting with a bullet (*), followed by a blank line,
    # and then another bullet. Remove the blank line.
    # We repeat this to catch multiple items.
    md = re.sub(r"(\n\* .+?)\n\n(?=\* )", r"\1\n", md)

    # Step C: Header Formatting
    # Ensure bold text on its own line (headers) has exactly one blank line above and below.
    # Pattern: Look for bold tags that make up a whole line.
    md = re.sub(r"(?<=.)\n(\*\*.*?\*\*)", r"\n\n\1", md)  # Space before
    md = re.sub(r"(\*\*.*?\*\*)\n(?=.)", r"\1\n\n", md)  # Space after

    # Step D: List Block Separation
    # Ensure a blank line before the first item of a list if there isn't one.
    # Only add blank line if preceding line is NOT already a list item.
    # Pattern: line starting with non-* char, ending with non-whitespace, followed by list item
    md = re.sub(r"(^[^*\n][^\n]*[^\n\s])\n(\* )", r"\1\n\n\2", md, flags=re.MULTILINE)

    # Ensure a blank line after the last item of a list.
    md = re.sub(r"(\n\* [^\n]+)\n([^\n\*])", r"\1\n\n\2", md)

    # Step E: Global Cleanup
    # Collapse any accidentally created triple newlines into double newlines.
    md = re.sub(r"\n{3,}", "\n\n", md)

    return md.strip()


def main():
    parser = argparse.ArgumentParser(description="HTML to Markdown with Clean Tight-List Rendering.")
    parser.add_argument("input", help="Path to JSON file")
    parser.add_argument("-o", "--output", help="Output file path")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found.")
        return

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    html_content = data.get("description", "")
    markdown_result = clean_and_convert(html_content)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown_result)
        print(f"Success! Saved to {args.output}")
    else:
        print(markdown_result)


if __name__ == "__main__":
    main()
