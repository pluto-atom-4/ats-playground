"""NLP preprocessing for job postings using spaCy."""

import logging
import re
from typing import Any, List, Optional, Set, Tuple

import spacy
from spacy.language import Language

from src.tokenization.keywords import get_all_keywords
from src.tokenization.soft_skills import get_all_soft_skills
from src.tokenization.technical_compounds import is_technical_compound

logger = logging.getLogger(__name__)


class Preprocessor:
    """Preprocess text using spaCy for NLP tasks."""

    def __init__(self, model: str = "en_core_web_md"):
        """Initialize preprocessor with spaCy model.

        Args:
            model: spaCy model name (e.g., en_core_web_md)
        """
        self.model_name = model
        self.nlp: Optional[Language] = None
        self._load_model()

    def _load_model(self) -> None:
        """Load spaCy model with error handling.

        Raises:
            OSError: If model cannot be loaded or is not installed.
        """
        try:
            logger.info(f"Loading spaCy model: {self.model_name}")
            self.nlp = spacy.load(self.model_name)
            logger.info(f"Successfully loaded spaCy model: {self.model_name}")
        except OSError as e:
            logger.error(
                f"Failed to load spaCy model '{self.model_name}': {e}. "
                "Ensure it's installed: python -m spacy download en_core_web_md"
            )
            raise

    def segment_sentences(self, text: str) -> List[str]:
        """Split text into sentences using spaCy sentence segmentation.

        Handles edge cases: abbreviations (Dr., Inc.), multiple punctuation.

        Args:
            text: Input text to segment

        Returns:
            List of sentence strings
        """
        if not self.nlp:
            logger.warning("spaCy model not loaded, returning empty list")
            return []

        if not text or not text.strip():
            return []

        try:
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents]
            logger.debug(f"Segmented text into {len(sentences)} sentences")
            return sentences
        except Exception as e:
            logger.error(f"Error segmenting sentences: {e}")
            return []

    def extract_entities(self, text: str) -> Tuple[List[str], List[str], List[str]]:
        """Extract named entities (skills, technologies, requirements).

        Phase 1: Smart filtering (section extraction → boilerplate removal → entity filtering)
        Uses spaCy NER for named entities and POS/DEP tagging for skills/tech.

        Args:
            text: Input text to extract entities from

        Returns:
            Tuple of (skills, technologies, requirements) as unique strings
        """
        if not self.nlp:
            logger.warning("spaCy model not loaded, returning empty lists")
            return [], [], []

        if not text or not text.strip():
            return [], [], []

        skills: set[str] = set()
        technologies: set[str] = set()
        requirements: set[str] = set()

        try:
            # Phase 10: Check if text is markdown
            is_md = self._is_markdown(text)

            if is_md:
                logger.debug("Text is markdown format, using entity-aware section extraction")
                # Use section-based method for intelligent extraction
                md_skills, md_technologies, md_requirements = self._extract_entities_by_section(text)
                skills.update(md_skills)
                technologies.update(md_technologies)
                requirements.update(md_requirements)

                # Use full text for additional extraction
                text_to_clean = text
            else:
                # Phase 1: Smart filtering pipeline
                # 1. Extract job section (ignore boilerplate sections)
                # Fallback to original text if no job section found
                job_section = self._extract_job_section(text)
                text_to_clean = job_section if job_section.strip() else text

            # 2. Remove boilerplate (salary, legal, location metadata)
            cleaned_text = self._remove_boilerplate(text_to_clean)

            # 3. Extract entities from cleaned text
            doc = self.nlp(cleaned_text)
            tech_keywords = self._get_tech_keywords()

            # Extract from NER (named entities)
            self._extract_from_ner(doc, tech_keywords, technologies, requirements)

            # Extract from POS tags and noun compounds
            self._extract_from_tokens(doc, tech_keywords, skills, technologies)

            # Extract soft skills from text
            soft_skills_set: set[str] = set()
            self._extract_soft_skills(doc, soft_skills_set)

            # Reclassify technical compounds (Phase 4)
            # Move compound phrases from skills to technologies
            skills_list = list(skills) + list(soft_skills_set)
            reclassified_skills: list[str] = []
            for skill in skills_list:
                if is_technical_compound(skill):
                    technologies.add(skill)
                else:
                    reclassified_skills.append(skill)

            # 5. Filter entities (remove noise, duplicates, short fragments)
            skills = set(self._filter_entities(reclassified_skills, entity_type="skills"))
            technologies = set(self._filter_entities(list(technologies), entity_type="technologies"))
            requirements = set(self._filter_entities(list(requirements), entity_type="requirements"))

            logger.debug(
                f"Extracted {len(skills)} skills, "
                f"{len(technologies)} technologies, "
                f"{len(requirements)} requirements (Phase 1 filtering applied)"
            )

            return (
                sorted(skills),
                sorted(technologies),
                sorted(requirements),
            )

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return [], [], []

    @staticmethod
    def _get_tech_keywords() -> set[str]:
        """Get technology keywords from centralized keywords module.

        Returns:
            Set of 86+ technology keywords across all categories
        """
        return get_all_keywords()

    @staticmethod
    def _extract_from_ner(
        doc: Any, tech_keywords: Set[str], technologies: Set[str], requirements: Set[str]
    ) -> None:
        """Extract entities from named entity recognition."""
        for ent in doc.ents:
            entity_text = ent.text.strip()
            if not entity_text or ent.label_ not in ("PRODUCT", "ORG"):
                continue

            if any(
                keyword in entity_text.lower() for keyword in tech_keywords
            ):
                technologies.add(entity_text)
            else:
                requirements.add(entity_text)

    @staticmethod
    def _extract_from_tokens(
        doc: Any, tech_keywords: Set[str], skills: Set[str], technologies: Set[str]
    ) -> None:
        """Extract skills and tech from tokens."""
        exclude_skills = {"senior", "junior", "required", "optional", "available"}

        for token in doc:
            token_text = token.text.strip()
            if not token_text:
                continue

            # Check if token matches tech keywords
            if token_text.lower() in tech_keywords:
                technologies.add(token_text)
            elif token.lemma_.lower() in tech_keywords:
                technologies.add(token.text)

            # Extract noun compounds as skills
            if (
                token.pos_ in ("NOUN", "PROPN")
                and token.dep_ in ("compound", "nmod", "attr")
                and len(token_text) > 3
            ):
                parent = token.head
                if parent.pos_ in ("NOUN", "PROPN"):
                    phrase = " ".join(
                        child.text
                        for child in doc
                        if child.head == parent or child == parent
                    )
                    if len(phrase) > 3 and "job" not in phrase.lower():
                        skills.add(phrase)

            # Extract adjectives
            if token.pos_ == "ADJ" and len(token_text) > 4:
                if token_text.lower() not in exclude_skills:
                    skills.add(token_text)

    def remove_stopwords(self, text: str) -> str:
        """Remove common English stopwords while preserving important terms.

        Uses spaCy's built-in stopwords list. Preserves technical terms
        and important entities.

        Args:
            text: Input text

        Returns:
            Text with stopwords removed
        """
        if not self.nlp:
            logger.warning("spaCy model not loaded, returning original text")
            return text

        if not text or not text.strip():
            return ""

        try:
            doc = self.nlp(text)

            # Terms to preserve (never remove as stopwords)
            preserve_terms = {
                "require",
                "required",
                "must",
                "should",
                "will",
                "ability",
                "experience",
                "skill",
                "knowledge",
                "understanding",
            }

            filtered_tokens = []
            for token in doc:
                # Keep if:
                # 1. Not a stopword
                # 2. Is a stopword but in preserve list
                # 3. Is named entity
                # 4. Is punctuation (keep for structure)
                if (
                    not token.is_stop
                    or token.lemma_.lower() in preserve_terms
                    or token.ent_type_
                    or token.is_punct
                ):
                    filtered_tokens.append(token.text)

            result = " ".join(filtered_tokens).strip()
            logger.debug(
                f"Removed stopwords: {len(doc)} tokens → {len(filtered_tokens)} tokens"
            )
            return result

        except Exception as e:
            logger.error(f"Error removing stopwords: {e}")
            return text

    def _extract_job_section(self, text: str) -> str:
        """Extract job requirement sections, ignore boilerplate.

        Returns text from recognized job sections, stops at legal disclaimers.
        Returns empty string if no job section found (fallback to original text).
        """
        if not text:
            return ""

        import re

        # Job requirement section headers (in priority order)
        # Match headers that are followed by colon or newline (to avoid matching mid-sentence)
        job_section_headers = [
            (
                r"(?i)(qualifications|requirements|what we're looking for|what we need|"
                r"what you'll need|must-have|essential|desired qualifications)(?:\s*[:|\n])"
            ),
            (
                r"(?i)(responsibilities|what you'll do|your role|what you will|"
                r"primary responsibilities)(?:\s*[:|\n])"
            ),
            r"(?i)(skills|technical skills|core skills|desired skills)(?:\s*[:|\n])",
        ]

        # Cutoff markers (stop extraction after these)
        cutoff_markers = [
            "equal opportunity",
            "affirmative action",
            "background check",
            "export control",
            "compliance",
            "how to apply",
            "apply now",
            "benefits",
            "compensation",
        ]

        # Find first job section marker
        first_match = None
        for pattern in job_section_headers:
            match = re.search(pattern, text)
            if match and (first_match is None or match.start() < first_match.start()):
                first_match = match

        # If no formal job section found, return empty (fallback to original text)
        if not first_match:
            logger.debug("No formal job section found, will use full text")
            return ""

        # Start extraction after the header
        start_idx = first_match.end()

        # Find first cutoff marker
        cutoff_idx = len(text)
        for marker in cutoff_markers:
            idx = text.lower().find(marker)
            if idx != -1 and idx > start_idx:
                cutoff_idx = min(cutoff_idx, idx)

        # Extract section between markers
        section = text[start_idx:cutoff_idx]
        logger.debug(f"Extracted job section: {len(section)} chars from {len(text)}")
        return section

    def _remove_boilerplate(self, text: str) -> str:
        """Remove salary, location, and legal boilerplate from text."""
        if not text:
            return ""

        import re

        # Patterns to remove
        boilerplate_patterns = [
            r"salary.*?(\n|$)",  # Salary mentions
            r"\$[\d,]+.*?(?:year|hour|annually)",  # Salary ranges
            r"(?:remote|on-site|location).*?(?:\n|$)",  # Location metadata
            r"(?:equal opportunity|affirmative action|fcra|dbids).*?(?:\n|$)",  # Legal
            r"(?:background check|export control).*?(?:\n|$)",  # Compliance
            r"(?:benefits|compensation|401\(k\)|health insurance).*?(?:\n|$)",  # Benefits
        ]

        cleaned = text
        for pattern in boilerplate_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

        logger.debug(f"Removed boilerplate: {len(text)} → {len(cleaned)} chars")
        return cleaned

    def _filter_entities(self, entities: list[str], entity_type: str = "skills") -> list[str]:
        """Filter extracted entities to remove noise and short fragments.

        Validation rules (Phase 12 with requirement-specific filtering):
        - Reject if: len < 2 or len > 70
        - Reject if: Matches boilerplate keywords
        - Reject if: Duplicate
        - For requirements: Skip numbers, possessives, job titles, policies, etc.
        """
        boilerplate_keywords = {
            "affirmative",
            "action",
            "equal",
            "opportunity",
            "applications",
            "candidates",
            "recruitment",
            "fcra",
            "dbids",
            "compliance",
            "background",
            "check",
            "export",
            "control",
            "base pay",
            "salary",
            "wage",
            "location",
            "remote",
        }

        filtered: set[str] = set()
        for entity in entities:
            entity_clean = entity.strip()

            # Length validation (Phase 1: conservative)
            if len(entity_clean) < 2 or len(entity_clean) > 70:
                continue

            # Skip boilerplate keywords
            entity_lower = entity_clean.lower()
            words = entity_lower.split()
            if any(kw in entity_lower for kw in boilerplate_keywords):
                continue

            # Skip if contains excessive formatting artifacts (but allow parentheses in some contexts)
            if entity_clean.count("\xa0") > 1 or entity_clean.count("(") > 2:
                continue

            # Phase 12: Requirement-specific filtering
            if entity_type == "requirements":
                # Skip pure numbers or numbers with decimals
                if __import__("re").match(r"^\d+(\.\d+)?$", entity_clean):
                    continue

                # Skip salary/cost ranges with $ or commas
                if "$" in entity_clean or ("range" in entity_lower and ":" in entity_clean):
                    continue

                # Skip items ending with colon (artifacts)
                if entity_clean.rstrip().endswith(":"):
                    continue

                # Skip possessive forms (Blue Origin's, Carbon Robotics', Blue's)
                if entity_clean.endswith("'s") or entity_clean.endswith("'"):
                    continue

                # Skip articles at start (the, a, an)
                if words and words[0] in ("the", "a", "an"):
                    continue

                # Skip single-word fragments
                if len(words) == 1:
                    if entity_lower in ("one", "review", "oversees"):
                        continue

                # Skip incomplete phrases
                if entity_clean in ("s of Service", "Oversees"):
                    continue

                # Skip generic phrases
                if entity_clean in ("each year", "U.S. National"):
                    continue

                # Skip job titles and generic categories
                job_titles = {
                    "design and verification engineer", "software lead",
                    "technical leadership", "technical oversight and authority of a range of software solutions"
                }
                if entity_lower in job_titles:
                    continue

                generic_categories = {
                    "software engineering", "software architecture and design",
                    "software configuration management", "software life cycle management",
                    "college of arts", "college of arts and sciences",
                    "computer science"
                }
                if entity_lower in generic_categories:
                    continue

                # Skip policy/benefit/regulation keywords
                policy_patterns = {
                    "alcohol", "commercial motor", "federal motor carrier",
                    "pre-ipo", "pre-IPO", "stock option", "regulation"
                }
                if any(pattern in entity_lower for pattern in policy_patterns):
                    continue

                # Skip responsibility phrases (action verbs)
                if len(words) >= 2:
                    action_verbs = {"optimize", "prepare", "manage", "oversee"}
                    if words[0] in action_verbs:
                        continue

                # Skip location/proper nouns
                location_nouns = {"seattle", "rocky", "road test"}
                if entity_lower in location_nouns:
                    continue

                # Skip unclear abbreviations
                if entity_lower in ("hdhp", "blue's"):
                    continue

            filtered.add(entity_clean)

        logger.debug(f"Filtered entities: {len(entities)} → {len(filtered)} after validation")
        return sorted(filtered)

    def _is_markdown(self, text: str) -> bool:
        """Detect if text is markdown format (Phase 9).

        Checks for markdown indicators: headers, lists, bold, code blocks.
        Prioritizes markdown headers (## Section) as strongest indicator.
        """
        if not text:
            return False

        # Strong indicator: Markdown section headers
        if re.search(r"^##\s+", text, re.MULTILINE):
            return True

        markdown_indicators = [
            r"^#+\s+",  # Headers (# ## ###)
            r"^[\*\-\+]\s+",  # Unordered lists
            r"^\d+\.\s+",  # Ordered lists
            r"\*\*.*?\*\*",  # Bold
            r"__.*?__",  # Bold (underscore)
            r"`.*?`",  # Inline code
            r"```.*?```",  # Code blocks
        ]

        for pattern in markdown_indicators:
            if re.search(pattern, text, re.MULTILINE):
                return True

        return False

    def _extract_markdown_sections(self, text: str) -> dict[str, str]:
        """Extract sections from structured markdown with divider awareness (Phase 10)."""
        if not text:
            return {}

        sections: dict[str, str] = {}
        current_section = "description"
        current_content: list[str] = []

        lines = text.split("\n")
        for line in lines:
            if line.strip() == "---":
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                    current_content = []
                continue

            header_match = re.match(r"^#+\s+(.+)$", line)
            if header_match:
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                    current_content = []

                header_text = header_match.group(1).strip().lower()
                if any(kw in header_text for kw in ("qualif", "requirement", "essential")):
                    current_section = "qualifications"
                elif any(kw in header_text for kw in ("skill", "technical", "core")):
                    current_section = "skills"
                elif any(kw in header_text for kw in ("knowledge", "experience")):
                    current_section = "knowledge"
                elif any(kw in header_text for kw in ("respons", "duty", "what you")):
                    current_section = "responsibilities"
                else:
                    current_section = header_text.replace(" ", "_")
            else:
                if line.strip():
                    current_content.append(line)

        if current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _extract_entities_by_section(self, text: str) -> Tuple[Set[str], Set[str], Set[str]]:
        """Extract entities intelligently from markdown sections using NER (Phase 11).

        Routes entities to skills, technologies, or requirements based on section type.
        Skips: Benefits, How to Apply, About, Company Culture, Legal content.
        """
        if not self.nlp or not text:
            return set(), set(), set()

        skills: Set[str] = set()
        technologies: Set[str] = set()
        requirements: Set[str] = set()

        sections = self._extract_markdown_sections(text)
        tech_keywords = self._get_tech_keywords()

        skip_sections = {
            "benefits", "compensation", "salary", "pay range", "401", "retirement",
            "insurance", "health", "dental", "vision", "pto", "vacation",
            "about", "company", "culture", "commitment", "team", "our",
            "equal opportunity", "eoe", "affirmative action", "disability",
            "background check", "export control", "security clearance", "visa",
            "apply", "posting date", "posted", "application close", "codevue",
            "shift", "location", "work location", "travel", "working condition",
            "fte", "temporary", "education:", "hiring practice"
        }

        for section_name, section_content in sections.items():
            section_lower = section_name.lower().replace("_", " ")
            if any(skip_kw in section_lower for skip_kw in skip_sections):
                continue
            if not section_content.strip():
                continue

            try:
                doc = self.nlp(section_content)
            except Exception:
                continue

            section_lower = section_name.lower()
            list_items = re.findall(r"^[\*\-\+]\s+(.+)$|^\d+\.\s+(.+)$", section_content, re.MULTILINE)

            for ent in doc.ents:
                entity_text = ent.text.strip()
                if not entity_text or len(entity_text) < 2:
                    continue

                if any(kw in section_lower for kw in ("skill", "technical", "ability")):
                    if any(kw in entity_text.lower() for kw in tech_keywords):
                        technologies.add(entity_text)
                    else:
                        skills.add(entity_text)
                elif any(kw in section_lower for kw in ("requirement", "qualif", "needed", "essential")):
                    requirements.add(entity_text)
                elif any(kw in section_lower for kw in ("knowledge", "experience", "responsibility")):
                    requirements.add(entity_text)

            if any(kw in section_lower for kw in ("skill", "technical")):
                for token in doc:
                    if token.pos_ in ("NOUN", "PROPN") and len(token.text) > 2:
                        if token.text.lower() in tech_keywords:
                            technologies.add(token.text)
                        elif token.text not in skills:
                            skills.add(token.text)

            for item in list_items:
                if isinstance(item, tuple):
                    item_text = item[0] if item[0] else (item[1] if len(item) > 1 else "")
                else:
                    item_text = str(item)

                item_text = item_text.strip()
                if not item_text or len(item_text) < 3:
                    continue

                if re.search(r"\d+\s*[-–]\s*\d+\s*years?|^\d+\+\s*years?", item_text.lower()):
                    continue

                if any(kw in section_lower for kw in ("skill", "technical")):
                    if len(item_text) > 3 and item_text.count(",") < 2:
                        skills.add(item_text)
                else:
                    if len(item_text) > 3 and item_text.count(",") < 2:
                        requirements.add(item_text)

        logger.debug(
            f"Entity extraction by section: {len(skills)} skills, "
            f"{len(technologies)} technologies, {len(requirements)} requirements"
        )
        return skills, technologies, requirements

    @staticmethod
    def _extract_soft_skills(doc: Any, soft_skills: Set[str]) -> None:
        """Extract soft skills from tokens."""
        soft_skills_list = get_all_soft_skills()
        tokens_list = list(doc)

        for token in tokens_list:
            token_text = token.text.strip()
            if not token_text or len(token_text) < 3:
                continue

            if token_text.lower() in soft_skills_list:
                soft_skills.add(token_text)
            elif token.lemma_.lower() in soft_skills_list:
                soft_skills.add(token.text)

            if token.pos_ in ("ADJ", "NOUN"):
                parent = token.head
                if parent.pos_ in ("NOUN", "ADJ") and parent != token:
                    phrase = " ".join(
                        child.text for child in tokens_list
                        if child.head == parent or child == parent
                    )
                    if 3 < len(phrase) < 50 and phrase.lower() in soft_skills_list:
                        soft_skills.add(phrase)
