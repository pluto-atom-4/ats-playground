"""Abstract base class for spaCy pipeline components.

Defines the interface for HTML→Markdown pipeline modules that transform text
in a composable, chainable fashion.

This module provides PipelineComponent, an abstract base class that all HTML
processing components (HTMLPreprocessor, HTMLMarkdownConverter, MarkdownPolisher)
must implement. The standard interface ensures components can be easily combined
in any order and integrated with spaCy's factory pattern.

Example:
    >>> from src.poc.tweak.spacy_pipeline import PipelineComponent
    >>> # Subclasses implement process() and name properties
    >>> class MyComponent(PipelineComponent):
    ...     def process(self, text: str) -> str:
    ...         return text.upper()
    ...
    ...     @property
    ...     def name(self) -> str:
    ...         return "my_component"
    >>>
    >>> component = MyComponent()
    >>> result = component.process("hello")  # "HELLO"
    >>> result = component("hello")          # Also works via __call__
"""

from abc import ABC, abstractmethod


class PipelineComponent(ABC):
    """Abstract base for HTML→Markdown pipeline components.

    Each component transforms text (string in, string out) independently.
    Components are composable and can be chained together.

    All pipeline components implement this interface:
    - process(text): Transform input text and return output
    - name property: Component identifier for logging/registration
    - __call__(): Functional calling support (alias for process)

    This allows components to be used interchangeably:
    >>> preprocessor = HTMLPreprocessor()
    >>> result1 = preprocessor.process(html)
    >>> result2 = preprocessor(html)  # Both work the same way

    Components can be chained in any order:
    >>> from functools import reduce
    >>> components = [preprocessor, converter, polisher]
    >>> result = reduce(lambda text, comp: comp(text), components, html)

    For spaCy integration, components are registered via @Language.factory()
    decorators in the registry module:
    >>> import spacy
    >>> nlp = spacy.load("en_core_web_md")
    >>> component = nlp.create_pipe("html_preprocessor")
    >>> result = component.process(text)
    """

    @abstractmethod
    def process(self, text: str) -> str:
        """Process text and return transformed result.

        This is the main transformation method that each component implements.
        The method must be pure (no side effects) and idempotent where possible.

        Args:
            text: Input text (HTML or Markdown string). Can be empty string.

        Returns:
            Transformed text (string). Return type is always string,
            even if the content changes substantially (e.g., HTML → Markdown).

        Raises:
            Only if component is configured to fail on error (e.g.,
            HTMLMarkdownConverter with fallback_mode="raise").
            Otherwise, should gracefully handle errors and return input or
            modified text.

        Examples:
            >>> preprocessor = HTMLPreprocessor()
            >>> preprocessor.process("<div>text</div>")
            '<div>text</div>'

            >>> converter = HTMLMarkdownConverter()
            >>> converter.process("<div><p>Hello</p></div>")
            'Hello\\n'

            >>> polisher = MarkdownPolisher()
            >>> polisher.process("text\\n\\n\\nmore")
            'text\\n\\nmore'
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Component name for logging and registration.

        Returns the component's identifier string. This name is used for:
        - Logging and debugging output
        - spaCy component registration (@Language.factory("name"))
        - Component identification in pipelines

        Returns:
            String identifier (e.g., 'html_preprocessor', 'markdown_polisher').
            Names should be lowercase with underscores (snake_case).

        Examples:
            >>> preprocessor = HTMLPreprocessor()
            >>> preprocessor.name
            'html_preprocessor'

            >>> converter = HTMLMarkdownConverter()
            >>> converter.name
            'html_markdown_converter'

            >>> polisher = MarkdownPolisher()
            >>> polisher.name
            'markdown_polisher'
        """
        pass

    def __call__(self, text: str) -> str:
        """Alias for process() to support functional calling.

        Allows components to be called like functions:
        >>> component = HTMLPreprocessor()
        >>> result1 = component.process(text)
        >>> result2 = component(text)  # Same as above
        >>> # Both are equivalent

        This enables elegant functional composition:
        >>> result = polisher(converter(preprocessor(html)))

        Args:
            text: Input text (HTML or Markdown string)

        Returns:
            Transformed text (string)

        Note:
            This is a convenience method that delegates to process().
            All error handling is delegated to process().

        Examples:
            >>> from src.poc.tweak.spacy_pipeline import HTMLPreprocessor
            >>> preprocessor = HTMLPreprocessor()
            >>> html = "<div>text</div>"
            >>> result = preprocessor(html)  # Uses __call__()
        """
        return self.process(text)
