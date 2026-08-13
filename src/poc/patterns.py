"""Centralized pattern definitions for POC-C section-aware extraction.

Contains:
- SECTION_RULER_PATTERNS: SpanRuler patterns (token-based + regex-based)
- CONFIDENCE_ADJUSTMENT_BY_SECTION: Section-specific confidence boosts/penalties
- SECTION_DISPLAY_NAMES: Human-readable section labels
- DEFAULT_TARGET_SECTIONS: Sections to extract requirements from

Issue #265: Redesigned to support multi-word section headers via regex patterns.
"""

from typing import Any, Dict, List

# =============================================================================
# SECTION RULER PATTERNS (SpanRuler)
# =============================================================================
# Hybrid approach: token-based patterns for single-word headers,
# regex-based patterns for multi-word headers and special chars.
#
# Pattern dict structure: {"label": str, "pattern": str | List[Dict]}
# - Token pattern: List of token attribute dicts (spaCy format)
# - Regex pattern: Single regex string (requires type: "regex")

SECTION_RULER_PATTERNS: List[Dict[str, Any]] = [
    # =================================================================
    # TARGET SECTIONS (extract requirements from these)
    # =================================================================
    # TOKEN PATTERNS (Multi-word headers - tokenized to match spaCy output)
    {
        "label": "SECTION_KNOWLEDGE_SKILLS",
        "pattern": [
            {"LOWER": "knowledge"},
            {"IS_PUNCT": True, "OP": "?"},  # optional comma
            {"LOWER": "skills"},
            {"LOWER": {"IN": ["&", "and"]}},
            {"LOWER": "abilities"},
        ],
    },
    {
        "label": "SECTION_IN_OFFICE",
        "pattern": [
            {"LOWER": {"IN": ["in"]}},
            {"LOWER": "office"},
            {"LOWER": {"IN": ["requirements", "location"]}},
        ],
    },
    {
        "label": "SECTION_WHAT_YOU_DO",
        "pattern": [
            {"LOWER": "what"},
            {"LOWER": {"IN": ["you'll", "you"]}},
            {"IS_PUNCT": False, "OP": "?"},  # optional 'll or will
            {"LOWER": "do"},
        ],
    },
    # TOKEN PATTERNS (Single-word headers, backward compatible)
    {
        "label": "SECTION_REQUIREMENTS",
        "pattern": [
            {"LOWER": "requirements"},
        ],
    },
    {
        "label": "SECTION_QUALIFICATIONS",
        "pattern": [
            {"LOWER": "qualifications"},
        ],
    },
    {
        "label": "SECTION_TECHNICAL_SKILLS",
        "pattern": r"(?i)technical\s+skills",
        "type": "regex",
    },
    {
        "label": "SECTION_PREFERRED_SKILLS",
        "pattern": [
            {"LOWER": "preferred"},
            {"LOWER": "skills", "OP": "?"},
        ],
    },
    {
        "label": "SECTION_NICE_TO_HAVE",
        "pattern": [
            {"LOWER": "nice"},
            {"LOWER": "to"},
            {"LOWER": "have"},
        ],
    },
    {
        "label": "SECTION_EDUCATION",
        "pattern": [
            {"LOWER": "education"},
        ],
    },
    {
        "label": "SECTION_EXPERIENCE",
        "pattern": r"(?i)(?:required\s+)?(?:professional\s+)?experience(?:\s+(?:section|level|required))?(?:\s*$|\n)",
        "type": "regex",
    },
    # =================================================================
    # FILTER SECTIONS (skip extraction from these)
    # =================================================================
    {
        "label": "SECTION_BENEFITS",
        "pattern": [
            {"LOWER": "benefits"},
            {"IS_PUNCT": False, "OP": "*"},
        ],
    },
    {
        "label": "SECTION_COMPENSATION",
        "pattern": [
            {"LOWER": {"IN": ["salary", "compensation", "pay"]}},
            {"IS_PUNCT": False, "OP": "*"},
        ],
    },
    {
        "label": "SECTION_HIRING_PROCESS",
        "pattern": [
            {"LOWER": {"IN": ["hiring", "application", "process"]}},
            {"IS_PUNCT": False, "OP": "*"},
        ],
    },
]


# =============================================================================
# CONFIDENCE ADJUSTMENTS BY SECTION
# =============================================================================
# Applied to base pattern confidence when extracting from specific sections.
# Range: -0.50 to +0.50. Final confidence clamped to [0.0, 1.0].

CONFIDENCE_ADJUSTMENT_BY_SECTION: Dict[str, float] = {
    # High priority sections (explicit requirements)
    "SECTION_REQUIREMENTS": 0.15,
    "SECTION_QUALIFICATIONS": 0.10,
    "SECTION_TECHNICAL_SKILLS": 0.12,
    "SECTION_KNOWLEDGE_SKILLS": 0.12,  # NEW: explicit "Skills & Abilities" section
    # Medium priority sections
    "SECTION_EXPERIENCE": 0.08,
    "SECTION_IN_OFFICE": 0.08,  # NEW: location/on-site requirement
    "SECTION_EDUCATION": 0.05,
    # Lower priority sections
    "SECTION_PREFERRED_SKILLS": -0.15,
    "SECTION_NICE_TO_HAVE": -0.25,
    "SECTION_WHAT_YOU_DO": -0.05,  # NEW: responsibilities, not requirements
    # Filter sections (exclude from extraction)
    "SECTION_BENEFITS": -0.50,
    "SECTION_COMPENSATION": -0.50,
    "SECTION_HIRING_PROCESS": -0.50,
}


# =============================================================================
# SECTION DISPLAY NAMES (Human-Readable Labels)
# =============================================================================

SECTION_DISPLAY_NAMES: Dict[str, str] = {
    # Token-based patterns
    "SECTION_REQUIREMENTS": "Requirements",
    "SECTION_QUALIFICATIONS": "Qualifications",
    "SECTION_TECHNICAL_SKILLS": "Technical Skills",
    "SECTION_PREFERRED_SKILLS": "Preferred Skills",
    "SECTION_NICE_TO_HAVE": "Nice to Have",
    "SECTION_EDUCATION": "Education",
    "SECTION_EXPERIENCE": "Experience",
    # Regex-based patterns (Issue #265)
    "SECTION_KNOWLEDGE_SKILLS": "Knowledge, Skills & Abilities",
    "SECTION_IN_OFFICE": "In Office Requirements",
    "SECTION_WHAT_YOU_DO": "What You'll Do",
    # Filter sections
    "SECTION_BENEFITS": "Benefits",
    "SECTION_COMPENSATION": "Compensation",
    "SECTION_HIRING_PROCESS": "Hiring Process",
}


# =============================================================================
# DEFAULT TARGET SECTIONS (Extract Requirements From These)
# =============================================================================
# Excludes filter sections automatically.

DEFAULT_TARGET_SECTIONS: List[str] = [
    "SECTION_REQUIREMENTS",
    "SECTION_QUALIFICATIONS",
    "SECTION_TECHNICAL_SKILLS",
    "SECTION_PREFERRED_SKILLS",
    "SECTION_NICE_TO_HAVE",
    "SECTION_EDUCATION",
    "SECTION_EXPERIENCE",
    "SECTION_KNOWLEDGE_SKILLS",  # NEW: from regex pattern
    "SECTION_IN_OFFICE",  # NEW: from regex pattern
    # SECTION_WHAT_YOU_DO intentionally excluded (responsibilities, penalty -0.05)
]
