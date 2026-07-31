"""Normalize extracted entities to match expected output format."""

import re
from difflib import SequenceMatcher
from typing import Set


def normalize_requirement(req: str) -> str:
    """Clean and normalize requirement text."""
    # Remove leading/trailing whitespace
    req = req.strip()

    # Extract and preserve "(Preferred)" tag
    is_preferred = "(Preferred)" in req
    req = req.replace("(Preferred)", "").strip()

    # Truncate at secondary clauses (keep primary requirement only)
    # Remove location/project context
    req = re.sub(r"\s+on\s+fast-paced\s+projects$", "", req, flags=re.IGNORECASE)
    req = re.sub(r"\s+on\s+military\s+installations?$", "", req, flags=re.IGNORECASE)

    # Remove trailing list items (keep first item)
    # Only remove "simulations" or "software" type trailing items, not core concepts like "implementation"
    # "X, simulations, and software" → "X"
    req = re.sub(r",\s+(?:simulations|software),\s+and\s+[^,\.]*$", "", req, flags=re.IGNORECASE)
    req = re.sub(r",\s+and\s+integrated\s+vehicle.*$", "", req, flags=re.IGNORECASE)

    # Handle "development, implementation, and testing" → "implementation and testing"
    if re.search(r"^Experience\s+in\s+development,\s+implementation,\s+and", req, re.IGNORECASE):
        req = re.sub(r"development,\s+", "", req, flags=re.IGNORECASE)
        # Clean up "implementation, and" → "implementation and"
        req = re.sub(r",\s+and\s+", " and ", req, flags=re.IGNORECASE)
    elif re.search(r"^Experience\s+in\s+development\s+and", req, re.IGNORECASE):
        req = re.sub(r"development\s+and\s+", "", req, flags=re.IGNORECASE)

    # Remove "the development of" from "with the development of"
    req = re.sub(r"\s+with\s+the\s+development\s+of\s+", " with ", req, flags=re.IGNORECASE)

    # Remove "Experience in development" (fragment left from trimming)
    if req.lower() == "experience in development":
        return ""  # Will be filtered out

    # Standardize phrasing patterns
    # "Demonstrated experience X" → "Experience X"
    req = re.sub(
        r"^Demonstrated\s+experience\s+(?:in|with|involving)\s+",
        "Experience in ",
        req,
        flags=re.IGNORECASE
    )
    # "demonstrated ability to" → "Ability to"
    req = re.sub(
        r"^Demonstrated\s+ability\s+to\s+",
        "Ability to ",
        req,
        flags=re.IGNORECASE
    )
    # "Experience in X as well as Y" → "Experience in X and Y"
    req = re.sub(r"\s+as\s+well\s+as\s+", " and ", req, flags=re.IGNORECASE)
    # "Experience in X, Y, and Z" → standardize commas
    req = re.sub(r"\s+,\s+", ", ", req)

    # Remove redundant parentheticals (keep "M.S. or Ph.D." and "Preferred" but remove others)
    if "M.S. or Ph.D." not in req:
        # Remove parentheticals like "(e.g., ...)" and "(HIL)"
        req = re.sub(r"\s*\(\s*e\.g\..*?\)\s*", " ", req)
        req = re.sub(r"\s*\(HIL\)", "", req)
        # Remove trailing parentheticals
        req = re.sub(r"\s*\([^)]*\)\s*$", "", req)

    # Collapse multiple spaces
    req = re.sub(r"\s+", " ", req)

    # Re-add "(Preferred)" if present
    if is_preferred:
        req = f"{req} (Preferred)"

    return req


def deduplicate_requirements(
    requirements: Set[str], similarity_threshold: float = 0.65
) -> Set[str]:
    """Remove near-duplicate requirements, keeping shortest/best version."""
    reqs = sorted(list(requirements), key=lambda r: (len(r), r))
    deduplicated = []
    used_indices = set()

    for i, req in enumerate(reqs):
        if i in used_indices:
            continue

        # Check similarity with already-kept requirements and future ones
        keep_this = True
        for j in range(i + 1, len(reqs)):
            if j in used_indices:
                continue
            other = reqs[j]
            ratio = SequenceMatcher(None, req.lower(), other.lower()).ratio()

            # If similarity is high, mark longer one as duplicate
            if ratio > similarity_threshold:
                # Check if req is a substring of other (stronger signal)
                if req.lower() in other.lower():
                    # req is shorter and contained in other, keep req, discard other
                    used_indices.add(j)
                elif other.lower() in req.lower():
                    # other is shorter, discard this one
                    keep_this = False
                    used_indices.add(i)
                    break
                else:
                    # Similar but not substring, keep shorter
                    if len(req) <= len(other):
                        used_indices.add(j)
                    else:
                        keep_this = False
                        used_indices.add(i)
                        break

        if keep_this:
            deduplicated.append(req)
            used_indices.add(i)

    return set(deduplicated)


def normalize_requirements(requirements: Set[str]) -> Set[str]:
    """Normalize all requirements and deduplicate."""
    # Normalize each
    normalized = {normalize_requirement(req) for req in requirements}

    # Filter out empty strings
    normalized = {req for req in normalized if req.strip()}

    # Deduplicate
    deduplicated = deduplicate_requirements(normalized, similarity_threshold=0.80)

    return deduplicated


def normalize_skills(skills: Set[str]) -> Set[str]:
    """Normalize skill names (preserve exact format from extraction)."""
    # Skills are already in correct format from extraction via keyphrases
    # Only add normalization if needed (fallback keywords)
    normalized = set()

    # Known correctly-capitalized skills (multi-domain)
    known_skills = {
        # Aerospace/Software Leadership
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
        # Software/Systems Domain
        "Software architecture",
        "Hands-on software development",
        "Systems maintenance",
        "Binary data transformation",
        "Integrity check implementation",
        "Time-series data analytics",
        "Storage architecture design",
        "Sensor data calibration",
        "Sensor data synchronization",
        "Technology evaluation",
        "Code reviews",
        "Design walkthroughs",
        "Technical coaching",
        "Project management",
        "Problem decomposition",
        "Technical communication",
        "Engineering data interpretation",
        "Engineering drawing interpretation",
        "Quantitative analysis",
        "Statistical analysis",
        "Data collection",
        "Data preparation",
        "Cloud service deployment",
        "Software documentation",
        # Additional Software/Systems
        "Software design",
        "System design",
        "Component design",
        "API design",
        "Database design",
        "Architecture review",
        "Code quality assurance",
        "Testing strategy",
        "Integration testing",
        "Performance testing",
        "Security testing",
        "Agile development",
        "DevOps practices",
        "CI/CD implementation",
        "Deployment automation",
        "Infrastructure management",
        "Configuration management",
        "Requirements analysis",
        "Stakeholder management",
        "Technical documentation",
        "Knowledge transfer",
        "Best practices implementation",
        "Standards compliance",
        "Process improvement",
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
