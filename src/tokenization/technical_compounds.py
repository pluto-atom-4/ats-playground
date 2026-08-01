"""Technical compound detection for skill classification.

Issue #191 Phase 2: Enhanced technical compound patterns for reclassification.
Identifies compound phrases that should be technologies, not skills.

Technical compounds identified in Phase 3 output:
- "software development" (6x) - development methodology
- "data processing" (3x) - data pipeline work
- "engineering technology" (3x) - tech framework/platform
- "manufacturing engineering" (3x) - engineering specialization
- "system-level" (3x) - architectural design

Confidence thresholds:
- High confidence (80%+): Exact matches, pattern-based detection
- Medium confidence (60-80%): Multi-word tech+verb combinations
"""

TECHNICAL_COMPOUND_PATTERNS = {
    # Software Development Compounds (Issue #191)
    "software development", "software engineering", "software development engineer",
    "software development platform", "software development lifecycle",

    # Data Processing Compounds (Issue #191)
    "data processing", "data processing pipeline", "data processing system",
    "data processing infrastructure", "big data processing",

    # Engineering Technology Compounds (Issue #191)
    "engineering technology", "engineering technology platform",
    "engineering technology stack", "engineering technology framework",

    # Manufacturing Engineering Compounds (Issue #191)
    "manufacturing engineering", "manufacturing engineering process",
    "manufacturing engineering technology", "manufacturing engineering automation",

    # System-Level Compounds (Issue #191)
    "system-level", "system-level design", "system-level architecture",
    "system-level integration", "system-level requirements",

    # Framework/library compounds (Phase 1)
    "spring framework", "spring boot", "react native", "express.js",

    # Service compounds (Phase 1)
    "web service", "microservice", "cloud service", "aws service",

    # Database compounds (Phase 1)
    "sql database", "nosql database",

    # Language/tool combinations (Phase 1)
    "python django", "python flask", "javascript react",
}


def is_technical_compound(phrase: str) -> bool:
    """Check if phrase is a technical compound that should be a technology not a skill.

    Phase 2 Logic:
    1. Exact match against known compounds (high confidence)
    2. Pattern-based detection (medium confidence)
    3. Multi-word validation (avoid false positives)

    Args:
        phrase: Text to check

    Returns:
        True if phrase is a technical compound, False otherwise
    """
    phrase_lower = phrase.lower().strip()

    if not phrase_lower or len(phrase_lower) < 3:
        return False

    # 1. Exact match against known compounds (highest confidence)
    if phrase_lower in TECHNICAL_COMPOUND_PATTERNS:
        return True

    # 2. Check for multi-word tech compounds (framework, library patterns)
    # Only applies to 2+ word phrases to avoid false positives on single words
    tech_keywords = {
        "framework", "library", "database", "service", "platform",
        "application", "system", "tool", "utility", "plugin", "extension",
    }

    words = phrase_lower.split()
    if len(words) >= 2:
        for kw in tech_keywords:
            if kw in phrase_lower:
                return True

    # 3. Pattern-based detection for Issue #191 compounds
    # Check for known compound patterns even if not exact match
    issue_191_keywords = {
        "software", "data processing", "engineering technology",
        "manufacturing", "system-level", "system",
    }

    # If phrase contains Issue #191 keywords AND is multi-word, likely compound
    if len(words) >= 2:
        for kw in issue_191_keywords:
            if kw in phrase_lower:
                # Validate: don't match single words (e.g., "software" alone)
                # Only match when part of a phrase (e.g., "software development")
                if phrase_lower != kw:
                    return True

    return False


def get_technical_compounds() -> set[str]:
    """Get all known technical compound patterns.

    Returns:
        Set of technical compound phrases
    """
    return TECHNICAL_COMPOUND_PATTERNS.copy()


def reclassify_compound(phrase: str) -> bool:
    """Determine if a phrase should be reclassified from skills to technologies.

    Args:
        phrase: Text to evaluate

    Returns:
        True if should be reclassified, False otherwise
    """
    return is_technical_compound(phrase)
