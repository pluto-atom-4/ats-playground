"""Pattern definitions for NER extraction."""

import re
from typing import Set

# Technology stack patterns (exact matches + variations)
TECH_PATTERNS = {
    "AI": [r"\bAI\b", r"\bartificial\s+intelligence\b"],
    "MATLAB": [r"\bMATLAB\b"],
    "Simulink": [r"\bSimulink\b"],
    "AI-assisted coding techniques": [
        r"AI-assisted\s+coding",
        r"AI\s+coding\s+techniques",
    ],
    "DOORS Next Generation": [r"DOORS\s+Next\s+Generation", r"DOORS\s+NG"],
    "JIRA": [r"\bJIRA\b"],
    "Git": [r"\bGit\b"],
    "Python": [r"\bPython\b"],
    "Verilog": [r"\bVerilog\b"],
    "SystemVerilog": [r"\bSystemVerilog\b", r"System\s+Verilog"],
    "ARM": [r"\bARM\b"],
    "C": [r"\bC\b(?!\+)"],  # C but not C++
    "C++": [r"\bC\+\+\b"],
}

# Skill keyphrases (extracted directly from job requirements)
SKILL_KEYPHRASES = {
    "Guidance and Control",
    "G&C algorithms",
    "Conceptual level design",
    "Post flight analysis",
    "Team leadership",
    "Staff coaching",
    "Collaborative skills",
    "Software integration",
    "Unit testing",
    "Launch operations support",
    "Test operations support",
    "Cross-functional communication",
    "Technical oversight",
    "Design reviews",
    "Systems analysis",
    "Architectural decision making",
    "Verification and validation",
    "Software development",
    "Mentoring",
    "Technical planning",
    "System modeling",
    "Hardware-in-the-loop testing",
    "Vehicle test campaigns",
}

# Fallback: single keywords for skills extraction
SKILL_KEYWORDS = {
    "leadership",
    "team leadership",
    "staff coaching",
    "mentoring",
    "management",
    "verification",
    "validation",
    "integration",
    "testing",
    "simulation",
    "modeling",
    "design",
    "architecture",
    "algorithm",
    "optimization",
    "performance",
    "analysis",
    "planning",
    "review",
    "oversight",
    "communication",
    "collaboration",
    "autonomy",
}

# Requirement keywords (years of experience, degrees, etc.)
REQUIREMENT_PATTERNS = {
    "years_experience": r"(\d+)\+?\s+years\s+(?:of\s+)?experience",
    "degree": r"(?:BS|MS|B\.S\.|M\.S\.|PhD|Ph\.D\.)",
    "skill_requirement": r"(?:required|must|must have|essential|needed)",
    "citizen_status": r"(?:U\.S\.\s+citizen|permanent\s+resident|refugee|asylee)",
}

# Context patterns (find skills in bullet points)
SKILL_EXTRACTION_PATTERNS = [
    r"(?:^|\n)\*\s+(.+?)(?:\n|\Z)",  # Bullet points with *
    r"(?:^|\n)(?:•|-)\s+(.+?)(?:\n|\Z)",  # Bullet points with • or -
]


def extract_technologies(text: str) -> Set[str]:
    """Extract known technologies from text."""
    techs = set()
    for tech_name, patterns in TECH_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                techs.add(tech_name)
                break
    return techs


def extract_requirement_spans(text: str) -> dict:
    """Extract requirement-related spans."""
    reqs = {
        "years_experience": [],
        "degrees": [],
        "citizen_status": [],
    }

    # Years of experience
    for match in re.finditer(REQUIREMENT_PATTERNS["years_experience"], text):
        reqs["years_experience"].append(match.group(0))

    # Degrees
    for match in re.finditer(REQUIREMENT_PATTERNS["degree"], text):
        reqs["degrees"].append(match.group(0))

    # Citizen status
    for match in re.finditer(REQUIREMENT_PATTERNS["citizen_status"], text):
        reqs["citizen_status"].append(match.group(0))

    return reqs


def extract_skill_candidates(text: str) -> Set[str]:
    """Extract skill candidates from bullet points."""
    candidates = set()

    # Extract all bullet point lines
    for pattern in SKILL_EXTRACTION_PATTERNS:
        for match in re.finditer(pattern, text, re.MULTILINE):
            line = match.group(1).strip()
            # Remove trailing punctuation and numbers
            line = re.sub(r"[\d\*\-\•]$", "", line).strip()
            if len(line) > 5:  # Skip short lines
                candidates.add(line)

    return candidates
