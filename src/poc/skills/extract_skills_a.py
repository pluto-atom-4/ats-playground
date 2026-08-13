import spacy
from spacy.matcher import Matcher
from spacy.util import filter_spans

from .patterns import SKILL_VERBS


class SkillExtractor:
    def __init__(self, model_name="en_core_web_md"):
        # Load spaCy model
        self.nlp = spacy.load(model_name)
        self.matcher = Matcher(self.nlp.vocab)

        # 2. Define the Matcher Pattern
        # Logic: [Action Verb] + [Optional Preposition/Article] + [Descriptive Nouns/Adjectives]
        pattern = [
            # The Action: Must be a verb and its base form must be in our list
            {"POS": "VERB", "LEMMA": {"IN": SKILL_VERBS}},
            # Optional: Connector words like "with", "the", "of"
            # (e.g., "partner WITH", "lead THE")
            {"POS": {"IN": ["ADP", "DET", "PART"]}, "OP": "?"},
            # The Meat: A sequence of Nouns, Adjectives, or Proper Nouns
            # (e.g., "novel deep learning architectures")
            {"POS": {"IN": ["ADJ", "NOUN", "PROPN", "ADP"]}, "OP": "+"},
        ]

        # Add pattern to matcher
        self.matcher.add("SKILL_PHRASE", [pattern])

    def extract(self, text):
        doc = self.nlp(text)

        # 3. Find matches in the document
        # 'as_spans=True' returns spaCy Span objects instead of ID tuples
        matches = self.matcher(doc, as_spans=True)

        # 4. Best Practice: Filter Overlaps
        # If the matcher finds "design architectures" and "design deep learning architectures",
        # filter_spans will only keep the longest one.
        unique_spans = filter_spans(matches)

        # Clean the text: strip whitespace and convert to lowercase
        results = [span.text.replace("\n", " ").strip().lower() for span in unique_spans]

        # Deduplicate and return
        return sorted(set(results))


# --- Implementation Example ---

if __name__ == "__main__":
    # Example input from the Carbon Robotics JD
    carbon_jd_bullets = """[PASTE THE JOB DESCRIPTION HERE]"""

    # Initialize and Run
    extractor = SkillExtractor()
    skills = extractor.extract(carbon_jd_bullets)

    print(f"{'INDEX':<5} | {'EXTRACTED SKILL'}")
    print("-" * 50)
    for i, skill in enumerate(skills):
        print(f"{i + 1:<5} | {skill}")
