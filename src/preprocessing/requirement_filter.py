"""Rule-based requirement extraction component for spaCy pipeline.

Implements trigger-word detection with regex patterns to extract job requirements
from prose text. Adds Doc._.requirements custom attribute with structured metadata.
"""

import bisect
import re
from typing import Any, Dict, List

from spacy.language import Language
from spacy.tokens import Doc

# Pattern definitions from Issue #248, organized by confidence tier
# Note: Patterns use [\w\s\-] to match word chars, spaces, and hyphens
# Case-insensitive matching via re.IGNORECASE flag
TIER_1_PATTERNS: List[Dict[str, Any]] = [
    {
        "trigger_word": "required",
        "regex": r"(required[\w\s\-]*)",
        "confidence": 0.95,
    },
    {
        "trigger_word": "must",
        "regex": r"(must\s+(?:have\s+)?[\w\s\-]+)",
        "confidence": 0.93,
    },
    {
        "trigger_word": "essential",
        "regex": r"(essential[\w\s\-]*)",
        "confidence": 0.90,
    },
    {
        "trigger_word": "ability to",
        "regex": r"(ability\s+to\s+[\w\s\-]+)",
        "confidence": 0.92,
    },
    {
        "trigger_word": "experience in",
        "regex": r"((?:experience|background)\s+(?:with|in)\s+[\w\s\-\.]+)",
        "confidence": 0.88,
    },
    {
        "trigger_word": "proficiency",
        "regex": r"(proficiency\s+(?:in|with)?\s+[\w\s\-\.]+)",
        "confidence": 0.91,
    },
    {
        "trigger_word": "knowledge of",
        "regex": r"(knowledge\s+of\s+[\w\s\-\.]+)",
        "confidence": 0.85,
    },
    {
        "trigger_word": "understanding of",
        "regex": r"(understanding\s+of\s+[\w\s\-\.]+)",
        "confidence": 0.83,
    },
]

TIER_2_PATTERNS: List[Dict[str, Any]] = [
    {
        "trigger_word": "should",
        "regex": r"(should\s+(?:have\s+)?[\w\s\-]+)",
        "confidence": 0.70,
    },
    {
        "trigger_word": "prefer",
        "regex": r"((?:preferred|prefer)[\w\s\-:]*)",
        "confidence": 0.65,
    },
    {
        "trigger_word": "degree",
        "regex": r"((?:bachelor's?|master's?|phd)\s+(?:degree\s*)?(?:in|of)?\s*[\w\s\-]*)",
        "confidence": 0.89,
    },
    {
        "trigger_word": "years of",
        "regex": r"([\d\+]+\s+years?\s+(?:of|in)\s+[\w\s\-]+)",
        "confidence": 0.80,
    },
]

TIER_3_PATTERNS: List[Dict[str, Any]] = [
    {
        "trigger_word": "nice to have",
        "regex": r"(nice\s+to\s+have\s+[\w\s\-]+)",
        "confidence": 0.40,
    },
    {
        "trigger_word": "ideal",
        "regex": r"(ideal[\w\s\-]*)",
        "confidence": 0.55,
    },
    {
        "trigger_word": "bonus",
        "regex": r"(bonus[\w\s\-:]*)",
        "confidence": 0.45,
    },
]

ALL_PATTERNS: List[Dict[str, Any]] = TIER_1_PATTERNS + TIER_2_PATTERNS + TIER_3_PATTERNS


def _build_sentence_char_ranges(doc: Doc) -> List[tuple[int, int]]:
    """Build list of (start_char, end_char) ranges for each sentence.

    Args:
        doc: spaCy Doc object

    Returns:
        List of character boundaries [(sent1_start, sent1_end), ...]
    """
    return [(sent.start_char, sent.end_char) for sent in doc.sents]


def _find_sentence_for_offset(char_offset: int, sent_ranges: List[tuple[int, int]]) -> tuple[int, int] | None:
    """Find sentence (start_char, end_char) containing char_offset using bisect.

    Args:
        char_offset: Character position to find
        sent_ranges: Precomputed sentence boundaries

    Returns:
        (sent_start, sent_end) if found, else None
    """
    # Binary search: find first sentence that ends after char_offset
    idx = bisect.bisect_right(sent_ranges, (char_offset, float("inf")))
    if idx > 0:
        start, end = sent_ranges[idx - 1]
        if start <= char_offset < end:
            return (start, end)
    return None


def _apply_casing_preference(req1: Dict[str, Any], req2: Dict[str, Any]) -> Dict[str, Any]:
    """Prefer requirement with better casing (more capitals) when confidence tied.

    Args:
        req1, req2: Requirement dicts with 'text' field

    Returns:
        Requirement with better casing (or req1 if equal)
    """
    caps1 = sum(1 for c in req1["text"] if c.isupper())
    caps2 = sum(1 for c in req2["text"] if c.isupper())
    return req1 if caps1 >= caps2 else req2


def _token_count(text: str) -> int:
    """Estimate token count using simple whitespace splitting.

    Args:
        text: Text to count tokens for

    Returns:
        Approximate token count
    """
    return len(text.split())


def _apply_confidence_adjustments(
    base_confidence: float,
    text: str,
    full_sentence: str,
) -> float:
    """Apply confidence adjustments based on context.

    Rules:
    - Negation (no/not before trigger): set to 0.0
    - Parenthetical context: -0.10
    - Conditional (if): -0.15
    - "Nice to have" in text: -0.25

    Args:
        base_confidence: Base confidence score from pattern
        text: Matched requirement text
        full_sentence: Full sentence context

    Returns:
        Adjusted confidence score (0.0-1.0)
    """
    adjusted = base_confidence

    # Check for negation patterns (within a local context window, not entire sentence)
    # Use span offsets directly instead of substring search to avoid -1 edge case
    # when text spans sentence boundary. This accesses the original doc text.
    # Note: full_sentence may be shorter than matched text, so use full doc.text offsets.
    # For now, use full_sentence with fallback bounds if not found.
    offset_in_sentence = full_sentence.find(text)
    if offset_in_sentence >= 0:
        text_start = max(0, offset_in_sentence - 50)
        text_end = min(len(full_sentence), offset_in_sentence + len(text) + 50)
        local_context = full_sentence[text_start:text_end]
    else:
        # Text not found in sentence (spans boundary). Use full_sentence as context.
        local_context = full_sentence

    # Pattern 1: Negation before trigger word (e.g., "not required", "no experience")
    negation_before_pattern = (
        r"(?:no|not|don't|doesn't|didn't|without)\s+(?:prior\s+)?"
        r"(?:experience|requirement|required|require|requires|must|essential|ability\s+to|"
        r"proficiency|knowledge|understanding)"
    )
    if re.search(negation_before_pattern, local_context, re.IGNORECASE):
        return 0.0

    # Pattern 2: Negation after trigger word (e.g., "experience is not required")
    # Limited to local context to avoid false positives across unrelated clauses
    negation_after_pattern = (
        r"(?:experience|requirement|required|require|requires|must|essential|ability\s+to|"
        r"proficiency|knowledge|understanding)\b.*?\b(?:not|no|don't|doesn't|didn't|without)\b"
    )
    if re.search(negation_after_pattern, local_context, re.IGNORECASE):
        return 0.0

    # Check for parenthetical context
    if "(" in text or ")" in text:
        adjusted -= 0.10

    # Check for conditional context
    if re.search(r"\bif\b", full_sentence, re.IGNORECASE):
        adjusted -= 0.15

    # Check for "nice to have" in sentence
    if re.search(r"nice\s+to\s+have", full_sentence, re.IGNORECASE):
        adjusted -= 0.25

    return max(0.0, min(1.0, adjusted))


# Register custom attribute if not already registered (module-level)
if not Doc.has_extension("requirements"):
    Doc.set_extension("requirements", default=None)


@Language.component("requirement_filter")
def requirement_filter(doc: Doc) -> Doc:
    """Extract requirements from Doc using trigger patterns.

    spaCy v3.7+ component that processes a Doc object and adds Doc._.requirements
    attribute with list of extracted requirement dicts.

    Args:
        doc: spaCy Doc object

    Returns:
        Doc with Doc._.requirements attribute set
    """
    requirements: List[Dict[str, Any]] = []
    text = doc.text

    # Precompute sentence boundaries for O(log n) lookup (Flaw #3 fix)
    sent_ranges = _build_sentence_char_ranges(doc)

    # Try each pattern
    for pattern in ALL_PATTERNS:
        regex_str: str = pattern["regex"]
        trigger_word: str = pattern["trigger_word"]
        base_confidence: float = pattern["confidence"]

        # Find all matches
        for match in re.finditer(regex_str, text, re.IGNORECASE):
            matched_text = match.group(1)
            span_start = match.start(1)
            span_end = match.end(1)

            # Extract sentence containing this match (O(log n) lookup via bisect)
            sent_range = _find_sentence_for_offset(span_start, sent_ranges)
            full_sentence = text[sent_range[0] : sent_range[1]] if sent_range else text

            # Apply confidence adjustments
            adjusted_confidence = _apply_confidence_adjustments(base_confidence, matched_text, full_sentence)

            # Skip if confidence is 0 (negation case)
            if adjusted_confidence <= 0.0:
                continue

            # Calculate token count
            token_cnt = _token_count(matched_text)

            # Create requirement entry
            requirement: Dict[str, Any] = {
                "text": matched_text,
                "span": (span_start, span_end),
                "trigger_word": trigger_word,
                "confidence": round(adjusted_confidence, 3),
                "token_count": token_cnt,
            }

            requirements.append(requirement)

    # Deduplicate by text (keep highest confidence; prefer better casing when tied)
    seen: Dict[str, Dict[str, Any]] = {}
    for req in requirements:
        req_text = req["text"].lower()
        if req_text not in seen:
            seen[req_text] = req
        elif req["confidence"] > seen[req_text]["confidence"]:
            # Higher confidence: always replace
            seen[req_text] = req
        elif req["confidence"] == seen[req_text]["confidence"]:
            # Tied confidence: prefer better casing (more capitals)
            seen[req_text] = _apply_casing_preference(seen[req_text], req)

    doc._.requirements = list(seen.values())
    return doc
