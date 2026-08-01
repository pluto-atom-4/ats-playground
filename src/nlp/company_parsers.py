"""Company-specific requirement parsers."""

import re
from abc import ABC, abstractmethod
from typing import Dict, Set


class CompanyParser(ABC):
    """Base class for company-specific requirement parsing."""

    company_name: str

    @abstractmethod
    def parse_requirements(self, text: str) -> Set[str]:
        """Parse requirements specific to this company's format."""
        pass

    def extract_section(self, text: str, section_pattern: str) -> str:
        """Extract a specific section from the text."""
        match = re.search(section_pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1) if match else ""


class BlueOriginParser(CompanyParser):
    """Blue Origin-specific requirement parser."""

    company_name = "blue origin"

    def parse_requirements(self, text: str) -> Set[str]:
        """Parse Blue Origin's structured bullet format."""
        requirements = set()

        # Extract minimum qualifications section
        min_qual = self.extract_section(
            text,
            r"(?:##\s+)?(?:minimum|required)\s+(?:qualifications?|experience)[\s\n:]*(.+?)(?=\n##|Preferred|---|\Z)"
        )

        if min_qual:
            bullets = re.findall(r"[\*•\-]\s+(.+?)(?:\n|$)", min_qual)
            for bullet in bullets:
                bullet = bullet.strip()
                # Keep bullets unless they're ONLY about years (no domain context)
                is_only_years = re.match(r"^\d+\+?\s+years\s+of\s+experience\s*$", bullet, re.IGNORECASE)
                if 10 < len(bullet) < 150 and not is_only_years:
                    requirements.add(bullet)

        # Years of experience (only add if domain specified)
        for match in re.finditer(
            r"(\d+)\+?\s+years\s+(?:of\s+)?experience"
            r"(?:\s+(?:in|with|focused\s+on)\s+([^\.\n]+))?",
            text,
            re.IGNORECASE,
        ):
            years = match.group(1)
            domain = match.group(2)
            if domain:
                domain = domain.strip().rstrip(".,;")
                requirements.add(f"{years}+ years of experience in {domain}")

        # Security clearance (Blue Origin: standard background check)
        if re.search(r"background\s+check|security\s+clearance", text, re.IGNORECASE):
            requirements.add("Blue's Standard Background Check")

        # Citizenship
        if re.search(r"U\.S\.\s+(?:citizen|national)", text, re.IGNORECASE):
            requirements.add("U.S. citizen, national, permanent resident, refugee, or asylee status")

        return requirements


class BoeingParser(CompanyParser):
    """Boeing-specific requirement parser (narrative + structured)."""

    company_name = "boeing"

    def parse_requirements(self, text: str) -> Set[str]:
        """Parse Boeing's mixed structured/narrative format."""
        requirements = set()

        # Extract basic qualifications section (handle ### h3 and ## h2 headers)
        basic_qual = self.extract_section(
            text,
            r"(?:#{2,3}\s+)?(?:basic|minimum|required)\s+(?:qualifications?|skills/experience)[\s\n:]*(.+?)(?=\n#{2,3}|Preferred|Travel|---|\Z)"
        )

        if basic_qual:
            bullets = re.findall(r"[\*•\-]\s+(.+?)(?:\n|$)", basic_qual)
            for bullet in bullets:
                bullet = bullet.strip()
                # Keep bullets unless they're ONLY about years (no domain context)
                is_only_years = re.match(r"^\d+\+?\s+years\s+of\s+experience\s*$", bullet, re.IGNORECASE)
                if 10 < len(bullet) < 150 and not is_only_years:
                    requirements.add(bullet)

        # Years of experience with language specification (only add if domain specified)
        for match in re.finditer(
            r"(\d+)\+?\s+years\s+(?:of\s+)?experience(?:\s+(?:in|with|using|focused\s+on)\s+([^\.\n]+))?",
            text,
            re.IGNORECASE
        ):
            years = match.group(1)
            domain = match.group(2)
            if domain:
                domain = domain.strip().rstrip(".,;")
                requirements.add(f"{years}+ years of experience {domain}")

        # Bachelor's degree
        if re.search(r"Bachelor[''s]*\s+(?:Degree|of\s+Science)", text, re.IGNORECASE):
            requirements.add("Bachelor's Degree")

        # Security clearance (Boeing: Top Secret for defense)
        if re.search(r"Top\s+Secret", text, re.IGNORECASE):
            requirements.add("Ability to obtain a U.S. Security Clearance (requires U.S. Citizenship)")

        # U.S. Person status
        if re.search(r"U\.S\.\s+Person|export\s+control", text, re.IGNORECASE):
            requirements.add("U.S. Person status as defined by 22 C.F.R. §120.62 for export control compliance")

        # Coding assessment
        if re.search(r"CodeVue|coding\s+challenge", text, re.IGNORECASE):
            requirements.add("Completion of the CodeVue Coding Challenge during the selection process")

        # Drug test
        if re.search(r"drug", text, re.IGNORECASE):
            requirements.add("Passing a post-offer drug test")

        # Extract from preferred section (marked as Preferred)
        pref_qual = self.extract_section(
            text,
            r"(?:#{2,3}\s+)?(?:preferred|desired)\s+(?:qualifications?|experience)[\s\n:]*(.+?)(?=\n#{2,3}|Travel|Background|---|\Z)"
        )

        if pref_qual:
            bullets = re.findall(r"[\*•\-]\s+(.+?)(?:\n|$)", pref_qual)
            for bullet in bullets:
                bullet = bullet.strip()
                if 10 < len(bullet) < 150:
                    requirements.add(f"{bullet} (Preferred)")

        return requirements


class GenericParser(CompanyParser):
    """Generic fallback parser for unknown companies."""

    company_name = "generic"

    def parse_requirements(self, text: str) -> Set[str]:
        """Generic requirement extraction."""
        requirements = set()

        # Try both minimum and basic qualifications
        for section_label in [r"basic\s+qualifications", r"minimum\s+qualifications"]:
            section = self.extract_section(
                text,
                rf"(?:##\s+)?(?:{section_label})[\s\n:]*(.+?)(?=\n##|Preferred|---|\Z)"
            )
            if section:
                bullets = re.findall(r"[\*•\-]\s+(.+?)(?:\n|$)", section)
                for bullet in bullets:
                    bullet = bullet.strip()
                    is_only_years = re.match(r"^\d+\+?\s+years\s+of\s+experience\s*$", bullet, re.IGNORECASE)
                    if 10 < len(bullet) < 150 and not is_only_years:
                        requirements.add(bullet)
                break

        # Years of experience (only add if in section with domain context)
        # Skip generic "X+ years of experience" without context

        # Degree
        if re.search(r"degree|bachelor|master", text, re.IGNORECASE):
            if not any("degree" in req.lower() for req in requirements):
                requirements.add("Bachelor's Degree or equivalent")

        return requirements


# Registry of company-specific parsers
COMPANY_PARSERS: Dict[str, CompanyParser] = {
    "blue origin": BlueOriginParser(),
    "boeing": BoeingParser(),
}


def get_parser(company_name: str) -> CompanyParser:
    """Get parser for company, or generic fallback."""
    normalized = company_name.lower().strip()
    return COMPANY_PARSERS.get(normalized, GenericParser())
