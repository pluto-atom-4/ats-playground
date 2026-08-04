"""Noise words taxonomy for filtering low-signal entities (Phase 1).

This module provides noise word categories to remove non-substantive terms
from skill extraction:
- Articles & Determiners: the, a, an, this, that, these, those, my, your
- Prepositions: in, on, at, of, with, by, to, from, for, about
- Conjunctions: and, or, but, nor, yet, so, as, if, because
- Pronouns: I, you, he, she, it, we, they, what, which, who
- Generic Verbs: do, make, have, be, get, go, come, know, take, see
- Numbers & Measurements: one, two, five, percent, years, months, plus
- Generic Nouns: thing, stuff, way, work, life, area, part, type, sort, kind
- Filler Words: really, very, just, only, also, even, still, yet, already
"""

# Noise words organized into 8 categories with 120+ terms total
NOISE_WORDS_BY_CATEGORY = {
    # 1. Articles & Determiners (15 terms)
    "articles_determiners": {
        "the",
        "a",
        "an",
        "this",
        "that",
        "these",
        "those",
        "my",
        "your",
        "his",
        "her",
        "its",
        "our",
        "their",
        "some",
    },
    # 2. Prepositions (20 terms)
    "prepositions": {
        "in",
        "on",
        "at",
        "of",
        "with",
        "by",
        "to",
        "from",
        "for",
        "about",
        "during",
        "before",
        "after",
        "above",
        "below",
        "under",
        "over",
        "between",
        "among",
        "through",
    },
    # 3. Conjunctions (12 terms)
    "conjunctions": {
        "and",
        "or",
        "but",
        "nor",
        "yet",
        "so",
        "as",
        "if",
        "because",
        "although",
        "while",
        "since",
    },
    # 4. Pronouns (12 terms)
    "pronouns": {
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "what",
        "which",
        "who",
    },
    # 5. Generic Verbs (15 terms)
    "generic_verbs": {
        "do",
        "make",
        "have",
        "be",
        "get",
        "go",
        "come",
        "know",
        "take",
        "see",
        "think",
        "say",
        "give",
        "keep",
        "try",
    },
    # 6. Numbers & Measurements (18 terms)
    "numbers_measurements": {
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "percent",
        "years",
        "months",
        "weeks",
        "days",
        "hours",
        "plus",
        "minus",
    },
    # 7. Generic Nouns (18 terms)
    "generic_nouns": {
        "thing",
        "stuff",
        "way",
        "work",
        "life",
        "area",
        "part",
        "type",
        "sort",
        "kind",
        "form",
        "case",
        "point",
        "item",
        "number",
        "level",
        "range",
        "value",
    },
    # 8. Filler Words (18 terms)
    "filler_words": {
        "really",
        "very",
        "just",
        "only",
        "also",
        "even",
        "still",
        "yet",
        "already",
        "quite",
        "rather",
        "somewhat",
        "somehow",
        "perhaps",
        "maybe",
        "actually",
        "basically",
    },
}

# Flat set of all noise words for quick lookups
NOISE_WORDS = set()
for category_words in NOISE_WORDS_BY_CATEGORY.values():
    NOISE_WORDS.update(category_words)


def get_all_noise_words() -> set[str]:
    """Get all noise words.

    Returns:
        Set of all noise word terms across all categories
    """
    return NOISE_WORDS.copy()


def get_noise_words_by_category(category: str) -> set[str]:
    """Get noise words for a specific category.

    Args:
        category: One of: articles_determiners, prepositions, conjunctions,
                  pronouns, generic_verbs, numbers_measurements, generic_nouns,
                  filler_words

    Returns:
        Set of noise word terms in that category, or empty set if category not found
    """
    return NOISE_WORDS_BY_CATEGORY.get(category, set()).copy()


def get_all_categories() -> list[str]:
    """Get all noise word categories.

    Returns:
        List of category names
    """
    return list(NOISE_WORDS_BY_CATEGORY.keys())


def is_noise_word(word: str) -> bool:
    """Check if a word is a noise word.

    Args:
        word: The word to check (will be lowercased)

    Returns:
        True if word is in noise words, False otherwise
    """
    return word.lower() in NOISE_WORDS
