"""Unit tests for cost tracking models (Phase 3A)."""

import pytest

from src.storage.cost_models import CostComparisonReport, ReprocessingMetrics


class TestReprocessingMetrics:
    """Test ReprocessingMetrics dataclass."""

    def test_tokens_saved(self) -> None:
        """Test tokens_saved calculation."""
        metrics = ReprocessingMetrics(
            job_id="job_123",
            preprocessing_version_before="v1.0",
            preprocessing_version_after="v2.0",
            tokens_before=1000,
            tokens_after=650,
            estimated_cost_before=0.003,
            estimated_cost_after=0.00195,
        )

        assert metrics.tokens_saved == 350

    def test_cost_saved_usd(self) -> None:
        """Test cost_saved_usd calculation."""
        metrics = ReprocessingMetrics(
            job_id="job_123",
            preprocessing_version_before="v1.0",
            preprocessing_version_after="v2.0",
            tokens_before=1000,
            tokens_after=650,
            estimated_cost_before=0.003,
            estimated_cost_after=0.00195,
        )

        assert metrics.cost_saved_usd == pytest.approx(0.00105, abs=1e-5)

    def test_token_reduction_percent(self) -> None:
        """Test token_reduction_percent calculation."""
        metrics = ReprocessingMetrics(
            job_id="job_123",
            preprocessing_version_before="v1.0",
            preprocessing_version_after="v2.0",
            tokens_before=1000,
            tokens_after=650,
            estimated_cost_before=0.003,
            estimated_cost_after=0.00195,
        )

        assert metrics.token_reduction_percent == pytest.approx(35.0, abs=0.1)

    def test_token_reduction_percent_zero_before(self) -> None:
        """Test token_reduction_percent when tokens_before is 0."""
        metrics = ReprocessingMetrics(
            job_id="job_123",
            preprocessing_version_before="v1.0",
            preprocessing_version_after="v2.0",
            tokens_before=0,
            tokens_after=0,
            estimated_cost_before=0.0,
            estimated_cost_after=0.0,
        )

        assert metrics.token_reduction_percent == 0.0

    def test_no_tokens_saved(self) -> None:
        """Test when token count doesn't change."""
        metrics = ReprocessingMetrics(
            job_id="job_123",
            preprocessing_version_before="v1.0",
            preprocessing_version_after="v2.0",
            tokens_before=1000,
            tokens_after=1000,
            estimated_cost_before=0.003,
            estimated_cost_after=0.003,
        )

        assert metrics.tokens_saved == 0
        assert metrics.cost_saved_usd == pytest.approx(0.0, abs=1e-6)
        assert metrics.token_reduction_percent == pytest.approx(0.0, abs=0.1)


class TestCostComparisonReport:
    """Test CostComparisonReport dataclass."""

    def test_empty_report(self) -> None:
        """Test default empty report."""
        report = CostComparisonReport()

        assert report.total_jobs_v1_0 == 0
        assert report.total_jobs_v2_0 == 0
        assert report.total_tokens_v1_0 == 0
        assert report.total_tokens_v2_0 == 0
        assert report.estimated_savings_usd == 0.0
        assert report.avg_tokens_per_job_v1_0 == 0.0
        assert report.avg_tokens_per_job_v2_0 == 0.0

    def test_migration_progress_percent_all_v1(self) -> None:
        """Test migration progress when all jobs are v1.0."""
        report = CostComparisonReport(
            total_jobs_v1_0=100,
            total_jobs_v2_0=0,
        )

        assert report.migration_progress_percent == pytest.approx(0.0, abs=0.1)

    def test_migration_progress_percent_all_v2(self) -> None:
        """Test migration progress when all jobs are v2.0."""
        report = CostComparisonReport(
            total_jobs_v1_0=0,
            total_jobs_v2_0=100,
        )

        assert report.migration_progress_percent == pytest.approx(100.0, abs=0.1)

    def test_migration_progress_percent_mixed(self) -> None:
        """Test migration progress with mixed versions."""
        report = CostComparisonReport(
            total_jobs_v1_0=75,
            total_jobs_v2_0=25,
        )

        assert report.migration_progress_percent == pytest.approx(25.0, abs=0.1)

    def test_avg_token_reduction_percent_no_runs(self) -> None:
        """Test avg token reduction with no re-processing runs."""
        report = CostComparisonReport(
            reprocessing_runs=[],
            total_reprocessing_tokens_saved=0,
            total_tokens_v1_0=1000,
        )

        assert report.avg_token_reduction_percent == pytest.approx(0.0, abs=0.1)

    def test_avg_token_reduction_percent_with_runs(self) -> None:
        """Test avg token reduction with re-processing runs."""
        metrics = ReprocessingMetrics(
            job_id="job_1",
            preprocessing_version_before="v1.0",
            preprocessing_version_after="v2.0",
            tokens_before=1000,
            tokens_after=650,
            estimated_cost_before=0.003,
            estimated_cost_after=0.00195,
        )

        report = CostComparisonReport(
            total_tokens_v1_0=1000,
            total_reprocessing_tokens_saved=350,
            reprocessing_runs=[metrics],
        )

        assert report.avg_token_reduction_percent == pytest.approx(35.0, abs=0.1)

    def test_avg_token_reduction_percent_zero_tokens(self) -> None:
        """Test avg token reduction when total_tokens_v1_0 is 0."""
        report = CostComparisonReport(
            total_tokens_v1_0=0,
            total_reprocessing_tokens_saved=350,
        )

        assert report.avg_token_reduction_percent == pytest.approx(0.0, abs=0.1)

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        report = CostComparisonReport(
            total_jobs_v1_0=50,
            total_jobs_v2_0=30,
            total_tokens_v1_0=50000,
            total_tokens_v2_0=35000,
            estimated_savings_usd=0.045,
            avg_tokens_per_job_v1_0=1000.0,
            avg_tokens_per_job_v2_0=1166.67,
            jobs_already_migrated=30,
            jobs_pending_migration=50,
            total_reprocessing_cost_saved=0.020,
            total_reprocessing_tokens_saved=5000,
        )

        report_dict = report.to_dict()

        assert report_dict["total_jobs_v1_0"] == 50
        assert report_dict["total_jobs_v2_0"] == 30
        assert report_dict["total_tokens_v1_0"] == 50000
        assert report_dict["total_tokens_v2_0"] == 35000
        assert isinstance(report_dict["estimated_savings_usd"], float)
        assert isinstance(report_dict["migration_progress_percent"], float)
        assert isinstance(report_dict["avg_token_reduction_percent"], float)

    def test_report_with_reprocessing_runs(self) -> None:
        """Test report with multiple re-processing runs."""
        metrics1 = ReprocessingMetrics(
            job_id="job_1",
            preprocessing_version_before="v1.0",
            preprocessing_version_after="v2.0",
            tokens_before=1000,
            tokens_after=650,
            estimated_cost_before=0.003,
            estimated_cost_after=0.00195,
        )

        metrics2 = ReprocessingMetrics(
            job_id="job_2",
            preprocessing_version_before="v1.0",
            preprocessing_version_after="v2.0",
            tokens_before=800,
            tokens_after=520,
            estimated_cost_before=0.0024,
            estimated_cost_after=0.00156,
        )

        report = CostComparisonReport(
            total_jobs_v1_0=100,
            total_jobs_v2_0=50,
            reprocessing_runs=[metrics1, metrics2],
            total_reprocessing_tokens_saved=630,
            total_reprocessing_cost_saved=0.00189,
        )

        assert len(report.reprocessing_runs) == 2
        assert report.total_reprocessing_tokens_saved == 630
        assert report.total_reprocessing_cost_saved == pytest.approx(0.00189, abs=1e-5)
