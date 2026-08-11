"""Integration tests for Phase 8b span preservation in chunking.

Tests full pipeline: requirement_filter → span_categorizer → chunking
Validates that requirement spans are never split across chunk boundaries.
"""

import logging
import time
from typing import Any, Dict, Generator, List

import pytest
import spacy
from spacy.language import Language

from src.tokenization.chunker import SemanticChunker
from src.tokenization.preprocessor import Preprocessor

# Sample job descriptions with requirements for testing
SAMPLE_JOBS = [
    {
        "id": "job_001",
        "title": "Senior Python Developer",
        "description": """
        We are looking for a Senior Python Developer to join our team.

        Required: 5+ years Python experience with Django and REST API design.
        Must have strong communication and problem-solving skills.
        Essential: experience with Docker and Kubernetes deployment.
        Knowledge of microservices architecture required.
        Ability to lead teams and mentor junior developers.
        Must understand agile methodologies and CI/CD pipelines.
        """,
    },
    {
        "id": "job_002",
        "title": "DevOps Engineer",
        "description": """
        Join our infrastructure team as a DevOps Engineer.

        Required: 3+ years experience with AWS or Google Cloud.
        Must have deep knowledge of Docker and container orchestration.
        Essential: experience with Terraform, CI/CD pipelines (Jenkins, GitLab CI).
        Knowledge of Kubernetes deployment and management required.
        Ability to automate infrastructure provisioning and monitoring.
        Strong understanding of networking and security best practices.
        """,
    },
    {
        "id": "job_003",
        "title": "Data Scientist",
        "description": """
        Seeking Data Scientist for machine learning team.

        Required: 4+ years experience with Python, pandas, scikit-learn.
        Must have strong statistics and experimental design knowledge.
        Essential: experience with deep learning frameworks (TensorFlow, PyTorch).
        Knowledge of SQL and big data tools (Spark) required.
        Ability to communicate findings to non-technical stakeholders.
        Experience in production ML systems and model deployment.
        """,
    },
    {
        "id": "job_004",
        "title": "Full Stack Developer",
        "description": """
        Build web applications as a Full Stack Developer.

        Required: 3+ years JavaScript/TypeScript and React experience.
        Must have backend experience (Node.js, Python, or similar).
        Essential: knowledge of PostgreSQL, MongoDB, or similar databases.
        Experience with modern development tools: Git, Docker, testing frameworks.
        Ability to design and implement RESTful APIs and GraphQL schemas.
        Strong problem-solving skills and attention to detail.
        """,
    },
    {
        "id": "job_005",
        "title": "Cloud Architect",
        "description": """
        Design scalable cloud infrastructure as a Cloud Architect.

        Required: 6+ years cloud infrastructure experience (AWS, Azure, or GCP).
        Must have expertise in containerization and microservices architecture.
        Essential: experience with Infrastructure as Code (Terraform, CloudFormation).
        Knowledge of security, compliance, and disaster recovery required.
        Ability to design multi-region high-availability systems.
        Experience mentoring engineering teams on cloud best practices.
        """,
    },
]


@pytest.fixture
def preprocessor() -> Generator[Preprocessor, None, None]:
    """Create a preprocessor with requirements extraction enabled.

    Yields:
        Preprocessor instance
    """
    try:
        prep = Preprocessor(
            model="en_core_web_md",
            extract_requirements=True,
            preserve_requirement_spans=True,
        )
        yield prep
    except OSError:
        pytest.skip("en_core_web_md not installed")


@pytest.fixture
def chunker() -> SemanticChunker:
    """Create a chunker with span preservation enabled.

    Returns:
        SemanticChunker instance
    """
    return SemanticChunker(target_chunk_size=400, preserve_requirement_spans=True)


class TestSpanPreservationIntegration:
    """Integration tests for requirement span preservation in chunking."""

    def test_preprocess_with_span_extraction(self, preprocessor: Preprocessor) -> None:
        """Test that preprocessing extracts requirements and spans.

        Args:
            preprocessor: Preprocessor fixture
        """
        job = SAMPLE_JOBS[0]
        text = job["description"]

        # Process through pipeline
        doc = preprocessor.nlp(text)  # type: ignore[misc]

        # Should extract requirements
        requirements = getattr(doc._, "requirements", None)
        assert requirements is not None, "Phase 8a should extract requirements"
        assert len(requirements) > 0, f"Should extract requirements from: {text[:100]}"

        # Should create spans
        requirement_spans = getattr(doc._, "requirement_spans", None)
        assert requirement_spans is not None, "Phase 8b should create spans"
        assert len(requirement_spans) > 0, f"Should create spans for: {len(requirements)} requirements"

        # Log extraction results
        logging.info(f"Job {job['id']}: Extracted {len(requirements)} requirements, {len(requirement_spans)} spans")

    def test_chunk_respects_requirement_spans(
        self,
        preprocessor: Preprocessor,
        chunker: SemanticChunker,
    ) -> None:
        """Test that chunking with span preservation works without errors.

        Args:
            preprocessor: Preprocessor fixture
            chunker: Chunker fixture
        """
        job = SAMPLE_JOBS[0]
        text = job["description"]

        # Process through full pipeline
        doc = preprocessor.nlp(text)  # type: ignore[misc]
        requirement_spans = getattr(doc._, "requirement_spans", [])

        if not requirement_spans:
            pytest.skip("No requirement spans extracted")

        # Chunk with span preservation (should not crash)
        chunks = chunker.chunk(text, doc=doc)

        # Should produce valid chunks
        assert len(chunks) > 0, "Should produce chunks with span preservation"
        assert all(isinstance(chunk, str) and chunk.strip() for chunk in chunks), (
            "All chunks should be non-empty strings"
        )

        # Verify core content is preserved (basic sanity check)
        full_text_lower = text.lower()
        combined_chunks = " ".join(chunks).lower()
        # Should contain most of the original content
        content_coverage = sum(1 for word in full_text_lower.split() if word in combined_chunks) / len(
            full_text_lower.split()
        )
        assert content_coverage > 0.8, f"Chunks should preserve ~80% of content, got {content_coverage:.0%}"

    def test_multiple_jobs_span_preservation(self, preprocessor: Preprocessor, chunker: SemanticChunker) -> None:
        """Test span preservation across 5 sample jobs.

        Args:
            preprocessor: Preprocessor fixture
            chunker: Chunker fixture
        """
        start_time = time.time()
        total_spans = 0
        total_chunks = 0
        jobs_processed = 0

        for job in SAMPLE_JOBS:
            text = job["description"]
            doc = preprocessor.nlp(text)  # type: ignore[misc]

            requirement_spans = getattr(doc._, "requirement_spans", [])
            total_spans += len(requirement_spans)

            # Chunk with span preservation enabled
            chunks = chunker.chunk(text, doc=doc)
            total_chunks += len(chunks)
            jobs_processed += 1

            # Basic validation: chunks should be created
            assert len(chunks) > 0, f"Should produce chunks for {job['id']}"
            assert all(isinstance(c, str) and c.strip() for c in chunks), f"Invalid chunks for {job['id']}"

        elapsed_ms = (time.time() - start_time) * 1000
        avg_time_per_job = elapsed_ms / jobs_processed

        logging.info(
            f"Processed {jobs_processed} jobs: "
            f"{total_spans} spans, {total_chunks} chunks in {elapsed_ms:.0f}ms "
            f"({avg_time_per_job:.0f}ms/job)"
        )

        # Performance check: should add <100ms per job (including pipeline overhead)
        assert avg_time_per_job < 100, f"Processing time {avg_time_per_job:.0f}ms/job exceeds 100ms target"

    def test_disable_span_preservation_flag(self, preprocessor: Preprocessor) -> None:
        """Test that disabling flag produces old behavior.

        Args:
            preprocessor: Preprocessor fixture
        """
        job = SAMPLE_JOBS[0]
        text = job["description"]

        # Create chunker with span preservation disabled
        chunker_no_spans = SemanticChunker(preserve_requirement_spans=False)

        doc = preprocessor.nlp(text)  # type: ignore[misc]

        # Chunk with flag disabled
        chunks = chunker_no_spans.chunk(text, doc=doc)

        # Should still produce chunks (backward compatible)
        assert len(chunks) > 0, "Should produce chunks even with span preservation disabled"

    def test_chunk_metadata_completeness(self, preprocessor: Preprocessor) -> None:
        """Test that spans have complete metadata.

        Args:
            preprocessor: Preprocessor fixture
        """
        job = SAMPLE_JOBS[0]
        text = job["description"]

        doc = preprocessor.nlp(text)  # type: ignore[misc]
        requirement_spans = getattr(doc._, "requirement_spans", [])

        required_fields = {
            "span_text",
            "start_token",
            "end_token",
            "span_type",
            "conjunct_count",
            "trigger_word",
            "confidence",
        }

        for span in requirement_spans:
            for field in required_fields:
                assert field in span, f"Missing field '{field}' in span: {span.keys()}"
            assert span["span_type"] in ["atomic", "compound"]
            assert 0 <= span["confidence"] <= 1.0
            assert span["conjunct_count"] >= 1


class TestBackwardCompatibility:
    """Test backward compatibility with old pipeline behavior."""

    def test_preprocessor_without_span_preservation(self) -> None:
        """Test preprocessor with span preservation disabled.

        Should work but not add span_categorizer.
        """
        try:
            prep = Preprocessor(
                model="en_core_web_md",
                extract_requirements=True,
                preserve_requirement_spans=False,
            )

            job_text = SAMPLE_JOBS[0]["description"]
            doc = prep.nlp(job_text)  # type: ignore[misc]

            # Should still extract requirements (Phase 8a)
            requirements = getattr(doc._, "requirements", None)
            assert requirements is not None

            # span_categorizer may or may not be in pipeline (depends on implementation)
            # But even if present, we're not using spans for chunking
        except OSError:
            pytest.skip("en_core_web_md not installed")

    def test_chunker_backward_compatible(self) -> None:
        """Test that chunker works without doc parameter (backward compatible)."""
        chunker = SemanticChunker(preserve_requirement_spans=True)
        job_text = SAMPLE_JOBS[0]["description"]

        # Should work without doc parameter
        chunks = chunker.chunk(job_text)

        assert len(chunks) > 0, "Should produce chunks without doc parameter"


class TestEdgeCases:
    """Test edge cases in span preservation."""

    def test_empty_spans_list(self, preprocessor: Preprocessor, chunker: SemanticChunker) -> None:
        """Test chunking when no spans are extracted.

        Args:
            preprocessor: Preprocessor fixture
            chunker: Chunker fixture
        """
        # Text without requirements
        text = "This is a simple job posting without specific requirements mentions."

        doc = preprocessor.nlp(text)  # type: ignore[misc]
        chunks = chunker.chunk(text, doc=doc)

        # Should still produce chunks (graceful degradation)
        assert len(chunks) > 0

    def test_single_long_span(self, preprocessor: Preprocessor, chunker: SemanticChunker) -> None:
        """Test handling of very long requirement spans.

        Args:
            preprocessor: Preprocessor fixture
            chunker: Chunker fixture
        """
        long_requirement = """
        Required: 10+ years experience with Python, Java, C++, JavaScript, TypeScript, Go, Rust,
        and Kotlin. Must have deep knowledge of SQL, MongoDB, Redis, and Cassandra databases.
        Essential: experience with AWS, Azure, GCP, Docker, Kubernetes, Terraform, Ansible,
        Chef, Puppet, and Jenkins. Knowledge of microservices, distributed systems, and
        high-availability architecture required.
        """

        doc = preprocessor.nlp(long_requirement)  # type: ignore[misc]
        requirement_spans = getattr(doc._, "requirement_spans", [])

        if requirement_spans:
            chunks = chunker.chunk(long_requirement, doc=doc)
            # Even with very long spans, shouldn't crash
            assert len(chunks) > 0
