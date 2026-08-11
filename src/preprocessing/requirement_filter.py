"""Rule-based requirement extraction component for spaCy pipeline.

Implements trigger-word detection with regex patterns to extract job requirements
from prose text. Adds Doc._.requirements custom attribute with structured metadata.
"""

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

    # Check for negation within matched text span only (not full sentence)
    # Pattern 1: Negation before trigger word (e.g., "not required", "no experience")
    negation_before_pattern = (
        r"(?:no|not|don't|doesn't|didn't|without)\s+(?:prior\s+)?"
        r"(?:experience|requirement|required|require|requires|must|essential|ability\s+to|"
        r"proficiency|knowledge|understanding)"
    )
    if re.search(negation_before_pattern, text, re.IGNORECASE):
        return 0.0

    # Pattern 2: Negation within matched text itself (e.g., "not required")
    if re.search(r"(?:not|no|don't|doesn't|didn't|without)\b", text, re.IGNORECASE):
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

            # Extract sentence containing this match (Bug #2 fix)
            # Find which sentence contains this character position
            full_sentence = text  # fallback to full text if no sentence found
            for sent in doc.sents:
                if sent.start_char <= span_start < sent.end_char:
                    full_sentence = sent.text
                    break

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

    # Deduplicate by text (keep highest confidence)
    seen: Dict[str, Dict[str, Any]] = {}
    for req in requirements:
        req_text = req["text"].lower()
        if req_text not in seen or req["confidence"] > seen[req_text]["confidence"]:
            seen[req_text] = req

    doc._.requirements = list(seen.values())
    return doc
