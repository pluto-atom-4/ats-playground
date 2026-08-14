import json
import logging

import spacy

from .patterns import TECH_TERMS

logger = logging.getLogger(__name__)


def _generate_patterns():
    patterns = []
    for term in TECH_TERMS:
        # Check if it's a multi-word phrase
        if " " in term:
            # Phrase pattern: Case-insensitive by using the text logic
            # 'computer vision' -> [{'LOWER': 'computer'}, {'LOWER': 'vision'}]
            tokens = term.lower().split()
            patterns.append({"label": "TECH", "pattern": [{"LOWER": t} for t in tokens]})
        else:
            # Single word pattern: Simple case-insensitive token match
            # 'PyTorch' -> {'LOWER': 'pytorch'}
            patterns.append({"label": "TECH", "pattern": [{"LOWER": term.lower()}]})
    return patterns


class TechExtractor:
    def __init__(self, nlp):
        self.nlp = nlp
        # Check if entity_ruler already exists
        if "entity_ruler" not in nlp.pipe_names:
            self.ruler = nlp.add_pipe("entity_ruler", before="ner")
        else:
            self.ruler = nlp.get_pipe("entity_ruler")
        self.ruler.add_patterns(_generate_patterns())

    def extract(self, doc):
        try:
            # Extract all TECH entities and normalize to lowercase for deduplication
            # This handles case-insensitive matching results (PyTorch vs pytorch)
            techs_lower = {ent.text.lower() for ent in doc.ents if ent.label_ == "TECH"}
            return sorted(techs_lower)
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return []


def main():
    # Load spaCy model
    nlp = spacy.load("en_core_web_md")

    # Initialize modules
    tech_engine = TechExtractor(nlp)

    text = """[PASTE THE JOB DESCRIPTION HERE]"""

    # Process text
    doc = nlp(text)

    # Run extractions
    results = {"technologies": tech_engine.extract(doc)}

    # Post-process: Remove common noise/duplicates
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
