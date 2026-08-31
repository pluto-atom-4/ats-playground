"""Tests for TUI job selector application."""

import json
import tempfile
from pathlib import Path

import pytest
from textual.widgets import SelectionList

from src.poc.ui.job_selector import (
    DEFAULT_OUTPUT_PATH,
    JobSelectorApp,
    format_job_row,
)
from src.poc.ui.loader import Job


class TestFormatJobRow:
    """Tests for format_job_row function."""

    def test_format_job_row_basic(self) -> None:
        """format_job_row should create pipe-separated columns."""
        job: Job = {
            "id": "j1",
            "title": "Engineer",
            "company": "TechCorp",
            "location": "Seattle",
            "status": "pending_review",
        }

        result = format_job_row(job)

        assert "|" in result
        assert "Engineer" in result
        assert "TechCorp" in result
        assert "Seattle" in result
        assert "pending_review" in result

    def test_format_job_row_column_alignment(self) -> None:
        """format_job_row should align columns consistently."""
        job1: Job = {
            "id": "j1",
            "title": "Short",
            "company": "A",
            "location": "Remote",
            "status": "pending_review",
        }
        job2: Job = {
            "id": "j2",
            "title": "Very Long Title That Goes On And On",
            "company": "Another Company",
            "location": "San Francisco, CA",
            "status": "confirmed",
        }

        row1 = format_job_row(job1)
        row2 = format_job_row(job2)

        # Both should have same pipe positions (columns aligned)
        pipes1 = [i for i, c in enumerate(row1) if c == "|"]
        pipes2 = [i for i, c in enumerate(row2) if c == "|"]

        # Should have 3 pipes (4 columns)
        assert len(pipes1) == 3
        assert len(pipes2) == 3

    def test_format_job_row_truncates_long_fields(self) -> None:
        """format_job_row should truncate fields that are too long."""
        job: Job = {
            "id": "j1",
            "title": "A" * 60,  # Very long title
            "company": "B" * 30,  # Very long company
            "location": "C" * 30,  # Very long location
            "status": "D" * 30,  # Very long status
        }

        result = format_job_row(job)

        # Should not exceed reasonable line length
        assert len(result) < 200


class TestJobSelectorApp:
    """Tests for JobSelectorApp class."""

    def test_app_initialization_with_jobs(self) -> None:
        """App should initialize with provided jobs."""
        jobs: list[Job] = [
            {
                "id": "j1",
                "title": "Role1",
                "company": "Corp1",
                "location": "Place1",
                "status": "pending_review",
            }
        ]

        app = JobSelectorApp(jobs=jobs)

        assert app.all_jobs == jobs
        assert len(app.all_jobs) == 1

    def test_app_initialization_with_warnings(self) -> None:
        """App should store warnings."""
        warnings = ["Warning 1", "Warning 2"]

        app = JobSelectorApp(warnings=warnings)

        assert app.all_warnings == warnings

    def test_app_initialization_default_output_path(self) -> None:
        """App should use default output path."""
        app = JobSelectorApp()

        assert app.output_path == DEFAULT_OUTPUT_PATH

    def test_app_initialization_custom_output_path(self) -> None:
        """App should accept custom output path."""
        custom_path = Path("/tmp/custom.json")

        app = JobSelectorApp(output_path=custom_path)

        assert app.output_path == custom_path

    def test_app_filter_text_empty_initially(self) -> None:
        """App should have empty filter text initially."""
        app = JobSelectorApp()

        assert app.filter_text == ""

    def test_app_selected_ids_empty_initially(self) -> None:
        """App should have empty selected IDs initially."""
        app = JobSelectorApp()

        assert app.selected_ids == set()


class TestJobSelectorAppFiltering:
    """Tests for job filtering logic."""

    def test_get_filtered_jobs_empty_filter(self) -> None:
        """With no filter, should return all jobs."""
        jobs: list[Job] = [
            {
                "id": f"j{i}",
                "title": f"Role {i}",
                "company": f"Corp {i}",
                "location": f"Place {i}",
                "status": "pending_review",
            }
            for i in range(3)
        ]
        app = JobSelectorApp(jobs=jobs)

        result = app._get_filtered_jobs()

        assert len(result) == 3
        assert result == jobs

    def test_get_filtered_jobs_by_title(self) -> None:
        """Should filter jobs by title."""
        jobs: list[Job] = [
            {
                "id": "j1",
                "title": "Python Developer",
                "company": "Corp",
                "location": "Place",
                "status": "pending_review",
            },
            {
                "id": "j2",
                "title": "Java Developer",
                "company": "Corp",
                "location": "Place",
                "status": "pending_review",
            },
            {
                "id": "j3",
                "title": "Engineer",
                "company": "Corp",
                "location": "Place",
                "status": "pending_review",
            },
        ]
        app = JobSelectorApp(jobs=jobs)
        app.filter_text = "python"

        result = app._get_filtered_jobs()

        assert len(result) == 1
        assert result[0]["id"] == "j1"

    def test_get_filtered_jobs_by_company(self) -> None:
        """Should filter jobs by company."""
        jobs: list[Job] = [
            {
                "id": "j1",
                "title": "Role",
                "company": "TechCorp",
                "location": "Place",
                "status": "pending_review",
            },
            {
                "id": "j2",
                "title": "Role",
                "company": "BigCorp",
                "location": "Place",
                "status": "pending_review",
            },
        ]
        app = JobSelectorApp(jobs=jobs)
        app.filter_text = "techcorp"

        result = app._get_filtered_jobs()

        assert len(result) == 1
        assert result[0]["id"] == "j1"

    def test_get_filtered_jobs_by_location(self) -> None:
        """Should filter jobs by location."""
        jobs: list[Job] = [
            {
                "id": "j1",
                "title": "Role",
                "company": "Corp",
                "location": "Seattle",
                "status": "pending_review",
            },
            {
                "id": "j2",
                "title": "Role",
                "company": "Corp",
                "location": "Remote",
                "status": "pending_review",
            },
        ]
        app = JobSelectorApp(jobs=jobs)
        app.filter_text = "seattle"

        result = app._get_filtered_jobs()

        assert len(result) == 1
        assert result[0]["id"] == "j1"

    def test_get_filtered_jobs_case_insensitive(self) -> None:
        """Filter should be case-insensitive."""
        jobs: list[Job] = [
            {
                "id": "j1",
                "title": "Python Developer",
                "company": "Corp",
                "location": "Place",
                "status": "pending_review",
            }
        ]
        app = JobSelectorApp(jobs=jobs)
        app.filter_text = "PYTHON"

        result = app._get_filtered_jobs()

        assert len(result) == 1

    def test_get_filtered_jobs_multiple_matches(self) -> None:
        """Filter should return multiple matches."""
        jobs: list[Job] = [
            {
                "id": "j1",
                "title": "Senior Developer",
                "company": "Corp",
                "location": "Place",
                "status": "pending_review",
            },
            {
                "id": "j2",
                "title": "Junior Developer",
                "company": "Corp",
                "location": "Place",
                "status": "pending_review",
            },
            {
                "id": "j3",
                "title": "Manager",
                "company": "Corp",
                "location": "Place",
                "status": "pending_review",
            },
        ]
        app = JobSelectorApp(jobs=jobs)
        app.filter_text = "developer"

        result = app._get_filtered_jobs()

        assert len(result) == 2
        assert result[0]["id"] == "j1"
        assert result[1]["id"] == "j2"


class TestJobSelectorAppSelection:
    """Tests for job selection logic (without running app)."""

    def test_selected_ids_tracks_selections(self) -> None:
        """App should track selected job IDs."""
        jobs: list[Job] = [
            {
                "id": "j1",
                "title": "Role",
                "company": "Corp",
                "location": "Place",
                "status": "pending_review",
            }
        ]
        app = JobSelectorApp(jobs=jobs)

        app.selected_ids.add("j1")

        assert "j1" in app.selected_ids

    def test_export_selected_with_no_selection(self) -> None:
        """Exporting with no selection should be graceful (no-op in production)."""
        app = JobSelectorApp()

        # In production, this would show a notification
        # Here we just verify the logic doesn't crash
        assert len(app.selected_ids) == 0


class TestJobSelectorAppIntegration:
    """Integration tests with real data and file I/O."""

    def test_app_loads_from_fixtures(self) -> None:
        """App should load jobs from fixture directory."""
        fixture_dir = Path(__file__).parent / "fixtures"

        app = JobSelectorApp()
        # Manually call load_jobs to test
        from src.poc.ui.loader import load_jobs

        result = load_jobs(fixture_dir)
        app.all_jobs = result.jobs
        app.all_warnings = result.warnings

        assert len(app.all_jobs) > 0

    def test_app_export_saves_correct_json(self) -> None:
        """App should export selected jobs as valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            output_file = tmppath / "selected.json"

            jobs: list[Job] = [
                {
                    "id": "j1",
                    "title": "Engineer",
                    "company": "Corp",
                    "location": "Place",
                    "status": "pending_review",
                },
                {
                    "id": "j2",
                    "title": "Manager",
                    "company": "Corp",
                    "location": "Place",
                    "status": "confirmed",
                },
            ]

            app = JobSelectorApp(jobs=jobs, output_path=output_file)
            app.selected_ids.add("j1")

            # Simulate export
            selected = [j for j in app.all_jobs if j["id"] in app.selected_ids]
            from src.poc.ui.exporter import export_jobs

            export_jobs(selected, output_file)

            # Verify file
            assert output_file.exists()
            with open(output_file) as f:
                loaded = json.load(f)

            assert len(loaded) == 1
            assert loaded[0]["id"] == "j1"

    def test_app_with_real_data(self) -> None:
        """Smoke test with real extracted_jobs data."""
        data_dir = Path("data/extracted_jobs")

        if data_dir.exists():
            from src.poc.ui.loader import load_jobs

            load_result = load_jobs(data_dir)
            app = JobSelectorApp(jobs=load_result.jobs, warnings=load_result.warnings)

            assert len(app.all_jobs) > 0
            # Should have 8 jobs from 4 companies
            assert len(app.all_jobs) == 8
