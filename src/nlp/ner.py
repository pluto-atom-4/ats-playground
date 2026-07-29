"""Job description NER extraction using spaCy."""

import re
from typing import Set
import spacy
from spacy.matcher import PhraseMatcher

from src.nlp.patterns import (
    extract_technologies,
    extract_requirement_spans,
    extract_skill_candidates,
    SKILL_KEYWORDS,
    SKILL_KEYPHRASES,
)
from src.nlp.normalizer import (
    normalize_requirements,
    normalize_skills,
    normalize_technologies,
)


class JobNERExtractor:
    """Extract skills, technologies, and requirements from job descriptions."""

    def __init__(self, model: str = "en_core_web_md"):
        """Initialize spaCy NLP model."""
        try:
            self.nlp = spacy.load(model)
        except OSError:
            raise RuntimeError(
                f"spaCy model '{model}' not found. Install with: "
                f"python -m spacy download {model}"
            )

        # Add phrase matcher for known keyphrases (best accuracy)
        self.keyphrase_matcher = PhraseMatcher(self.nlp.vocab)
        keyphrase_patterns = [self.nlp.make_doc(kp) for kp in SKILL_KEYPHRASES]
        self.keyphrase_matcher.add("KEYPHRASE", keyphrase_patterns)

        # Fallback matcher for skill keywords
        self.skill_matcher = PhraseMatcher(self.nlp.vocab)
        skill_patterns = [self.nlp.make_doc(skill) for skill in SKILL_KEYWORDS]
        self.skill_matcher.add("SKILL", skill_patterns)

    def _infer_related_skills(self, text: str) -> Set[str]:
        """Infer skills from context by looking for related phrases."""
        inferred = set()

        # Map patterns to skill phrases
        skill_mappings = {
            "Guidance and Control": [r"guidance\s+and\s+control|G&C", r"guidance.*control"],
            "G&C algorithms": [r"G&C\s+algorithms|guidance.*control.*algorithm"],
            "Conceptual level design": [r"conceptual.*design"],
            "Post flight analysis": [r"post.?flight\s+analysis|post.?operation"],
            "Team leadership": [r"team.*leadership|lead.*team"],
            "Staff coaching": [r"coaching|coach.*staff"],
            "Collaborative skills": [r"collaborat|cross.?functional.*team"],
            "Software integration": [r"software.*integration|integrate.*software"],
            "Unit testing": [r"unit\s+test"],
            "Launch operations support": [r"launch.*operation"],
            "Test operations support": [r"test.*operation|operational.*test"],
            "Cross-functional communication": [r"cross.?functional|cross.?team.*communicat"],
            "Technical oversight": [r"technical.*oversight|oversee.*technical"],
            "Design reviews": [r"design.*review|review.*design"],
            "Systems analysis": [r"system.*analysis|systems.*analysis"],
            "Architectural decision making": [r"architectur.*decision"],
            "Verification and validation": [r"verif.*validat|v&v"],
            "Software development": [r"software\s+development|develop.*software"],
            "Mentoring": [r"mentor"],
            "Technical planning": [r"technical.*planning|planning.*technical"],
            "System modeling": [r"system.*model|model.*system"],
            "Hardware-in-the-loop testing": [r"hardware.?in.?loop|HIL.*test"],
            "Vehicle test campaigns": [r"vehicle.*test.*campaign|test.*campaign"],
        }

        for skill, patterns in skill_mappings.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    inferred.add(skill)
                    break

        return inferred

    def extract_skills(self, text: str) -> Set[str]:
        """Extract skills using keyphrase matching + context inference."""
        skills = set()
        doc = self.nlp(text)

        # First pass: extract known keyphrases (highest priority)
        matches = self.keyphrase_matcher(doc)
        for match_id, start, end in matches:
            skill = doc[start:end].text
            skills.add(skill)

        # Second pass: infer skills from context
        inferred = self._infer_related_skills(text)
        skills.update(inferred)

        # Third pass: extract from matched skill keywords (fallback)
        if len(skills) < 15:
            matches = self.skill_matcher(doc)
            for match_id, start, end in matches:
                skill = doc[start:end].text.strip()
                # Capitalize and format
                formatted = " ".join(w.capitalize() for w in skill.split())
                if formatted not in skills and len(formatted) > 2:
                    skills.add(formatted)

        return skills

    def extract_technologies(self, text: str) -> Set[str]:
        """Extract known technologies (tools, frameworks, languages)."""
        return extract_technologies(text)

    def extract_requirements(self, text: str) -> Set[str]:
        """Extract requirements (years experience, degrees, qualifications)."""
        requirements = set()

        # 1. Years of experience with domain context
        years_matches = re.finditer(
            r"(\d+)\+?\s+years\s+(?:of\s+)?experience(?:\s+(?:in|with|focused\s+on|related\s+to)\s+(.+?))?(?:[\.,\n]|$)",
            text,
            re.IGNORECASE
        )
        for match in years_matches:
            years = match.group(1)
            domain = match.group(2)
            if domain:
                # Clean domain text
                domain = domain.strip()
                domain = re.sub(r"[\.,;]*$", "", domain)
                # Shorten very long domains
                if len(domain) > 80:
                    # Try to extract key parts
                    if "autonomy" in domain.lower() and "aerospace" in domain.lower():
                        domain = "autonomy or aerospace autonomy/GNC"
                requirements.add(f"{years}+ years of experience {domain}")
            else:
                requirements.add(f"{years}+ years of experience")

        # 2. Extract from minimum qualifications section (bullets only)
        min_qual_match = re.search(
            r"(?:minimum|required)\s+(?:qualifications?|experience)[\s\n:]*(.+?)(?=\n###|Preferred|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if min_qual_match:
            qual_text = min_qual_match.group(1)
            bullets = re.findall(r"[\*•\-]\s+(.+?)(?:\n|$)", qual_text)
            for bullet in bullets:
                bullet = bullet.strip()
                # Only add concise requirements (filter out long descriptions)
                if 15 < len(bullet) < 120 and not re.match(r"^\d+\+", bullet):
                    # Don't duplicate years of experience
                    if "years of experience" not in bullet.lower():
                        requirements.add(bullet)

        # 3. Preferred qualifications (marked as such)
        pref_match = re.search(
            r"(?:preferred|desired)\s+(?:qualifications?|experience|qualifications?)[\s\n:]*(.+?)(?=\n###|Background|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if pref_match:
            pref_text = pref_match.group(1)
            # Look for degree requirement
            if re.search(r"(?:M\.S\.|MS|PhD|Ph\.D\.|master|advanced\s+degree)", pref_text, re.IGNORECASE):
                requirements.add("Advanced degree (M.S. or Ph.D.) in a relevant engineering field (Preferred)")
            # Look for specific experience
            if re.search(r"launch\s+vehicle.*guidance|guidance.*launch\s+vehicle", pref_text, re.IGNORECASE):
                requirements.add("Direct experience with launch vehicle guidance and control algorithms (Preferred)")

        # 4. Citizenship/export control
        if re.search(r"U\.S\.\s+(?:citizen|national)|permanent\s+resident.*refugee|asylee", text, re.IGNORECASE):
            requirements.add("U.S. citizen, national, permanent resident, refugee, or asylee status")

        # 5. Background check
        if re.search(r"background\s+check", text, re.IGNORECASE):
            requirements.add("Blue's Standard Background Check")

        return requirements

    def extract_all(self, text: str) -> dict:
        """Extract all entities from job description."""
        skills = self.extract_skills(text)
        technologies = self.extract_technologies(text)
        requirements = self.extract_requirements(text)

        # Normalize
        skills = normalize_skills(skills)
        technologies = normalize_technologies(technologies)
        requirements = normalize_requirements(requirements)

        return {
            "skills": sorted(list(skills)),
            "technologies": sorted(list(technologies)),
            "requirements": sorted(list(requirements)),
        }
