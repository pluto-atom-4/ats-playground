"""Advanced normalization for requirement text matching."""

import re
from difflib import SequenceMatcher
from typing import Set


class RequirementNormalizer:
    """Normalize requirement text to improve semantic matching."""

    @staticmethod
    def normalize_requirement_for_comparison(req: str) -> str:
        """Normalize requirement for semantic comparison.

        Handles:
        - Verbose alternatives: "working with and/or interpreting" -> "interpreting"
        - Adjective variations: "deep experience" -> "experience"
        - Prepositional phrases: Preserves but standardizes
        """
        req = req.strip()

        # Remove parenthetical notes at end (e.g., "(Preferred)")
        req = re.sub(r'\s*\(.*?\)\s*$', '', req)

        # Collapse verbose alternatives (and/or patterns)
        req = re.sub(r'working\s+with\s+and/or\s+', '', req, flags=re.IGNORECASE)
        req = re.sub(r'working\s+with\s+', '', req, flags=re.IGNORECASE)

        # Simplify adjectives before "experience"
        adj_pattern = r'\b(deep|strong|extensive|proven|demonstrated)\s+experience\b'
        req = re.sub(adj_pattern, 'experience', req, flags=re.IGNORECASE)

        # Remove "hands-on" prefix
        req = re.sub(r'\bhands-?on\s+', '', req, flags=re.IGNORECASE)

        # Standardize years patterns
        years_pattern = r'(\d+)\+?\s+years?\s+(?:of\s+)?experience\s+'
        req = re.sub(years_pattern, r'\1+ years of experience ', req, flags=re.IGNORECASE)

        # Collapse multiple spaces
        req = re.sub(r'\s+', ' ', req).strip()

        return req

    @staticmethod
    def find_matching_requirement(
        target: str, candidates: Set[str], threshold: float = 0.7
    ) -> tuple[str | None, float]:
        """Find best semantic match from candidates using fuzzy matching.

        Args:
            target: Requirement to match
            candidates: Set of requirements to search
            threshold: Similarity threshold (0-1)

        Returns:
            (best_match, similarity_score) or (None, 0) if no match above threshold
        """
        normalized_target = RequirementNormalizer.normalize_requirement_for_comparison(target)

        best_match: str | None = None
        best_score: float = 0.0

        for candidate in candidates:
            normalized_candidate = RequirementNormalizer.normalize_requirement_for_comparison(candidate)

            # Check for exact match after normalization
            if normalized_target.lower() == normalized_candidate.lower():
                return (candidate, 1.0)

            # Fuzzy string matching using SequenceMatcher
            target_lower = normalized_target.lower()
            candidate_lower = normalized_candidate.lower()

            # Use SequenceMatcher for fuzzy matching
            ratio = SequenceMatcher(None, target_lower, candidate_lower).ratio()

            # Boost score for substring matches
            if target_lower in candidate_lower or candidate_lower in target_lower:
                # Scale based on length overlap
                overlap_len = min(len(target_lower), len(candidate_lower))
                union_len = max(len(target_lower), len(candidate_lower))
                substring_score = overlap_len / union_len if union_len > 0 else 0
                # Weight substring match higher if both are long (more specific)
                if min(len(target_lower), len(candidate_lower)) > 40:
                    ratio = max(ratio, substring_score * 1.1)
                else:
                    ratio = max(ratio, substring_score)

            if ratio > best_score:
                best_score = ratio
                best_match = candidate

        if best_score >= threshold:
            return (best_match, best_score)

        return (None, 0.0)

    @staticmethod
    def deduplicate_requirements(requirements: Set[str]) -> Set[str]:
        """Remove semantically duplicate requirements.

        Keeps original text of most specific/longest version.
        """
        deduplicated: set[str] = set()
        sorted_reqs = sorted(requirements, key=len, reverse=True)

        for req in sorted_reqs:
            # Check if any existing item is semantically equivalent
            match, score = RequirementNormalizer.find_matching_requirement(req, deduplicated, threshold=0.8)

            if score < 0.8:
                # No close match found, add this requirement
                deduplicated.add(req)

        return deduplicated


def normalize_and_deduplicate(requirements: Set[str]) -> Set[str]:
    """Normalize and deduplicate a set of requirements."""
    return RequirementNormalizer.deduplicate_requirements(requirements)
