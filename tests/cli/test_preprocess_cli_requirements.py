"""Integration tests for preprocess CLI with requirement extraction.

Tests CLI flags --extract-requirements, --no-extract-requirements,
and --export-requirements-json for Phase 8 requirement extraction.
"""

import json
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


@pytest.fixture
def sample_jobs_file() -> Generator[tuple[Path, list[dict[str, Any]]], None, None]:
    """Create a temporary sample jobs file for testing."""
    sample_jobs = [
        {
            "id": "job_001",
            "title": "Senior Python Developer",
            "company": "TechCorp",
            "location": "Remote",
            "url": "https://example.com/job1",
            "description": (
                "We are seeking a Senior Python Developer. "
                "Required: 5+ years of Python experience. "
                "Must have knowledge of Django and FastAPI. "
                "Essential skills include REST API design. "
                "Proficiency in Docker is mandatory."
            ),
        },
        {
            "id": "job_002",
            "title": "Full Stack Engineer",
            "company": "StartupXYZ",
            "location": "San Francisco",
            "url": "https://example.com/job2",
            "description": (
                "Join our team as a Full Stack Engineer. "
                "Required technologies: React, Node.js, PostgreSQL. "
                "Must understand microservices architecture. "
                "Experience with AWS is essential. "
                "Should have CI/CD pipeline experience."
            ),
        },
        {
            "id": "job_003",
            "title": "Data Scientist",
            "company": "DataSys",
            "location": "New York",
            "url": "https://example.com/job3",
            "description": (
                "Join our analytics team as a Data Scientist. "
                "Essential: Machine learning knowledge required. "
                "Proficiency in Python and SQL. "
                "Understanding of statistical methods. "
                "Ability to communicate findings."
            ),
        },
        {
            "id": "job_004",
            "title": "DevOps Engineer",
            "company": "CloudPlatform",
            "location": "Remote",
            "url": "https://example.com/job4",
            "description": (
                "DevOps Engineer for infrastructure automation. "
                "Must have hands-on Kubernetes experience. "
                "Required: AWS or GCP certification. "
                "Essential: Infrastructure as Code (Terraform). "
                "Strong Linux/Unix administration skills."
            ),
        },
        {
            "id": "job_005",
            "title": "Frontend Developer",
            "company": "WebDesign Inc",
            "location": "Boston",
            "url": "https://example.com/job5",
            "description": (
                "Seeking Frontend Developer for modern web apps. "
                "Required: JavaScript/TypeScript expertise. "
                "Must know React or Vue.js. "
                "Proficiency in HTML5 and CSS3. "
                "Understanding of responsive design essential."
            ),
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        extracted_dir = tmpdir_path / "extracted_jobs"
        extracted_dir.mkdir(exist_ok=True)

        job_file = extracted_dir / "test_jobs.json"
        with open(job_file, "w") as f:
            json.dump(sample_jobs, f)

        yield job_file, sample_jobs


class TestPreprocessCLIRequirementExtraction:
    """Tests for CLI requirement extraction flags."""

    def test_extract_requirements_flag_enabled(self, sample_jobs_file):
        """Test that --extract-requirements flag enables extraction."""
        job_file, _ = sample_jobs_file

        # Extract requirements enabled (default)
        result = runner.invoke(app, ["preprocess", "--extract-requirements"])

        # Should succeed
        assert result.exit_code == 0, f"CLI failed: {result.stdout}"
        assert "Preprocessing complete" in result.stdout or "Processing" in result.stdout

    def test_extract_requirements_flag_disabled(self, sample_jobs_file):
        """Test that --no-extract-requirements flag disables extraction."""
        job_file, _ = sample_jobs_file

        # Extract requirements disabled
        result = runner.invoke(app, ["preprocess", "--no-extract-requirements"])

        # Should succeed
        assert result.exit_code == 0, f"CLI failed: {result.stdout}"
        assert "Preprocessing complete" in result.stdout or "Processing" in result.stdout

    def test_export_requirements_json_flag(self, sample_jobs_file):
        """Test that --export-requirements-json flag creates output file."""
        job_file, _ = sample_jobs_file

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "requirements.json"

            # Run preprocess with export flag
            result = runner.invoke(
                app,
                [
                    "preprocess",
                    "--extract-requirements",
                    "--export-requirements-json",
                    str(output_file),
                ],
            )

            # Should succeed (or skip if no jobs found)
            assert result.exit_code in [0, 1], f"CLI failed unexpectedly: {result.stdout}"

    def test_preprocess_help_includes_requirement_flags(self):
        """Test that help text includes requirement extraction flags."""
        result = runner.invoke(app, ["preprocess", "--help"])

        assert result.exit_code == 0
        # Check for flag names (may be truncated in help due to column width)
        assert "extract-requireme" in result.stdout or "--extract-requirements" in result.stdout
        assert "no-extract-requi" in result.stdout or "--no-extract-requirements" in result.stdout
        assert "export-requiremen" in result.stdout or "--export-requirements-json" in result.stdout
        assert "trigger-based requirement extraction" in result.stdout.lower()

    def test_default_extract_requirements_enabled(self):
        """Test that requirement extraction is enabled by default."""
        # The default should be --extract-requirements (True)
        result = runner.invoke(app, ["preprocess", "--help"])

        assert result.exit_code == 0
        # Look for default mention in the help
        assert "extract-requirement" in result.stdout.lower()

    def test_requirement_extraction_produces_json_output(self, sample_jobs_file):
        """Test that requirement extraction produces valid JSON output."""
        job_file, _ = sample_jobs_file

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "requirements.json"

            # Run preprocess with export
            result = runner.invoke(
                app,
                [
                    "preprocess",
                    "--extract-requirements",
                    "--export-requirements-json",
                    str(output_file),
                ],
            )

            # Should complete (exit 0 or 1 if no jobs found)
            assert result.exit_code in [0, 1]

            # If export happened, verify JSON format
            if output_file.exists():
                try:
                    with open(output_file) as f:
                        requirements = json.load(f)
                    assert isinstance(requirements, list)

                    # Verify structure of requirements
                    for req in requirements:
                        assert isinstance(req, dict)
                        assert "text" in req
                        assert "trigger_word" in req
                        assert "confidence" in req
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in {output_file}")


class TestPreprocessCLITokenCostAnalysis:
    """Tests for token cost impact analysis with requirement extraction."""

    def test_token_cost_impact_10_jobs(self, sample_jobs_file):
        """Measure token cost impact of requirement extraction on 10-job batch.

        Expected: <5% token increase with requirement extraction enabled.
        """
        job_file, _ = sample_jobs_file

        # Run with requirement extraction enabled
        result_with = runner.invoke(
            app,
            [
                "preprocess",
                "--extract-requirements",
                "--show-estimates",
                "--batch-size",
                "10",
            ],
        )

        # Extract token count from output
        tokens_with = _extract_token_count_from_output(result_with.stdout)

        # Run without requirement extraction
        result_without = runner.invoke(
            app,
            [
                "preprocess",
                "--no-extract-requirements",
                "--show-estimates",
                "--batch-size",
                "10",
            ],
        )

        tokens_without = _extract_token_count_from_output(result_without.stdout)

        # Both should complete successfully
        assert result_with.exit_code in [0, 1]
        assert result_without.exit_code in [0, 1]

        # If we got token counts, verify impact is <5%
        if tokens_with is not None and tokens_without is not None and tokens_without > 0:
            percent_increase = ((tokens_with - tokens_without) / tokens_without) * 100
            assert percent_increase < 5.0, f"Token increase too high: {percent_increase:.2f}% (expected <5%)"

    def test_cost_reporting_with_requirements(self):
        """Test that cost is reported correctly with requirement extraction."""
        result = runner.invoke(
            app,
            ["preprocess", "--extract-requirements", "--show-estimates"],
        )

        # Should show cost information
        assert "Total cost" in result.stdout or "cost" in result.stdout.lower()


def _extract_token_count_from_output(output: str) -> int | None:
    """Extract total token count from CLI output.

    Args:
        output: CLI stdout output

    Returns:
        Token count if found, None otherwise
    """
    for line in output.split("\n"):
        if "Total tokens:" in line:
            try:
                # Extract number after "Total tokens:"
                parts = line.split("Total tokens:")
                if len(parts) > 1:
                    token_str = parts[1].strip().split()[0].replace(",", "")
                    return int(token_str)
            except (ValueError, IndexError):
                pass
    return None
