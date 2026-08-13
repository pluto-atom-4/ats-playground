import json

import spacy

from poc.technologies.patterns import TECH_TERMS


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
        self.ruler = nlp.add_pipe("entity_ruler", before="ner")
        self.ruler.add_patterns(_generate_patterns())

    def extract(self, doc):
        # We use a set to automatically handle duplicates in the text
        return sorted({ent.text for ent in doc.ents if ent.label_ == "TECH"})


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
