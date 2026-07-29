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

        # Map patterns to skill phrases (aerospace + software domains)
        skill_mappings = {
            # Aerospace domain
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
            "Design reviews": [r"design.*review|review.*design|code\s+review"],
            "Systems analysis": [r"system.*analysis|systems.*analysis"],
            "Architectural decision making": [r"architectur.*decision"],
            "Verification and validation": [r"verif.*validat|v&v"],
            "Software development": [r"software\s+development|develop.*software"],
            "Mentoring": [r"mentor"],
            "Technical planning": [r"technical.*planning|planning.*technical"],
            "System modeling": [r"system.*model|model.*system"],
            "Hardware-in-the-loop testing": [r"hardware.?in.?loop|HIL.*test"],
            "Vehicle test campaigns": [r"vehicle.*test.*campaign|test.*campaign"],
            # Software/Systems domain
            "Software architecture": [r"software.*architecture|architect.*software"],
            "Hands-on software development": [r"hands.?on.*development|development.*hands.?on"],
            "Systems maintenance": [r"system.*maintenance|maintain.*system"],
            "Binary data transformation": [r"binary.*data|data.*transformation"],
            "Integrity check implementation": [r"integrity.*check|check.*integrity"],
            "Time-series data analytics": [r"time.?series|analytics.*time"],
            "Storage architecture design": [r"storage.*architecture|architecture.*storage"],
            "Sensor data calibration": [r"calibration.*sensor|sensor.*calibration"],
            "Sensor data synchronization": [r"synchronization.*sensor|sensor.*sync"],
            "Technology evaluation": [r"evaluat.*technology|technology.*evaluat"],
            "Code reviews": [r"code.*review|review.*code"],
            "Design walkthroughs": [r"design.*walkthrough|walkthrough"],
            "Technical coaching": [r"coaching|coach.*engineer"],
            "Project management": [r"project.*management|manage.*project"],
            "Problem decomposition": [r"decomposition|decompose.*problem"],
            "Technical communication": [r"technical.*communication|communicat.*technical"],
            "Engineering data interpretation": [r"engineering.*data|interpret.*data"],
            "Engineering drawing interpretation": [r"engineering.*drawing"],
            "Quantitative analysis": [r"quantitative.*analysis"],
            "Statistical analysis": [r"statistical.*analysis|statistical"],
            "Data collection": [r"data.*collection|collect.*data"],
            "Data preparation": [r"data.*preparation|prepare.*data"],
            "Cloud service deployment": [r"cloud.*deployment|deploy.*cloud"],
            "Software documentation": [r"software.*documentation|document.*software"],
            "Software design": [r"software.*design|design.*software"],
            "System design": [r"system.*design|design.*system"],
            "Component design": [r"component.*design"],
            "API design": [r"API.*design|design.*API"],
            "Database design": [r"database.*design"],
            "Architecture review": [r"architecture.*review"],
            "Code quality assurance": [r"code.*quality|quality.*code"],
            "Testing strategy": [r"testing.*strategy|strategy.*test"],
            "Integration testing": [r"integration.*test"],
            "Performance testing": [r"performance.*test"],
            "Security testing": [r"security.*test"],
            # Note: These are often in "Preferred" or context; be conservative
            # "Agile development": [r"agile.*development"],  # Too broad
            # "DevOps practices": [r"DevOps|devops"],  # Often preference
            # "CI/CD implementation": [r"CI/CD|CI.?CD"],  # Often preference
            "Deployment automation": [r"deployment.*automat|automat.*deploy"],
            "Infrastructure management": [r"infrastructure.*management"],
            "Configuration management": [r"configuration.*management|SCM"],
            "Requirements analysis": [r"requirement.*analysis"],
            "Stakeholder management": [r"stakeholder.*management"],
            "Technical documentation": [r"technical.*documentation"],
            "Knowledge transfer": [r"knowledge.*transfer"],
            # Removed: too generic, appear in preferences not skills
            # "Best practices implementation": [r"best.*practice"],
            # "Standards compliance": [r"standard.*compliance"],
            # "Process improvement": [r"process.*improvement"],
            # "Deployment automation": [r"deployment.*automat"],
            # "Software design": [r"software.*design"],
            # "System design": [r"system.*design"],
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

        # 1. Years of experience (from minimum qualifications section only)
        min_qual_match = re.search(
            r"(?:##\s+)?(?:minimum|required)\s+(?:qualifications?|experience)[\s\n:]*(.+?)(?=\n##|Preferred|---|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if min_qual_match:
            min_qual_section = min_qual_match.group(1)

            # Extract years from this section only
            years_pattern = r"(\d+)\+?\s+years\s+(?:of\s+)?experience(?:\s+(?:in|with|focused\s+on|involving|related\s+to)\s+([^\.\n]+))?"
            for match in re.finditer(years_pattern, min_qual_section, re.IGNORECASE):
                years = match.group(1)
                domain = match.group(2)

                if domain:
                    domain = domain.strip()
                    # Remove trailing punctuation
                    domain = re.sub(r"[\.,;]*$", "", domain)
                    # Normalize specific domains
                    if "autonomy" in domain.lower() and "aerospace" in domain.lower():
                        domain = "autonomy or aerospace autonomy/GNC"
                    elif "autonomy" in domain.lower():
                        domain = "autonomy"
                    requirements.add(f"{years}+ years of experience in {domain}")
                else:
                    requirements.add(f"{years}+ years of experience")

        # 2. Extract from "Minimum Qualifications" section
        min_qual_match = re.search(
            r"(?:##\s+)?(?:minimum|required)\s+(?:qualifications?|experience)[\s\n:]*(.+?)(?=\n##|Preferred|---|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if min_qual_match:
            qual_text = min_qual_match.group(1)
            bullets = re.findall(r"[\*•\-]\s+(.+?)(?:\n|$)", qual_text)
            for bullet in bullets:
                bullet = bullet.strip()
                # Skip very long bullets (likely responsibilities, not requirements)
                if 15 < len(bullet) < 130 and not re.match(r"^\d+\+", bullet):
                    # Don't duplicate years of experience
                    if "years of experience" not in bullet.lower():
                        requirements.add(bullet)

        # 3. Extract from "Preferred Qualifications" section
        pref_match = re.search(
            r"(?:##\s+)?(?:preferred|desired)\s+(?:qualifications?|experience)[\s\n:]*(.+?)(?=\n##|Background|---|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if pref_match:
            pref_text = pref_match.group(1)
            pref_bullets = re.findall(r"[\*•\-]\s+(.+?)(?:\n|$)", pref_text)
            for bullet in pref_bullets:
                bullet = bullet.strip()
                if 10 < len(bullet) < 150:
                    # Add (Preferred) tag if not already there
                    if "(Preferred)" not in bullet:
                        bullet = f"{bullet} (Preferred)"
                    requirements.add(bullet)

        # 4. Look for specific requirement patterns in text
        # Advanced degree pattern
        advanced_degree_match = re.search(
            r"(?:M\.S\.|MS|Master|PhD|Ph\.D\.)\s+(?:or|\/)\s+(?:PhD|Ph\.D\.)",
            text,
            re.IGNORECASE
        )
        if advanced_degree_match:
            # Check if marked as preferred
            context = text[max(0, advanced_degree_match.start() - 100):advanced_degree_match.end() + 100]
            if "preferred" in context.lower():
                requirements.add("Advanced degree (M.S. or Ph.D.) in a relevant engineering field (Preferred)")
            else:
                # If in preferred section, don't add duplicate
                if not any("Advanced degree" in req for req in requirements):
                    requirements.add("Advanced degree (M.S. or Ph.D.) in a relevant engineering field")

        # 5. Citizenship/export control
        if re.search(r"U\.S\.\s+(?:citizen|national)|permanent\s+resident", text, re.IGNORECASE):
            if not any("U.S. citizen" in req for req in requirements):
                requirements.add("U.S. citizen, national, permanent resident, refugee, or asylee status")

        # 6. Background check
        if re.search(r"background\s+check", text, re.IGNORECASE):
            if not any("Background Check" in req for req in requirements):
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
