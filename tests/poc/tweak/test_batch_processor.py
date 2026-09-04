"""Tests for POC Batch Processor for multi-job markdown pipeline.

Tests validate:
1. Job loading from JSON array
2. Error handling for non-array input
3. Error handling for missing description field
4. Empty array handling
5. Full batch processing integration
"""

import json
from pathlib import Path

import pytest

from src.poc.tweak.batch_processor import JobResult, load_jobs, run_batch


class TestLoadJobs:
    """Tests for load_jobs() function."""

    def test_load_jobs_valid_array_returns_list_of_dicts(self, tmp_path):
        """Test loading valid JSON array of job records."""
        # Arrange
        fixture_path = Path(__file__).parent.parent / "fixtures" / "details_test_fixture.json"

        # Act
        jobs = load_jobs(str(fixture_path))

        # Assert
        assert isinstance(jobs, list)
        assert len(jobs) == 4, "Fixture should contain 4 job records"
        assert all(isinstance(job, dict) for job in jobs)
        assert all("description" in job for job in jobs)

    def test_load_jobs_non_array_raises_valueerror(self, tmp_path):
        """Test that non-array JSON raises ValueError with clear message."""
        # Arrange
        test_file = tmp_path / "non_array.json"
        test_file.write_text(json.dumps({"job": "single_object"}))

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            load_jobs(str(test_file))

        assert "Expected JSON array at root" in str(exc_info.value)
        assert "got dict" in str(exc_info.value)

    def test_load_jobs_missing_description_field_raises_valueerror(self, tmp_path):
        """Test that records without description field raise ValueError."""
        # Arrange
        test_file = tmp_path / "missing_description.json"
        test_file.write_text(
            json.dumps(
                [
                    {
                        "id": "job1",
                        "title": "Developer",
                        "company": "Acme",
                        # Missing "description" field
                    }
                ]
            )
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            load_jobs(str(test_file))

        assert "missing 'description' field" in str(exc_info.value)
        assert "job1" in str(exc_info.value)

    def test_load_jobs_empty_array_returns_empty_list(self, tmp_path):
        """Test that empty JSON array returns empty list without error."""
        # Arrange
        test_file = tmp_path / "empty_array.json"
        test_file.write_text(json.dumps([]))

        # Act
        jobs = load_jobs(str(test_file))

        # Assert
        assert jobs == []

    def test_load_jobs_file_not_found_raises_error(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            load_jobs(str(tmp_path / "nonexistent.json"))


class TestRunBatch:
    """Tests for run_batch() integration."""

    def test_run_batch_processes_4_jobs_from_fixture(self):
        """Test full batch processing on fixture with 4 jobs."""
        # Arrange
        fixture_path = Path(__file__).parent.parent / "fixtures" / "details_test_fixture.json"

        # Act
        results = run_batch(str(fixture_path))

        # Assert
        assert isinstance(results, list)
        assert len(results) == 4, "Should process all 4 jobs from fixture"

        # Verify each result
        for result in results:
            assert isinstance(result, JobResult)
            assert result.job_id, "Job ID should be set"
            assert result.title, "Title should be set"
            assert result.company, "Company should be set"
            assert result.sections_detected >= 0, "Sections detected should be non-negative"
            assert result.keyword_matches >= 0, "Keyword matches should be non-negative"
            assert 0.0 <= result.confidence_min <= 1.0, "Min confidence should be in [0,1]"
            assert 0.0 <= result.confidence_max <= 1.0, "Max confidence should be in [0,1]"
            assert 0.0 <= result.confidence_avg <= 1.0, "Avg confidence should be in [0,1]"

        # Verify confidence constraints
        for result in results:
            if result.sections_detected > 0:
                # If sections were detected, confidence scores should be reasonable
                assert result.confidence_max >= result.confidence_min, "Max confidence should be >= min confidence"
                assert result.confidence_avg >= result.confidence_min, "Avg confidence should be >= min confidence"
                assert result.confidence_avg <= result.confidence_max, "Avg confidence should be <= max confidence"
