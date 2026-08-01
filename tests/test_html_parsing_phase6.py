"""Phase 1: Baseline tests for HTML parsing improvement (Issue #193)."""

import pytest

from src.tokenization.preprocessor import Preprocessor


class TestHTMLParsingBaseline:
    """Baseline tests for HTML parsing quality before Phase 2 improvements."""

    @pytest.fixture
    def preprocessor(self, monkeypatch):
        """Initialize Preprocessor with real spaCy model."""
        preprocessor = Preprocessor(model="en_core_web_md")
        return preprocessor

    # Test Data: Representative problematic fragments from real job descriptions
    TEST_DATA = [
        {
            "name": "Multi-word fragment with case transition",
            "text": "Requires 5+ years of experience may differCulture StatementDon't settle for less.",
            "expected_fragment": "may differCulture StatementDon't",
            "description": "Mixed case artifact from HTML parsing",
        },
        {
            "name": "Section header artifact",
            "text": "Core CompetenciesRequired QualificationsTo apply, send your resume.",
            "expected_fragment": "Required QualificationsTo",
            "description": "Section headers concatenated without spacing",
        },
        {
            "name": "Compound science keywords",
            "text": "Degree in computer science and years of data science , or science background.",
            "expected_fragments": ["computer science and years", "data science , or science"],
            "description": "Oddly split compound keywords",
        },
        {
            "name": "Article concatenation",
            "text": "the Hiring Manager wants experienced developers for team.",
            "expected_fragment": "the Hiring Manager",
            "description": "Article with proper noun concatenation",
        },
        {
            "name": "HTML entity artifacts",
            "text": "Requirements&nbsp;&nbsp;Position Details&nbsp;We are looking for professionals.",
            "expected_fragment": None,  # Should be removed during cleanup
            "description": "HTML non-breaking spaces in text",
        },
    ]

    def test_baseline_extraction_quality(self, preprocessor):
        """Extract entities from problematic text and measure baseline quality."""
        test_text = (
            "Requires 5+ years of experience may differCulture StatementDon't settle for less. "
            "Core CompetenciesRequired QualificationsTo apply, send your resume. "
            "Degree in computer science and years of data science , or science background. "
            "the Hiring Manager wants experienced developers for team."
        )

        skills, tech, reqs = preprocessor.extract_entities(test_text)

        # Baseline metrics
        metrics = {
            "total_entities": len(skills) + len(tech) + len(reqs),
            "skills_count": len(skills),
            "tech_count": len(tech),
            "reqs_count": len(reqs),
        }

        # Count multi-word fragments with suspicious characteristics
        suspicious_count = 0
        for entity_list in [skills, tech, reqs]:
            for entity in entity_list:
                # Check for problematic patterns: MixedCase, articles, etc.
                if self._has_suspicious_pattern(entity):
                    suspicious_count += 1

        metrics["suspicious_fragments"] = suspicious_count
        metrics["quality_score"] = self._calculate_quality_score(suspicious_count, len(skills) + len(tech) + len(reqs))

        # Store baseline metrics
        pytest.baseline_metrics = metrics
        assert metrics["quality_score"] >= 0  # Baseline can be any value

    def test_fragment_count_baseline(self, preprocessor):
        """Establish baseline fragment count before improvements."""
        test_cases = [
            ("Senior may differCulture StatementDeveloper wanted", "MixedCase fragment"),
            ("Core CompetenciesRequired QualificationsTo apply", "Section header artifact"),
            ("Computer science and years data science", "Oddly split compound"),
        ]

        total_fragments = 0
        for text, _ in test_cases:
            skills, tech, reqs = preprocessor.extract_entities(text)
            fragment_count = self._count_suspicious_fragments(skills + tech + reqs)
            total_fragments += fragment_count

        # Baseline measurement (no assertion yet - just measurement)
        baseline_fragment_count = total_fragments
        pytest.baseline_fragment_count = baseline_fragment_count

    def test_quality_score_calculation(self, preprocessor):
        """Test quality score calculation: (total_entities - suspicious) / total_entities * 100."""
        text = "Senior may differCulture StatementDeveloper with Core CompetenciesRequired Qualifications."

        skills, tech, reqs = preprocessor.extract_entities(text)
        all_entities = skills + tech + reqs

        quality_score = self._calculate_quality_score(
            self._count_suspicious_fragments(all_entities),
            len(all_entities)
        )

        # Store for Phase 4 comparison
        pytest.quality_score_baseline = quality_score
        assert 0 <= quality_score <= 100

    def test_signal_to_noise_ratio_baseline(self, preprocessor):
        """Calculate baseline signal-to-noise ratio (good entities / total entities)."""
        text = (
            "Needs Python JavaScript React expertise. "
            "Experience with may differCulture StatementPostgreSQL and MongoDB. "
            "Required QualificationsTo include AWS cloud skills."
        )

        skills, tech, reqs = preprocessor.extract_entities(text)
        all_entities = skills + tech + reqs

        good_count = len([e for e in all_entities if not self._has_suspicious_pattern(e)])
        ratio = (good_count / len(all_entities) * 100) if all_entities else 0

        pytest.baseline_signal_to_noise_ratio = ratio
        # Baseline target: 45%+ (before Phase 2 improvements)
        assert ratio >= 0  # Baseline can be any value

    @staticmethod
    def _has_suspicious_pattern(entity: str) -> bool:
        """Check if entity has suspicious patterns indicating HTML parsing issues."""
        # MixedCase transitions (e.g., "differCulture")
        mixed_case = any(
            entity[i].isupper() and entity[i-1].islower()
            for i in range(1, len(entity))
        )

        # Multiple case transitions (e.g., "may differCulture StatementDon't")
        case_transitions = sum(
            1 for i in range(1, len(entity))
            if entity[i].isupper() != entity[i-1].isupper()
        )

        # Unclosed punctuation
        has_unclosed_punc = (
            entity.count("(") != entity.count(")")
            or entity.count("[") != entity.count("]")
        )

        # Very short multi-word with odd spacing
        words = entity.split()
        odd_spacing = len(words) > 1 and any(len(w) < 3 for w in words)

        return mixed_case or case_transitions > 2 or has_unclosed_punc or odd_spacing

    @staticmethod
    def _count_suspicious_fragments(entities: list) -> int:
        """Count entities with suspicious patterns."""
        return sum(
            1 for entity in entities
            if TestHTMLParsingBaseline._has_suspicious_pattern(entity)
        )

    @staticmethod
    def _calculate_quality_score(suspicious_count: int, total_count: int) -> float:
        """Calculate quality score: (total - suspicious) / total * 100."""
        if total_count == 0:
            return 100.0
        return ((total_count - suspicious_count) / total_count) * 100
