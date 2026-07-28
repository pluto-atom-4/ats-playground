"""NLP preprocessing for job postings using spaCy."""

import logging
from typing import Any, List, Optional, Set, Tuple

import spacy
from spacy.language import Language

from src.tokenization.keywords import get_all_keywords

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

            # 4. Filter entities (remove noise, duplicates, short fragments)
            skills = set(self._filter_entities(list(skills)))
            technologies = set(self._filter_entities(list(technologies)))
            requirements = set(self._filter_entities(list(requirements)))

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
            r"(?i)(qualifications|requirements|what we're looking for|what we need|what you'll need|must-have|essential|desired qualifications)(?:\s*[:|\n])",
            r"(?i)(responsibilities|what you'll do|your role|what you will|primary responsibilities)(?:\s*[:|\n])",
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

    def _filter_entities(self, entities: list[str]) -> list[str]:
        """Filter extracted entities to remove noise and short fragments.

        Validation rules (Phase 1 - Conservative):
        - Reject if: len < 2 or len > 70
        - Reject if: Matches boilerplate keywords
        - Reject if: Duplicate
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
            if any(kw in entity_lower for kw in boilerplate_keywords):
                continue

            # Skip if contains excessive formatting artifacts (but allow parentheses in some contexts)
            if entity_clean.count("\xa0") > 1 or entity_clean.count("(") > 2:
                continue

            filtered.add(entity_clean)

        logger.debug(f"Filtered entities: {len(entities)} → {len(filtered)} after validation")
        return sorted(filtered)
