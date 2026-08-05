"""Job description NER extraction using spaCy."""

import re
from typing import Any, Dict, Set

import spacy
from spacy.matcher import PhraseMatcher

from src.nlp.company_parsers import get_parser
from src.nlp.confidence import (
    ExtractionMethod,
    average_confidence,
    get_confidence,
)
from src.nlp.domains import Domain, detect_domain, get_keyphrases_auto
from src.nlp.narrative import NarrativeRequirementExtractor
from src.nlp.normalizer import (
    normalize_requirements,
    normalize_skills,
    normalize_technologies,
)
from src.nlp.patterns import (
    SKILL_KEYWORDS,
    extract_technologies,
)


class JobNERExtractor:
    """Extract skills, technologies, and requirements from job descriptions."""

    def __init__(self, model: str = "en_core_web_md", company_name: str | None = None):
        """Initialize spaCy NLP model.

        Args:
            model: spaCy model name
            company_name: Company name for company-specific parsers (blue origin, boeing, etc)
                         If None, uses generic parser
        """
        try:
            self.nlp = spacy.load(model)
        except OSError as err:
            raise RuntimeError(
                f"spaCy model '{model}' not found. Install with: python -m spacy download {model}"
            ) from err

        self.company_name = company_name
        self.parser = get_parser(company_name) if company_name else None
        self.narrative_extractor = NarrativeRequirementExtractor(self.nlp)
        # Pre-compile matchers for reuse (not recreated per-job)
        self.keyphrase_matcher = PhraseMatcher(self.nlp.vocab)
        self.skill_matcher = PhraseMatcher(self.nlp.vocab)

    def _init_matchers(self, job_description: str) -> None:
        """Load keyphrases and patterns into pre-initialized matchers."""
        # Get keyphrases (domain parameter is not currently used for filtering)
        keyphrases = get_keyphrases_auto(job_description)

        # Clear and re-add patterns for domain-specific keyphrases
        try:
            self.keyphrase_matcher.remove("KEYPHRASE")
        except (ValueError, KeyError):
            pass  # Pattern doesn't exist yet
        keyphrase_patterns = [self.nlp.make_doc(kp) for kp in keyphrases]
        if keyphrase_patterns:
            self.keyphrase_matcher.add("KEYPHRASE", keyphrase_patterns)

        # Clear and re-add patterns for skill keywords
        try:
            self.skill_matcher.remove("SKILL")
        except (ValueError, KeyError):
            pass  # Pattern doesn't exist yet
        skill_patterns = [self.nlp.make_doc(skill) for skill in SKILL_KEYWORDS]
        if skill_patterns:
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

    def extract_skills_with_confidence(self, text: str) -> Dict[str, tuple[str, float, ExtractionMethod]]:
        """Extract skills with confidence scores.

        Returns:
            Dict mapping skill -> (skill, confidence, method)
        """
        skills_with_conf = {}
        doc = self.nlp(text)

        # First pass: keyphrase exact match (high confidence)
        matches = self.keyphrase_matcher(doc)
        for _match_id, start, end in matches:
            skill = doc[start:end].text
            if skill not in skills_with_conf:
                conf = get_confidence(ExtractionMethod.KEYPHRASE_EXACT)
                skills_with_conf[skill] = (skill, conf, ExtractionMethod.KEYPHRASE_EXACT)

        # Second pass: infer from context (medium confidence)
        inferred = self._infer_related_skills(text)
        for skill in inferred:
            if skill not in skills_with_conf:
                conf = get_confidence(ExtractionMethod.CONTEXT_INFERRED)
                skills_with_conf[skill] = (skill, conf, ExtractionMethod.CONTEXT_INFERRED)

        # Third pass: skill keyword fallback (low confidence)
        if len(skills_with_conf) < 15:
            matches = self.skill_matcher(doc)
            for _match_id, start, end in matches:
                skill = doc[start:end].text.strip()
                formatted = " ".join(w.capitalize() for w in skill.split())
                if formatted not in skills_with_conf and len(formatted) > 2:
                    conf = get_confidence(ExtractionMethod.SKILL_KEYWORD)
                    skills_with_conf[formatted] = (formatted, conf, ExtractionMethod.SKILL_KEYWORD)

        return skills_with_conf

    def extract_skills(self, text: str) -> Set[str]:
        """Extract skills using keyphrase matching + context inference."""
        skills_with_conf = self.extract_skills_with_confidence(text)
        return set(skills_with_conf.keys())

    def extract_technologies_with_confidence(self, text: str) -> Dict[str, tuple[str, float, ExtractionMethod]]:
        """Extract technologies with confidence scores.

        Returns:
            Dict mapping tech -> (tech, confidence, method)
        """
        techs = extract_technologies(text)
        # All tech extractions use pattern matching
        return {
            tech: (tech, get_confidence(ExtractionMethod.PATTERN_MATCH), ExtractionMethod.PATTERN_MATCH)
            for tech in techs
        }

    def extract_technologies(self, text: str) -> Set[str]:
        """Extract known technologies (tools, frameworks, languages)."""
        return extract_technologies(text)

    def extract_narrative_requirements(self, text: str) -> Set[str]:
        """Extract requirements from narrative/prose text."""
        return self.narrative_extractor.extract_narrative_requirements(text)

    def extract_narrative_skills(self, text: str) -> Set[str]:
        """Extract skills mentioned in narrative prose."""
        return self.narrative_extractor.extract_skill_requirements(text)

    def extract_narrative_qualifications(self, text: str) -> Set[str]:
        """Extract degree/certification requirements from narrative."""
        return self.narrative_extractor.extract_qualification_requirements(text)

    def _extract_structured_requirements(self, text: str) -> Dict[str, tuple[str, float, ExtractionMethod]]:
        """Extract structured requirements from company parser.

        Args:
            text: Job description text

        Returns:
            Dict mapping requirement -> (requirement, confidence, method)
        """
        requirements_with_conf: Dict[str, tuple[str, float, ExtractionMethod]] = {}
        if not self.parser:
            return requirements_with_conf
        reqs = self.parser.parse_requirements(text)

        # Structured bullet requirements from company parser = high confidence
        for req in reqs:
            if req not in requirements_with_conf:
                # Determine if this is from a structured section or pattern
                is_structured = (
                    any(
                        pattern in req.lower()
                        for pattern in ["bachelor", "clearance", "citizenship", "drug", "codevue", "u.s. person"]
                    )
                    and len(req) > 20
                )

                if is_structured:
                    method = ExtractionMethod.STRUCTURED_BULLET
                    conf = get_confidence(ExtractionMethod.STRUCTURED_BULLET)
                else:
                    method = ExtractionMethod.PATTERN_MATCH
                    conf = get_confidence(ExtractionMethod.PATTERN_MATCH)
                requirements_with_conf[req] = (req, conf, method)

        return requirements_with_conf

    def _extract_narrative_and_merge(
        self, text: str, requirements_with_conf: Dict[str, tuple[str, float, ExtractionMethod]]
    ) -> None:
        """Extract narrative requirements and merge into requirements dict.

        Args:
            text: Job description text
            requirements_with_conf: Dict to merge narrative requirements into (mutated in place)
        """
        narrative_reqs = self.extract_narrative_requirements(text)

        for req in narrative_reqs:
            # Only add if not already covered by structured extraction
            # Use word boundary check instead of substring to avoid false positives
            # (e.g., 'C' != 'C++', 'Python' != 'Python3')
            if self._is_duplicate_requirement(req, requirements_with_conf):
                continue

            # Lower confidence for narrative to account for possible false positives
            requirements_with_conf[req] = (req, 0.75, ExtractionMethod.FALLBACK)

    def _is_duplicate_requirement(
        self, req: str, requirements_with_conf: Dict[str, tuple[str, float, ExtractionMethod]]
    ) -> bool:
        """Check if requirement is already in the dict after normalization.

        Args:
            req: Requirement to check
            requirements_with_conf: Existing requirements dict

        Returns:
            True if duplicate found, False otherwise
        """
        req_lower = req.lower()
        for existing in requirements_with_conf:
            existing_lower = existing.lower()
            # Check if they're very similar (word boundary or 80%+ match)
            # For now, just check exact match after normalization
            if req_lower == existing_lower:
                return True
        return False

    def extract_requirements_with_confidence(
        self, text: str, include_narrative: bool = True
    ) -> Dict[str, tuple[str, float, ExtractionMethod]]:
        """Extract requirements with confidence scores.

        Args:
            text: Job description text
            include_narrative: Also extract from narrative prose (default: True)

        Returns:
            Dict mapping requirement -> (requirement, confidence, method)
        """
        # Use company-specific parser if available
        if self.parser:
            requirements_with_conf = self._extract_structured_requirements(text)

            # Add narrative requirements from prose (medium confidence)
            if include_narrative:
                self._extract_narrative_and_merge(text, requirements_with_conf)

            return requirements_with_conf

        # Fallback to generic extraction (lower confidence)
        fallback_requirements = self._extract_requirements_fallback(text)
        requirements_with_conf = self._build_fallback_requirements(fallback_requirements)

        return requirements_with_conf

    def _build_fallback_requirements(self, requirements: Set[str]) -> Dict[str, tuple[str, float, ExtractionMethod]]:
        """Build requirements dict from fallback extraction.

        Args:
            requirements: Set of requirements to build dict from

        Returns:
            Dict mapping requirement -> (requirement, confidence, method)
        """
        result: Dict[str, tuple[str, float, ExtractionMethod]] = {}
        for req in requirements:
            if req not in result:
                conf = get_confidence(ExtractionMethod.FALLBACK)
                result[req] = (req, conf, ExtractionMethod.FALLBACK)
        return result

    def _extract_years_from_section(self, text: str, section_label: str) -> Set[str]:
        """Extract years of experience from a section."""
        years_reqs: Set[str] = set()
        min_qual_match = re.search(
            rf"(?:##\s+)?(?:{section_label})[\s\n:]*(.+?)(?=\n##|Preferred|---|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not min_qual_match:
            return years_reqs

        min_qual_section = min_qual_match.group(1)
        years_pattern = (
            r"(\d+)\+?\s+years\s+(?:of\s+)?experience"
            r"(?:\s+(?:in|with|focused\s+on|involving|related\s+to|using|with)\s+([^\.\n]+))?"
        )
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
                years_reqs.add(f"{years}+ years of experience {domain}")
            else:
                years_reqs.add(f"{years}+ years of experience")

        return years_reqs

    def _extract_qualification_bullets(self, text: str, section_label: str) -> Set[str]:
        """Extract bullet points from a qualifications section."""
        bullets_reqs: Set[str] = set()
        min_qual_match = re.search(
            rf"(?:##\s+)?(?:{section_label})[\s\n:]*(.+?)(?=\n##|Preferred|---|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not min_qual_match:
            return bullets_reqs

        qual_text = min_qual_match.group(1)
        bullets = re.findall(r"[\*•\-]\s+(.+?)(?:\n|$)", qual_text)
        for bullet in bullets:
            bullet = bullet.strip()
            # Keep requirement bullets (10-150 chars, not starting with years)
            if 10 < len(bullet) < 150 and not re.match(r"^\d+\+", bullet):
                # Don’t duplicate years of experience
                if "years of experience" not in bullet.lower():
                    bullets_reqs.add(bullet)

        return bullets_reqs

    def _extract_preferred_qualifications(self, text: str) -> Set[str]:
        """Extract from Preferred Qualifications section."""
        pref_reqs: Set[str] = set()
        pref_match = re.search(
            r"(?:##\s+)?(?:preferred|desired)\s+(?:qualifications?|experience)[\s\n:]*(.+?)(?=\n##|Background|---|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not pref_match:
            return pref_reqs

        pref_text = pref_match.group(1)
        pref_bullets = re.findall(r"[\*•\-]\s+(.+?)(?:\n|$)", pref_text)
        for bullet in pref_bullets:
            bullet = bullet.strip()
            if 10 < len(bullet) < 150:
                # Add (Preferred) tag if not already there
                if "(Preferred)" not in bullet:
                    bullet = f"{bullet} (Preferred)"
                pref_reqs.add(bullet)

        return pref_reqs

    def _extract_advanced_degree(self, text: str) -> Set[str]:
        """Extract advanced degree requirements."""
        degree_reqs = set()
        advanced_degree_match = re.search(
            r"(?:M\.S\.|MS|Master|PhD|Ph\.D\.)\s+(?:or|\/)\s+(?:PhD|Ph\.D\.)", text, re.IGNORECASE
        )
        if advanced_degree_match:
            # Check if marked as preferred
            context = text[max(0, advanced_degree_match.start() - 100) : advanced_degree_match.end() + 100]
            if "preferred" in context.lower():
                degree_reqs.add("Advanced degree (M.S. or Ph.D.) in a relevant engineering field (Preferred)")
            else:
                # If in preferred section, don’t add duplicate
                if not any("Advanced degree" in req for req in degree_reqs):
                    degree_reqs.add("Advanced degree (M.S. or Ph.D.) in a relevant engineering field")

        return degree_reqs

    def _extract_citizenship_requirement(self, text: str, existing_reqs: Set[str]) -> Set[str]:
        """Extract citizenship/export control requirements."""
        citizen_reqs = set()
        if re.search(r"U\.S\.\s+(?:citizen|national)|permanent\s+resident", text, re.IGNORECASE):
            if not any("U.S. citizen" in req for req in existing_reqs):
                citizen_reqs.add("U.S. citizen, national, permanent resident, refugee, or asylee status")

        return citizen_reqs

    def _extract_background_check(self, text: str, existing_reqs: Set[str]) -> Set[str]:
        """Extract background check and drug test requirements."""
        bg_reqs = set()
        if re.search(r"background\s+check", text, re.IGNORECASE):
            if not any("Background Check" in req for req in existing_reqs):
                bg_reqs.add("Blue’s Standard Background Check")

        if re.search(r"drug", text, re.IGNORECASE):
            if not any("drug" in req.lower() for req in existing_reqs):
                bg_reqs.add("Passing a post-offer drug test")

        return bg_reqs

    def _extract_coding_assessment(self, text: str, existing_reqs: Set[str]) -> Set[str]:
        """Extract coding assessment requirements."""
        coding_reqs = set()
        if re.search(r"CodeVue|coding\s+challenge|technical.*assessment", text, re.IGNORECASE):
            if not any("codevue" in req.lower() or "coding" in req.lower() for req in existing_reqs):
                coding_reqs.add("Completion of the CodeVue Coding Challenge during the selection process")

        return coding_reqs

    def _extract_bachelors_degree(self, text: str, existing_reqs: Set[str]) -> Set[str]:
        """Extract Bachelor’s degree requirements."""
        bs_reqs = set()
        if re.search(r"Bachelor[‘’s]*\s+(?:Degree|of\s+Science)", text, re.IGNORECASE):
            if not any("Bachelor" in req or "Degree" in req for req in existing_reqs):
                bs_reqs.add("Bachelor’s Degree")

        return bs_reqs

    def _extract_requirements_fallback(self, text: str) -> Set[str]:
        """Generic requirement extraction fallback."""
        requirements = set()

        # 1. Years of experience (from basic/minimum qualifications section)
        for section_label in [r"basic\s+qualifications", r"minimum\s+qualifications", r"required\s+skills"]:
            requirements.update(self._extract_years_from_section(text, section_label))

        # 2. Extract other bullets from Basic/Minimum Qualifications section
        for section_label in [r"basic\s+qualifications", r"minimum\s+qualifications", r"required\s+skills/experience"]:
            requirements.update(self._extract_qualification_bullets(text, section_label))

        # 3. Extract from "Preferred Qualifications" section
        requirements.update(self._extract_preferred_qualifications(text))

        # 4. Extract advanced degree requirements
        requirements.update(self._extract_advanced_degree(text))

        # 5. Extract citizenship/export control
        requirements.update(self._extract_citizenship_requirement(text, requirements))

        # 6. Extract background check & drug test
        requirements.update(self._extract_background_check(text, requirements))

        # 7. Extract coding assessments & challenges
        requirements.update(self._extract_coding_assessment(text, requirements))

        # 8. Extract Bachelor’s degree requirement
        requirements.update(self._extract_bachelors_degree(text, requirements))

        return requirements

    def extract_requirements(self, text: str) -> Set[str]:
        """Extract requirements (backward compatibility).

        Returns set of requirement strings. Use extract_requirements_with_confidence
        for confidence scores.
        """
        reqs_with_conf = self.extract_requirements_with_confidence(text)
        return set(reqs_with_conf.keys())

    def extract_all_with_confidence(self, text: str) -> dict[str, Any]:
        """Extract all entities with confidence scores."""
        # Initialize matchers based on job description domain
        self._init_matchers(text)

        skills_with_conf = self.extract_skills_with_confidence(text)
        techs_with_conf = self.extract_technologies_with_confidence(text)
        reqs_with_conf = self.extract_requirements_with_confidence(text)

        # Extract just values for normalization
        skills = set(skills_with_conf.keys())
        techs = set(techs_with_conf.keys())
        reqs = set(reqs_with_conf.keys())

        # Normalize
        skills = normalize_skills(skills)
        techs = normalize_technologies(techs)
        reqs = normalize_requirements(reqs)

        # Build result with confidence scores
        def build_confident_list(
            values: set[str], conf_dict: Dict[str, tuple[str, float, ExtractionMethod]]
        ) -> list[dict[str, float | str]]:
            """Build list of dicts with value and confidence."""
            result: list[dict[str, float | str]] = []
            for val in sorted(values):
                # Find confidence from original dict (before normalization)
                # For now, use average confidence from matches
                val_lower = val.lower()
                matching_confs = [
                    conf_dict.get(v, (v, 0.5, None))[1]
                    for v in conf_dict
                    if val_lower in v.lower() or v.lower() in val_lower
                ]
                avg_conf = sum(matching_confs) / len(matching_confs) if matching_confs else 0.5
                result.append({"value": val, "confidence": round(avg_conf, 2)})
            return result

        return {
            "skills": build_confident_list(skills, skills_with_conf),
            "technologies": build_confident_list(techs, techs_with_conf),
            "requirements": build_confident_list(reqs, reqs_with_conf),
            "detected_domain": detect_domain(text).value,
            "metrics": {
                "avg_skills_confidence": round(average_confidence(build_confident_list(skills, skills_with_conf)), 2),
                "avg_tech_confidence": round(average_confidence(build_confident_list(techs, techs_with_conf)), 2),
                "avg_req_confidence": round(average_confidence(build_confident_list(reqs, reqs_with_conf)), 2),
            },
        }

    def extract_all(self, text: str) -> dict[str, Any]:
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
            "skills": sorted(skills),
            "technologies": sorted(technologies),
            "requirements": sorted(requirements),
            "detected_domain": detect_domain(text).value,
        }
