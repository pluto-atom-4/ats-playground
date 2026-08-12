"""Standalone POC: Requirement extraction from job descriptions.

No dependencies on Phase 8a/8b components. Implements simplified pipeline:
1. Sentence splitting (spaCy sentencizer)
2. Sentence classification (hardcoded patterns + confidence scoring)
3. Span refinement (optional multi-line expansion)
4. JSON output (company + requirements list)

Uses en_core_web_sm for lightweight inference.
"""

import logging
import re
from typing import Any, Dict, List, Optional, TypedDict

import spacy
from pydantic import BaseModel, Field
from spacy.language import Language

from .bullet_point_preprocessor import normalize_bullet_points

logger = logging.getLogger(__name__)


class RequirementPattern(TypedDict):
    """Type definition for requirement pattern dict."""

    trigger: str
    regex: str
    confidence: float
    priority: int


# =============================================================================
# HARDCODED TRIGGER PATTERNS (Tier-Based)
# =============================================================================

REQUIREMENT_PATTERNS: List[RequirementPattern] = [
    # TIER 1: High-confidence (0.90-0.95) - Mandatory language
    {
        "trigger": "required",
        "regex": r"\brequired\b",
        "confidence": 0.95,
        "priority": 1,
    },
    {
        "trigger": "must",
        "regex": r"\bmust\s+(?:have|be|possess|know|understand)",
        "confidence": 0.93,
        "priority": 1,
    },
    {
        "trigger": "essential",
        "regex": r"\bessential\b",
        "confidence": 0.90,
        "priority": 1,
    },
    {
        "trigger": "mandatory",
        "regex": r"\bmandatory\b",
        "confidence": 0.92,
        "priority": 1,
    },
    {
        "trigger": "ability to",
        "regex": r"\bability\s+to\b",
        "confidence": 0.92,
        "priority": 1,
    },
    {
        "trigger": "experience with",
        "regex": r"\b(?:experience|background)\s+(?:with|in)\b",
        "confidence": 0.88,
        "priority": 1,
    },
    {
        "trigger": "proficiency",
        "regex": r"\bproficiency\b",
        "confidence": 0.91,
        "priority": 1,
    },
    {
        "trigger": "knowledge of",
        "regex": r"\bknowledge\s+of\b",
        "confidence": 0.85,
        "priority": 1,
    },
    {
        "trigger": "understanding of",
        "regex": r"\bunderstanding\s+of\b",
        "confidence": 0.83,
        "priority": 1,
    },
    # TIER 2: Medium-confidence (0.65-0.80) - Softer requirements
    {
        "trigger": "should",
        "regex": r"\bshould\s+(?:have|know|be|possess)",
        "confidence": 0.70,
        "priority": 2,
    },
    {
        "trigger": "prefer",
        "regex": r"\b(?:prefer|preferred)\b",
        "confidence": 0.65,
        "priority": 2,
    },
    {
        "trigger": "bachelor's degree",
        "regex": r"\b(?:bachelor's?|master's?|phd)\s+(?:degree|in)\b",
        "confidence": 0.89,
        "priority": 2,
    },
    {
        "trigger": "years of",
        "regex": r"\b(\d+\+?)\s+years?\s+(?:of|in)\b",
        "confidence": 0.80,
        "priority": 2,
    },
    # TIER 3: Lower-confidence (0.40-0.55) - Nice-to-have, aspirational
    {
        "trigger": "nice to have",
        "regex": r"\bnice\s+to\s+have\b",
        "confidence": 0.40,
        "priority": 3,
    },
    {
        "trigger": "ideal",
        "regex": r"\bideal\b",
        "confidence": 0.55,
        "priority": 3,
    },
    {
        "trigger": "bonus",
        "regex": r"\bbonus\b",
        "confidence": 0.45,
        "priority": 3,
    },
    # BULLET-SPECIFIC PATTERNS (extracted from bullets)
    {
        "trigger": "years_in_bullet",
        "regex": r"\b(\d+\+?)\s+years?\b",
        "confidence": 0.85,
        "priority": 2,
    },
    {
        "trigger": "ability_in_bullet",
        "regex": r"\bability\b",
        "confidence": 0.90,
        "priority": 1,
    },
    {
        "trigger": "required_prefix",
        "regex": r"\brequired\b",
        "confidence": 0.95,
        "priority": 1,
    },
    {
        "trigger": "degree_in_bullet",
        "regex": r"\b(?:bachelor's?|master's?|phd|degree)\b",
        "confidence": 0.92,
        "priority": 2,
    },
]


# =============================================================================
# OUTPUT MODELS
# =============================================================================


class SimpleRequirementExtractionOutput(BaseModel):
    """Minimal output schema (company + requirements list only)."""

    company: Optional[str] = Field(None, description="Company name")
    requirements: List[str] = Field(default_factory=list, description="Extracted requirements")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Pipeline metadata (sentences analyzed, patterns matched, etc.)",
    )


# =============================================================================
# CORE FUNCTIONS
# =============================================================================


def load_spacy_model(model_name: str = "en_core_web_sm") -> Language:
    """Load spaCy model, raise error if missing.

    Args:
        model_name: spaCy model to load (default: en_core_web_sm)

    Returns:
        Loaded spaCy Language object

    Raises:
        RuntimeError: If model not found
    """
    try:
        return spacy.load(model_name)
    except OSError as e:
        raise RuntimeError(
            f"spaCy model '{model_name}' not found. Install with: python -m spacy download {model_name}"
        ) from e


def split_sentences(text: str, nlp: Language) -> List[str]:
    """Split text into sentences using spaCy sentencizer.

    Args:
        text: Input text
        nlp: Loaded spaCy Language object

    Returns:
        List of sentence texts (stripped)
    """
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


def _has_negation_context(sentence: str, trigger: str) -> bool:
    """Detect negation patterns near trigger word.

    Detects:
    - "not required"
    - "no experience"
    - "don't need"
    - "isn't necessary"
    - "without experience"

    Args:
        sentence: Full sentence text
        trigger: Trigger word to search for

    Returns:
        True if negation found near trigger word
    """
    negation_words = [
        r"\bnot\b",
        r"\bno\b",
        r"\bdon't\b",
        r"\bdoesn't\b",
        r"\bwithout\b",
    ]

    # Find trigger position
    trigger_pos = sentence.lower().find(trigger.lower())
    if trigger_pos == -1:
        return False

    # Look ±50 chars around trigger
    context_start = max(0, trigger_pos - 50)
    context_end = min(len(sentence), trigger_pos + len(trigger) + 50)
    context = sentence[context_start:context_end]

    for neg_pattern in negation_words:
        if re.search(neg_pattern, context, re.IGNORECASE):
            return True

    return False


def _apply_adjustments(base_confidence: float, sentence: str) -> float:
    """Apply confidence adjustments for context.

    Adjustments:
    - Parentheticals (e.g., "(preferred)"): -0.10
    - Conditional ("if you have..."): -0.15
    - Nice to have: -0.25
    - All caps (emphasis): +0.05

    Args:
        base_confidence: Base confidence score
        sentence: Full sentence text

    Returns:
        Adjusted confidence (clamped to [0.0, 1.0])
    """
    adj = base_confidence

    # Parentheticals: lower confidence
    if re.search(r"\(.*?\)", sentence):
        adj -= 0.10

    # Conditional: lower confidence
    if re.search(r"\bif\b", sentence, re.IGNORECASE):
        adj -= 0.15

    # Nice to have: significantly lower
    if re.search(r"nice\s+to\s+have", sentence, re.IGNORECASE):
        adj -= 0.25

    # All-caps emphasis: boost
    if len(re.findall(r"\b[A-Z]{4,}\b", sentence)) > 2:
        adj += 0.05

    return max(0.0, min(1.0, adj))


def classify_sentence_as_requirement(
    sentence: str,
    nlp: Language,
) -> Optional[Dict[str, Any]]:
    """Classify single sentence as containing a requirement.

    Returns dict with requirement info or None if no requirement detected.

    Args:
        sentence: Single sentence text
        nlp: Loaded spaCy Language object

    Returns:
        Dict with keys: text, trigger_word, confidence, negated, source
        or None if no requirement detected
    """
    if not sentence.strip():
        return None

    # Try each pattern
    best_match: Optional[Dict[str, Any]] = None

    for pattern in REQUIREMENT_PATTERNS:
        if re.search(pattern["regex"], sentence, re.IGNORECASE):
            # Found a match
            confidence: float = pattern["confidence"]

            # Check negations
            if _has_negation_context(sentence, pattern["trigger"]):
                return None  # Negation found, skip entirely

            # Apply context adjustments
            confidence = _apply_adjustments(confidence, sentence)

            if confidence > 0:
                # Keep best match (by priority, then confidence)
                if best_match is None:
                    should_update = True
                else:
                    best_priority: int = best_match["priority"]  # type: ignore
                    best_confidence: float = best_match["confidence"]  # type: ignore
                    should_update = pattern["priority"] < best_priority or (
                        pattern["priority"] == best_priority and confidence > best_confidence
                    )

                if should_update:
                    best_match = {
                        "text": sentence,
                        "trigger_word": pattern["trigger"],
                        "confidence": confidence,
                        "negated": False,
                        "source": "single_sentence",
                        "priority": pattern["priority"],
                    }

    if best_match:
        # Remove temporary priority field
        best_match.pop("priority")
        return best_match

    return None


def extract_company_name_enhanced(markdown: str) -> Optional[str]:
    """Extract company name from markdown with enhanced fallback chain.

    Tries patterns in order:
    1. # Company Name (h1 header)
    2. ## Company Name section
    3. company: Name field
    4. employer: Name field
    5. Prose mention (capital company name near start)
    6. Capitalized phrase pattern

    Args:
        markdown: Markdown job description

    Returns:
        Company name or None if not found
    """
    patterns = [
        (r"^#\s+([^\n]+)", "h1"),
        (r"^##\s+company\b.*?\n([^\n]+)", "h2_company"),
        (r"company:\s*([^\n]+)", "company_field"),
        (r"employer:\s*([^\n]+)", "employer_field"),
        (
            r"\b([A-Z][a-zA-Z0-9\s&]*(?:Robotics|Corp|Inc|Ltd|LLC|Technology|AI|Systems|Software|Services))\b",
            "prose_mention",
        ),
        (r"\b([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)?)\s+(?:is the|is a|has|announces)", "capitalized_phrase"),
    ]

    for pattern, _name in patterns:
        match = re.search(pattern, markdown, re.MULTILINE | re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if company and len(company) > 1:  # Filter out single-char matches
                return company

    return None


def extract_company_name(markdown: str) -> Optional[str]:
    """Legacy function: delegates to enhanced version.

    Args:
        markdown: Markdown job description

    Returns:
        Company name or None if not found
    """
    return extract_company_name_enhanced(markdown)


def extract_requirements_standalone(
    markdown: str,
    min_confidence: float = 0.50,
    max_requirements: int = 20,
) -> SimpleRequirementExtractionOutput:
    """Full extraction pipeline (standalone, no Phase 8a/8b).

    Pipeline:
    1. Load spaCy model
    2. Split into sentences
    3. Classify each sentence as requirement
    4. Filter by confidence
    5. Deduplicate
    6. Extract company
    7. Return JSON

    Args:
        markdown: Raw markdown job description
        min_confidence: Minimum confidence threshold (default 0.50)
        max_requirements: Maximum requirements to return (default 20)

    Returns:
        SimpleRequirementExtractionOutput with company + requirements
    """
    logger.info("Starting standalone requirement extraction pipeline")

    # Stage 1: Load model
    nlp = load_spacy_model("en_core_web_sm")

    # Stage 1.5: Normalize bullet points
    normalized_markdown = normalize_bullet_points(markdown)
    logger.info("Normalized bullet points")

    # Stage 2: Split sentences
    sentences = split_sentences(normalized_markdown, nlp)
    logger.info(f"Split into {len(sentences)} sentences")

    # Stage 3: Classify sentences
    candidate_requirements = []
    for sentence in sentences:
        req_info = classify_sentence_as_requirement(sentence, nlp)
        if req_info and req_info["confidence"] >= min_confidence:
            candidate_requirements.append(req_info)

    logger.info(f"Classified {len(candidate_requirements)} requirements (confidence >= {min_confidence})")

    # Stage 4: Deduplicate by normalized text
    seen_normalized: Dict[str, Dict[str, Any]] = {}
    for req in candidate_requirements:
        norm_key = req["text"].lower().strip()
        if norm_key not in seen_normalized:
            seen_normalized[norm_key] = req
        elif req["confidence"] > seen_normalized[norm_key]["confidence"]:
            seen_normalized[norm_key] = req

    # Sort by confidence descending
    unique_reqs = sorted(
        seen_normalized.values(),
        key=lambda r: r["confidence"],
        reverse=True,
    )[:max_requirements]

    logger.info(f"Deduplicated to {len(unique_reqs)} unique requirements")

    # Stage 5: Extract company
    company = extract_company_name(markdown)
    logger.info(f"Extracted company: {company}")

    # Build output
    metadata = {
        "sentences_analyzed": len(sentences),
        "requirements_extracted": len(unique_reqs),
        "spacy_model": "en_core_web_sm",
        "pipeline_components": ["sentencizer", "pattern_matching", "deduplication"],
        "min_confidence_threshold": min_confidence,
        "max_requirements_limit": max_requirements,
        "patterns_count": len(REQUIREMENT_PATTERNS),
    }

    return SimpleRequirementExtractionOutput(
        company=company,
        requirements=[r["text"] for r in unique_reqs],
        metadata=metadata,
    )


# =============================================================================
# CONVENIENCE INTERFACE
# =============================================================================


def extract_requirements_b(
    markdown_text: str,
    min_confidence: float = 0.50,
    max_requirements: int = 20,
) -> SimpleRequirementExtractionOutput:
    """Convenience function for single-pass extraction.

    Args:
        markdown_text: Markdown job description
        min_confidence: Minimum confidence threshold
        max_requirements: Maximum requirements to return

    Returns:
        SimpleRequirementExtractionOutput with structured results
    """
    return extract_requirements_standalone(markdown_text, min_confidence, max_requirements)


if __name__ == "__main__":
    # Simple CLI for testing
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.poc.extract_requirements_b <markdown_file>")
        sys.exit(1)

    markdown_file = sys.argv[1]
    with open(markdown_file) as f:
        markdown_text = f.read()

    result = extract_requirements_b(markdown_text)
    print(json.dumps(result.model_dump(), indent=2))
