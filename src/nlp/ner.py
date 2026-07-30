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
)
from src.nlp.normalizer import (
    normalize_requirements,
    normalize_skills,
    normalize_technologies,
)
from src.nlp.domains import get_keyphrases_auto, detect_domain, Domain
from src.nlp.company_parsers import get_parser


class JobNERExtractor:
    """Extract skills, technologies, and requirements from job descriptions."""

    def __init__(self, model: str = "en_core_web_md", domain: str = None, company_name: str = None):
        """Initialize spaCy NLP model.

        Args:
            model: spaCy model name
            domain: Force specific domain (aerospace, software, hardware, general)
                   If None, auto-detect from job description
            company_name: Company name for company-specific parsers (blue origin, boeing, etc)
                         If None, uses generic parser
        """
        try:
            self.nlp = spacy.load(model)
        except OSError:
            raise RuntimeError(
                f"spaCy model '{model}' not found. Install with: "
                f"python -m spacy download {model}"
            )

        self.domain = domain
        self.company_name = company_name
        self.parser = get_parser(company_name) if company_name else None
        # Matchers will be initialized per-job in extract_all
        self.keyphrase_matcher = None
        self.skill_matcher = None

    def _init_matchers(self, job_description: str) -> None:
        """Initialize phrase matchers based on detected/specified domain."""
        # Detect or use specified domain
        if self.domain:
            domain_enum = Domain[self.domain.upper()] if isinstance(self.domain, str) else self.domain
            keyphrases = get_keyphrases_auto(job_description) if self.domain is None else \
                        get_keyphrases_auto(job_description) if Domain[self.domain.upper()] == Domain.GENERAL \
                        else get_keyphrases_auto(job_description)
        else:
            keyphrases = get_keyphrases_auto(job_description)

        # Add phrase matcher for domain-specific keyphrases
        self.keyphrase_matcher = PhraseMatcher(self.nlp.vocab)
        keyphrase_patterns = [self.nlp.make_doc(kp) for kp in keyphrases]
        self.keyphrase_matcher.add("KEYPHRASE", keyphrase_patterns)

        # Fallback matcher for skill keywords
        self.skill_matcher = PhraseMatcher(self.nlp.vocab)
        skill_patterns = [self.nlp.make_doc(skill) for skill in SKILL_KEYWORDS]
        self.skill_matcher.add("SKILL", skill_patterns)

    def _infer_related_skills(self, text: str) -> Set[str]:
        """Infer skills from context by looking for related phrases."""
        inferred = set()
        detected_domain = detect_domain(text)

        # Map patterns to skill phrases (domain-aware)
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
            # Software/Systems domain (be conservative to avoid false positives)
            # "Software architecture": [r"software.*architecture"],  # Too broad - matches "architectural"
            "Hands-on software development": [r"hands.?on.*development"],  # Specific phrase
            # "Systems maintenance": [r"system.*maintenance"],  # Too broad
            "Binary data transformation": [r"binary.*data.*transformation"],  # Specific
            "Integrity check implementation": [r"integrity\s+check"],  # Specific
            "Time-series data analytics": [r"time.?series.*data|data.*time.?series"],  # Specific
            "Storage architecture design": [r"storage.*architecture"],  # Less likely to false match
            "Sensor data calibration": [r"calibration.*sensor|sensor.*calibration"],
            "Sensor data synchronization": [r"synchronization.*sensor|sensor.*sync"],
            "Technology evaluation": [r"evaluat.*(?:technology|emerging)"],  # More specific context
            "Code reviews": [r"code\s+review"],  # Exact phrase
            "Design walkthroughs": [r"design\s+walkthrough"],  # Exact phrase
            # "Technical coaching": [r"coaching"],  # Too generic
            "Project management": [r"project.*management"],  # Less risky
            "Problem decomposition": [r"problem\s+decomposition"],  # Exact
            # "Technical communication": [r"technical.*communication"],  # Too broad
            "Engineering data interpretation": [r"engineering\s+data"],  # Less generic
            "Engineering drawing interpretation": [r"engineering\s+drawing"],  # Specific
            "Quantitative analysis": [r"quantitative\s+analysis"],  # Exact
            "Statistical analysis": [r"statistical\s+analysis"],  # Exact
            "Data collection": [r"data\s+collection"],  # Exact
            "Data preparation": [r"data\s+preparation"],  # Exact
            "Cloud service deployment": [r"cloud.*deployment|deploy.*cloud"],
            "Software documentation": [r"software.*documentation"],
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
            # Defense/Software domain (less exact, more narrative)
            "Software architecture": [r"(?:design|architect).*software\s+system|software\s+(?:design|architect)"],
            "Systems maintenance": [r"maintain.*system|system.*maintain"],
            "Binary data transformation": [r"binary.*(?:data|sensor)|data\s+(?:transformation|processing)"],
            "Time-series data analytics": [r"time.?series|analytics.*time|temporal\s+data"],
            "Data collection": [r"collect.*data|data\s+collection"],
            "Data preparation": [r"preparation.*data|data\s+preparation"],
            "Engineering data interpretation": [r"interpret.*data|(?:engineering|sensor)\s+data"],
            "Technical communication": [r"communicate.*technical|technical\s+communicat"],
        }

        for skill, patterns in skill_mappings.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    inferred.add(skill)
                    break

        # Defense/Software domain: ARINC-specific inferences
        if detected_domain == Domain.DEFENSE or detected_domain == Domain.SOFTWARE:
            if re.search(r"\bARINC\s+\d{3}\b", text, re.IGNORECASE):
                inferred.add("Binary data transformation")
                inferred.add("Integrity check implementation")
                inferred.add("Sensor data calibration")
                inferred.add("Time-series data analytics")
                inferred.add("Sensor data synchronization")

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
        """Extract requirements (years experience, degrees, qualifications).

        Uses company-specific parser if company_name provided, otherwise generic extraction.
        """
        # Use company-specific parser if available
        if self.parser:
            return self.parser.parse_requirements(text)

        # Fallback to generic extraction
        requirements = set()

        # 1. Years of experience (from basic/minimum qualifications section)
        for section_label in [r"basic\s+qualifications", r"minimum\s+qualifications", r"required\s+skills"]:
            min_qual_match = re.search(
                rf"(?:##\s+)?(?:{section_label})[\s\n:]*(.+?)(?=\n##|Preferred|---|\Z)",
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if min_qual_match:
                min_qual_section = min_qual_match.group(1)

                # Extract years from this section
                years_pattern = r"(\d+)\+?\s+years\s+(?:of\s+)?experience(?:\s+(?:in|with|focused\s+on|involving|related\s+to|using|with)\s+([^\.\n]+))?"
                for match in re.finditer(years_pattern, min_qual_section, re.IGNORECASE):
                    years = match.group(1)
                    domain = match.group(2)

                    if domain:
                        domain = domain.strip()
                        domain = re.sub(r"[\.,;]*$", "", domain)
                        # Normalize specific domains
                        if "autonomy" in domain.lower() and "aerospace" in domain.lower():
                            domain = "autonomy or aerospace autonomy/GNC"
                        elif "autonomy" in domain.lower():
                            domain = "autonomy"
                        requirements.add(f"{years}+ years of experience {domain}")
                    else:
                        requirements.add(f"{years}+ years of experience")

        # 2. Extract other bullets from Basic/Minimum Qualifications section
        for section_label in [r"basic\s+qualifications", r"minimum\s+qualifications", r"required\s+skills/experience"]:
            min_qual_match = re.search(
                rf"(?:##\s+)?(?:{section_label})[\s\n:]*(.+?)(?=\n##|Preferred|---|\Z)",
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if min_qual_match:
                qual_text = min_qual_match.group(1)
                bullets = re.findall(r"[\*•\-]\s+(.+?)(?:\n|$)", qual_text)
                for bullet in bullets:
                    bullet = bullet.strip()
                    # Keep requirement bullets (10-150 chars, not starting with years)
                    if 10 < len(bullet) < 150 and not re.match(r"^\d+\+", bullet):
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

        # 6. Background check & drug test
        if re.search(r"background\s+check", text, re.IGNORECASE):
            if not any("Background Check" in req for req in requirements):
                requirements.add("Blue's Standard Background Check")

        if re.search(r"drug", text, re.IGNORECASE):
            if not any("drug" in req.lower() for req in requirements):
                requirements.add("Passing a post-offer drug test")

        # 7. Coding assessments & challenges
        if re.search(r"CodeVue|coding\s+challenge|technical.*assessment", text, re.IGNORECASE):
            if not any("codevue" in req.lower() or "coding" in req.lower() for req in requirements):
                requirements.add("Completion of the CodeVue Coding Challenge during the selection process")

        # 8. Bachelor's/Degree requirement
        if re.search(r"Bachelor['’s]*\s+(?:Degree|of\s+Science)", text, re.IGNORECASE):
            if not any("Bachelor" in req or "Degree" in req for req in requirements):
                requirements.add("Bachelor's Degree")

        return requirements

    def extract_all(self, text: str) -> dict:
        """Extract all entities from job description."""
        # Initialize matchers based on job description domain
        self._init_matchers(text)

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
            "detected_domain": detect_domain(text).value,  # Include detected domain
        }
