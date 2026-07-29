"""Normalize extracted entities to match expected output format."""

import re
from typing import Set, List
from difflib import SequenceMatcher


def normalize_requirement(req: str) -> str:
    """Clean and normalize requirement text."""
    # Remove leading/trailing whitespace
    req = req.strip()

    # Extract and preserve "(Preferred)" tag
    is_preferred = "(Preferred)" in req
    req = req.replace("(Preferred)", "").strip()

    # Standardize phrasing
    req = re.sub(r"demonstrated\s+", "Demonstrated ", req, flags=re.IGNORECASE)
    req = re.sub(r"^experience\s+in", "Experience in", req, flags=re.IGNORECASE)

    # Remove redundant parentheticals (keep "M.S. or Ph.D." but remove others)
    if "M.S. or Ph.D." not in req:
        req = re.sub(r"\s*\([^)]*\)\s*", " ", req).strip()

    # Collapse multiple spaces
    req = re.sub(r"\s+", " ", req)

    # Re-add "(Preferred)" if present
    if is_preferred:
        req = f"{req} (Preferred)"

    return req


def deduplicate_requirements(
    requirements: Set[str], similarity_threshold: float = 0.75
) -> Set[str]:
    """Remove near-duplicate requirements, keeping shortest version."""
    reqs = sorted(list(requirements), key=len)
    deduplicated = []
    used = set()

    for req in reqs:
        if req in used:
            continue

        # Check similarity with already-kept requirements
        is_duplicate = False
        for kept in deduplicated:
            ratio = SequenceMatcher(None, req.lower(), kept.lower()).ratio()
            if ratio > similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            deduplicated.append(req)
            used.add(req)

    return set(deduplicated)


def normalize_requirements(requirements: Set[str]) -> Set[str]:
    """Normalize all requirements and deduplicate."""
    # Normalize each
    normalized = {normalize_requirement(req) for req in requirements}

    # Deduplicate
    deduplicated = deduplicate_requirements(normalized, similarity_threshold=0.80)

    return deduplicated


def normalize_skills(skills: Set[str]) -> Set[str]:
    """Normalize skill names (preserve exact format from extraction)."""
    # Skills are already in correct format from extraction via keyphrases
    # Only add normalization if needed (fallback keywords)
    normalized = set()

    # Known correctly-capitalized skills
    known_skills = {
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
        # ASIC/Hardware
        "Formal verification",
        "Clock gating",
        "CDC analysis",
        "RDC analysis",
        "Lint checking",
        "Verilog design",
        "SystemVerilog design",
        "SoC design",
        "ASIC design",
        "SOC verification",
        "Performance optimization",
        "Power optimization",
        "DFT implementation",
        "Gate simulation",
        "Timing analysis",
    }

    for skill in skills:
        if skill in known_skills:
            normalized.add(skill)
        else:
            # Fallback: capitalize first letter of each word
            words = skill.split()
            capitalized = [w.capitalize() for w in words]
            normalized.add(" ".join(capitalized))

    return normalized


def normalize_technologies(technologies: Set[str]) -> Set[str]:
    """Normalize technology names."""
    # Most tech names have specific capitalization; keep as-is
    return technologies
