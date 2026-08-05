"""Data models for cost analysis and comparison reporting."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ReprocessingMetrics:
    """Metrics for a single re-preprocessing run."""

    job_id: str
    preprocessing_version_before: str
    preprocessing_version_after: str
    tokens_before: int
    tokens_after: int
    estimated_cost_before: float
    estimated_cost_after: float
    timestamp: Optional[str] = None

    @property
    def tokens_saved(self) -> int:
        """Calculate tokens saved by re-preprocessing."""
        return self.tokens_before - self.tokens_after

    @property
    def cost_saved_usd(self) -> float:
        """Calculate USD cost saved by re-preprocessing."""
        return self.estimated_cost_before - self.estimated_cost_after

    @property
    def token_reduction_percent(self) -> float:
        """Calculate token reduction as percentage."""
        if self.tokens_before == 0:
            return 0.0
        return ((self.tokens_before - self.tokens_after) / self.tokens_before) * 100


@dataclass
class CostComparisonReport:
    """Comprehensive cost analysis report for v1.0 vs v2.0 preprocessing."""

    total_jobs_v1_0: int = 0
    total_jobs_v2_0: int = 0
    total_tokens_v1_0: int = 0
    total_tokens_v2_0: int = 0
    estimated_savings_usd: float = 0.0
    avg_tokens_per_job_v1_0: float = 0.0
    avg_tokens_per_job_v2_0: float = 0.0
    jobs_already_migrated: int = 0
    jobs_pending_migration: int = 0
    reprocessing_runs: List[ReprocessingMetrics] = field(default_factory=list)
    total_reprocessing_cost_saved: float = 0.0
    total_reprocessing_tokens_saved: int = 0

    @property
    def avg_token_reduction_percent(self) -> float:
        """Calculate average token reduction percentage across all re-preprocessing runs."""
        if not self.reprocessing_runs:
            return 0.0
        if self.total_tokens_v1_0 == 0:
            return 0.0
        return (
            (self.total_reprocessing_tokens_saved / self.total_tokens_v1_0) * 100 if self.total_tokens_v1_0 > 0 else 0.0
        )

    @property
    def migration_progress_percent(self) -> float:
        """Calculate migration progress as percentage."""
        total = self.total_jobs_v1_0 + self.total_jobs_v2_0
        if total == 0:
            return 0.0
        return (self.total_jobs_v2_0 / total) * 100

    def to_dict(self) -> dict:
        """Convert report to dictionary for serialization."""
        return {
            "total_jobs_v1_0": self.total_jobs_v1_0,
            "total_jobs_v2_0": self.total_jobs_v2_0,
            "total_tokens_v1_0": self.total_tokens_v1_0,
            "total_tokens_v2_0": self.total_tokens_v2_0,
            "estimated_savings_usd": round(self.estimated_savings_usd, 6),
            "avg_tokens_per_job_v1_0": round(self.avg_tokens_per_job_v1_0, 2),
            "avg_tokens_per_job_v2_0": round(self.avg_tokens_per_job_v2_0, 2),
            "jobs_already_migrated": self.jobs_already_migrated,
            "jobs_pending_migration": self.jobs_pending_migration,
            "total_reprocessing_cost_saved": round(self.total_reprocessing_cost_saved, 6),
            "total_reprocessing_tokens_saved": self.total_reprocessing_tokens_saved,
            "avg_token_reduction_percent": round(self.avg_token_reduction_percent, 2),
            "migration_progress_percent": round(self.migration_progress_percent, 2),
            "reprocessing_runs": len(self.reprocessing_runs),
        }
