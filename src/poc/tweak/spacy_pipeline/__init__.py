"""spaCy pipeline components for HTML→Markdown conversion.

Provides composable, chainable components for HTML processing:
1. HTMLPreprocessor: Clean HTML, normalize structure, remove non-breaking spaces
2. HTMLMarkdownConverter: Convert HTML to Markdown using MarkItDown
3. MarkdownPolisher: Apply formatting rules for polished output

All components inherit from PipelineComponent abstract base and follow the same interface:
- process(text: str) -> str: Transform text through the component
- name property: Component identifier for logging and registration
- __call__() operator: Functional calling syntax (alias for process)

Components are composable and can be chained independently or via spaCy factory pattern.

Quick Start - Direct Instantiation:
    >>> from src.poc.tweak.spacy_pipeline import HTMLPreprocessor, HTMLMarkdownConverter, MarkdownPolisher
    >>>
    >>> preprocessor = HTMLPreprocessor()
    >>> converter = HTMLMarkdownConverter()
    >>> polisher = MarkdownPolisher()
    >>>
    >>> raw_html = "<div><p>Hello <strong>World</strong></p></div>"
    >>> markdown = polisher.process(converter.process(preprocessor.process(raw_html)))
    >>> print(markdown)
    # Output: "Hello **World**\n"

Chaining Example:
    >>> # Process through pipeline with chaining
    >>> result = (polisher(converter(preprocessor(raw_html))))

Quick Start - spaCy Factory Pattern:
    >>> import spacy
    >>> from src.poc.tweak.spacy_pipeline import registry  # Trigger factory registration
    >>>
    >>> nlp = spacy.load("en_core_web_md")
    >>>
    >>> # Create components via spaCy factory
    >>> preprocessor = nlp.create_pipe("html_preprocessor")
    >>> converter = nlp.create_pipe("html_markdown_converter")
    >>> polisher = nlp.create_pipe("markdown_polisher")
    >>>
    >>> # Process
    >>> markdown = polisher.process(converter.process(preprocessor.process(raw_html)))

Advanced - Custom Configuration:
    >>> # Use graceful error handling for converter
    >>> converter = HTMLMarkdownConverter(fallback_mode="html")
    >>>
    >>> # Use selective rules for polisher (only normalize lines + cleanup)
    >>> polisher = MarkdownPolisher(rules=['line_norm', 'cleanup'])
    >>>
    >>> markdown = polisher.process(converter.process(preprocessor.process(raw_html)))

Component Descriptions:

HTMLPreprocessor:
    Cleans raw HTML and normalizes structure for downstream conversion.
    - Removes non-breaking spaces (\\xa0 → space)
    - Normalizes HTML structure via BeautifulSoup
    - Prepares for MarkItDown conversion

    Example:
        >>> preprocessor = HTMLPreprocessor()
        >>> html = "<div>Text\\xa0with\\xa0nbsp</div>"
        >>> clean_html = preprocessor.process(html)
        >>> print(clean_html)  # Non-breaking spaces removed

HTMLMarkdownConverter:
    Converts HTML to Markdown using MarkItDown with robust error handling.
    - Converts HTML to Markdown via MarkItDown library
    - Manages temp files robustly (write → convert → cleanup)
    - Supports fallback modes: "html" (graceful) or "raise" (fail-fast)
    - Always cleans up temp files, even on exception

    Example:
        >>> converter = HTMLMarkdownConverter()
        >>> html = "<div><p>Hello <strong>World</strong></p></div>"
        >>> markdown = converter.process(html)
        >>> print(markdown)  # "Hello **World**\\n"

MarkdownPolisher:
    Applies formatting rules to Markdown for clean, consistent output.
    - Applies 5 rules in strict order:
      1. line_norm: Strip trailing/leading whitespace from each line
      2. list_tight: Remove blank lines between consecutive bullets
      3. header_format: Ensure blank lines before/after bold headers
      4. list_block: Ensure blank lines before/after list blocks
      5. cleanup: Collapse 3+ newlines to 2
    - Supports selective rule disabling
    - Pre-compiles regex patterns for performance

    Example:
        >>> polisher = MarkdownPolisher()
        >>> markdown = "Line 1  \\n\\n* Item 1\\n\\n* Item 2\\n\\n\\n"
        >>> polished = polisher.process(markdown)
        >>> print(polished)  # Formatted with proper spacing

Usage Patterns:

1. Pipeline class (recommended for repeated use):
    >>> class HTMLToMarkdownPipeline:
    ...     def __init__(self, polisher_rules=None):
    ...         self.preprocessor = HTMLPreprocessor()
    ...         self.converter = HTMLMarkdownConverter()
    ...         self.polisher = MarkdownPolisher(rules=polisher_rules)
    ...
    ...     def process(self, html):
    ...         stage1 = self.preprocessor.process(html)
    ...         stage2 = self.converter.process(stage1)
    ...         return self.polisher.process(stage2)
    >>>
    >>> pipeline = HTMLToMarkdownPipeline()
    >>> result = pipeline.process(raw_html)

2. Functional chaining (for one-off use):
    >>> from functools import reduce
    >>> components = [HTMLPreprocessor(), HTMLMarkdownConverter(), MarkdownPolisher()]
    >>> result = reduce(lambda text, comp: comp.process(text), components, raw_html)

Performance Notes:
- HTMLPreprocessor: <1ms (string manipulation)
- HTMLMarkdownConverter: ~50ms (MarkItDown I/O)
- MarkdownPolisher: <1ms (pre-compiled regex)
- Total: ~50ms per document

See docs/spacy_pipeline.md for comprehensive documentation, configuration options,
troubleshooting, and advanced integration patterns.

Module Contents:
- PipelineComponent: Abstract base class for all components
- HTMLPreprocessor: Stage 1 - HTML cleanup
- HTMLMarkdownConverter: Stage 2 - HTML to Markdown conversion
- MarkdownPolisher: Stage 3 - Markdown formatting
- registry: spaCy factory registrations
"""

# Import components for public API
# Import registry module to trigger @Language.factory() decorators
# This must happen on module import so factories are registered
from . import registry  # noqa: F401
from .base import PipelineComponent
from .html_markdown_converter import HTMLMarkdownConverter
from .html_preprocessor import HTMLPreprocessor
from .markdown_polisher import MarkdownPolisher

__all__ = [
    "PipelineComponent",
    "HTMLPreprocessor",
    "HTMLMarkdownConverter",
    "MarkdownPolisher",
    "registry",
]
