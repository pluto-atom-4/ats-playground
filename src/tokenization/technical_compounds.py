"""Technical compound detection for skill classification."""

TECHNICAL_COMPOUND_PATTERNS = {
    # Framework/library compounds
    "spring framework", "spring boot", "react native", "express.js",
    # Service compounds
    "web service", "microservice", "cloud service", "aws service",
    # Database compounds
    "sql database", "nosql database",
    # Language/tool combinations
    "python django", "python flask", "javascript react",
}


def is_technical_compound(phrase: str) -> bool:
    """Check if phrase is a technical compound that should be a technology not a skill."""
    phrase_lower = phrase.lower()

    # Check exact matches
    if phrase_lower in TECHNICAL_COMPOUND_PATTERNS:
        return True

    # Check for multi-word tech compounds (framework, library patterns)
    tech_keywords = {
        "framework", "library", "database", "service", "platform",
        "application", "system", "tool", "utility", "plugin", "extension",
    }

    words = phrase_lower.split()
    if len(words) >= 2:
        for kw in tech_keywords:
            if kw in phrase_lower:
                return True

    return False
