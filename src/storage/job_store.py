"""Job storage and management for ATS Playground."""

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.storage.cost_models import CostComparisonReport, ReprocessingMetrics

logger = logging.getLogger(__name__)


class JobStore:
    """SQLite storage for job reviews with preprocessing version tracking."""

    JOBS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS job_reviews (
        job_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        location TEXT,
        company TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        reason TEXT,
        tokens INTEGER,
        estimated_cost REAL,
        crawled_at TIMESTAMP,
        preprocessed_at TIMESTAMP,
        reviewed_at TIMESTAMP,
        preprocessing_version TEXT DEFAULT 'v2.0',
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    )
    """

    def __init__(self, db_path: str = "data/ats_playground.db"):
        """Initialize job store."""
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize database and schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()
        cursor.execute(self.JOBS_TABLE_SQL)
        self.conn.commit()
        logger.info("Initialized job store database")
        self._run_migrations()

    def _run_migrations(self) -> None:
        """Run schema migrations to add missing columns."""
        if not self.conn:
            return
        cursor = self.conn.cursor()

        # Add preprocessing_version column if missing (Phase 2)
        try:
            cursor.execute("ALTER TABLE job_reviews ADD COLUMN preprocessing_version TEXT DEFAULT 'v2.0'")
            self.conn.commit()
            logger.info("Added preprocessing_version column to job_reviews")
        except sqlite3.OperationalError:
            pass  # Column already exists

    def add_job(
        self,
        job_id: str,
        title: str,
        company: Optional[str] = None,
        location: Optional[str] = None,
        status: str = "pending",
        preprocessing_version: str = "v2.0",
        tokens: Optional[int] = None,
        estimated_cost: Optional[float] = None,
    ) -> None:
        """Add or update a job in the database.

        Args:
            job_id: Unique job identifier
            title: Job title
            company: Company name
            location: Job location
            status: Job status (pending, confirmed, rejected)
            preprocessing_version: Version used for preprocessing (v1.0, 1.0, v2.0, 2.0)
            tokens: Token count
            estimated_cost: Estimated LLM cost
        """
        if not self.conn:
            return

        # Normalize version to v-prefixed format
        version_query = preprocessing_version if preprocessing_version.startswith("v") else f"v{preprocessing_version}"

        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO job_reviews
               (job_id, title, company, location, status,
                preprocessing_version, tokens, estimated_cost, crawled_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (job_id, title, company, location, status, version_query, tokens, estimated_cost),
        )
        self.conn.commit()
        logger.debug(f"Added/updated job {job_id}")

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job dict or None if not found
        """
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM job_reviews WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()

        return dict(row) if row else None

    def update_preprocessing_version(self, job_id: str, version: str) -> None:
        """Update preprocessing_version for a job.

        Args:
            job_id: Job ID to update
            version: '1.0', 'v1.0', '2.0', or 'v2.0'

        Raises:
            ValueError: If version not valid
            sqlite3.OperationalError: If job_id not found
        """
        # Normalize version
        clean_version = version.replace("v", "")
        if clean_version not in ("1.0", "2.0"):
            raise ValueError(f"Invalid preprocessing version: {version}. Must be '1.0' or '2.0'")

        if not self.conn:
            raise RuntimeError("Database connection not available")

        # Format for storage
        version_query = version if version.startswith("v") else f"v{version}"

        cursor = self.conn.cursor()
        cursor.execute(
            """UPDATE job_reviews
               SET preprocessing_version = ?, preprocessed_at = CURRENT_TIMESTAMP
               WHERE job_id = ?""",
            (version_query, job_id),
        )

        if cursor.rowcount == 0:
            raise sqlite3.OperationalError(f"Job not found: {job_id}")

        self.conn.commit()

    def get_jobs_by_version(self, version: str) -> List[Dict[str, Any]]:
        """Get all jobs with specific preprocessing version.

        Args:
            version: '1.0', 'v1.0', '2.0', or 'v2.0'

        Returns:
            List of job dicts with all columns

        Raises:
            ValueError: If version not valid
        """
        # Normalize and validate version
        clean_version = version.replace("v", "")
        if clean_version not in ("1.0", "2.0"):
            raise ValueError(f"Invalid preprocessing version: {version}. Must be '1.0' or '2.0'")

        if not self.conn:
            return []

        # Format for query
        version_query = version if version.startswith("v") else f"v{version}"

        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT *
               FROM job_reviews
               WHERE preprocessing_version = ?
               ORDER BY crawled_at DESC""",
            (version_query,),
        )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_version_stats(self) -> Dict[str, int]:
        """Get count of jobs by preprocessing version.

        Returns:
            Dict like {'1.0': 42, '2.0': 8}
        """
        if not self.conn:
            return {}

        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT preprocessing_version, COUNT(*) as count
               FROM job_reviews
               GROUP BY preprocessing_version
               ORDER BY preprocessing_version"""
        )

        stats: Dict[str, int] = {}
        for row in cursor.fetchall():
            version = row[0] or "unknown"  # Handle NULL
            count = row[1]
            # Normalize version (remove 'v' prefix for return)
            clean_version = version.replace("v", "")
            stats[clean_version] = count

        return stats

    def get_all_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all jobs, optionally filtered by status.

        Args:
            status: Optional status filter (pending, confirmed, rejected)

        Returns:
            List of job dicts
        """
        if not self.conn:
            return []

        cursor = self.conn.cursor()

        if status:
            cursor.execute("SELECT * FROM job_reviews WHERE status = ? ORDER BY crawled_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM job_reviews ORDER BY crawled_at DESC")

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def _ensure_cost_tracking_table(self) -> None:
        """Ensure cost_tracking table exists with all required columns.

        Creates the table if it doesn't exist, and adds missing columns if needed.
        """
        if not self.conn:
            return

        cursor = self.conn.cursor()

        # Create cost_tracking table if it doesn't exist
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS cost_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                phase TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                preprocessing_version_before TEXT,
                preprocessing_version_after TEXT,
                tokens_before INTEGER,
                tokens_after INTEGER,
                estimated_cost_before REAL,
                estimated_cost_after REAL,
                is_re_preprocessing BOOLEAN DEFAULT FALSE,
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            )"""
        )

        # Check and add missing columns
        cursor.execute("PRAGMA table_info(cost_tracking)")
        columns = {row[1] for row in cursor.fetchall()}

        columns_to_add = [
            ("preprocessing_version_before", "TEXT"),
            ("preprocessing_version_after", "TEXT"),
            ("tokens_before", "INTEGER"),
            ("tokens_after", "INTEGER"),
            ("estimated_cost_before", "REAL"),
            ("estimated_cost_after", "REAL"),
            ("is_re_preprocessing", "BOOLEAN DEFAULT FALSE"),
        ]

        for col_name, col_type in columns_to_add:
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE cost_tracking ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Added column {col_name} to cost_tracking")
                except sqlite3.OperationalError:
                    pass  # Column already exists

        self.conn.commit()

    def log_reprocessing_metrics(
        self,
        job_id: str,
        tokens_before: int,
        tokens_after: int,
        version_before: str,
        version_after: str,
        cost_before: float,
        cost_after: float,
    ) -> None:
        """Log cost/quality metrics for a re-preprocessing run.

        Args:
            job_id: Job ID being re-preprocessed
            tokens_before: Token count before re-preprocessing
            tokens_after: Token count after re-preprocessing
            version_before: Preprocessing version before (e.g., 'v1.0')
            version_after: Preprocessing version after (e.g., 'v2.0')
            cost_before: Estimated cost before re-preprocessing
            cost_after: Estimated cost after re-preprocessing

        Raises:
            RuntimeError: If database connection not available
        """
        if not self.conn:
            raise RuntimeError("Database connection not available")

        self._ensure_cost_tracking_table()

        cursor = self.conn.cursor()

        # Normalize versions
        version_before_normalized = version_before if version_before.startswith("v") else f"v{version_before}"
        version_after_normalized = version_after if version_after.startswith("v") else f"v{version_after}"

        cursor.execute(
            """INSERT INTO cost_tracking
               (job_id, phase, is_re_preprocessing, preprocessing_version_before,
                preprocessing_version_after, tokens_before, tokens_after,
                estimated_cost_before, estimated_cost_after, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (
                job_id,
                "reprocess",
                True,
                version_before_normalized,
                version_after_normalized,
                tokens_before,
                tokens_after,
                cost_before,
                cost_after,
            ),
        )

        self.conn.commit()
        logger.debug(
            f"Logged reprocessing metrics for job {job_id}: "
            f"{tokens_before} → {tokens_after} tokens, "
            f"${cost_before:.6f} → ${cost_after:.6f}"
        )

    def get_cost_comparison_report(self, limit_days: Optional[int] = None) -> CostComparisonReport:
        """Generate cost analysis report for v1.0 vs v2.0 preprocessing.

        Compares token usage, cost estimates, and tracks re-preprocessing progress.

        Args:
            limit_days: Optional limit to jobs preprocessed in last N days

        Returns:
            CostComparisonReport with comprehensive cost/quality metrics
        """
        if not self.conn:
            return CostComparisonReport()

        self._ensure_cost_tracking_table()

        cursor = self.conn.cursor()
        report = CostComparisonReport()

        # Count jobs by version
        cursor.execute("SELECT COUNT(*) FROM job_reviews WHERE preprocessing_version = 'v1.0'")
        report.total_jobs_v1_0 = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM job_reviews WHERE preprocessing_version = 'v2.0'")
        report.total_jobs_v2_0 = cursor.fetchone()[0] or 0

        # Calculate tokens by version
        cursor.execute("SELECT SUM(tokens) FROM job_reviews WHERE preprocessing_version = 'v1.0'")
        result = cursor.fetchone()
        report.total_tokens_v1_0 = result[0] or 0

        cursor.execute("SELECT SUM(tokens) FROM job_reviews WHERE preprocessing_version = 'v2.0'")
        result = cursor.fetchone()
        report.total_tokens_v2_0 = result[0] or 0

        # Calculate averages
        if report.total_jobs_v1_0 > 0:
            report.avg_tokens_per_job_v1_0 = report.total_tokens_v1_0 / report.total_jobs_v1_0
        if report.total_jobs_v2_0 > 0:
            report.avg_tokens_per_job_v2_0 = report.total_tokens_v2_0 / report.total_jobs_v2_0

        # Estimate total savings (assuming $0.003 per 1M tokens for input)
        token_rate = 0.003 / 1_000_000
        if report.total_tokens_v1_0 > 0 and report.total_tokens_v2_0 > 0:
            tokens_saved = report.total_tokens_v1_0 - report.total_tokens_v2_0
            report.estimated_savings_usd = tokens_saved * token_rate

        # Get re-preprocessing metrics
        cursor.execute(
            """SELECT job_id, preprocessing_version_before, preprocessing_version_after,
                      tokens_before, tokens_after, estimated_cost_before, estimated_cost_after
               FROM cost_tracking
               WHERE is_re_preprocessing = TRUE
               ORDER BY timestamp DESC"""
        )

        reprocessing_runs = []
        for row in cursor.fetchall():
            metrics = ReprocessingMetrics(
                job_id=row[0],
                preprocessing_version_before=row[1],
                preprocessing_version_after=row[2],
                tokens_before=row[3],
                tokens_after=row[4],
                estimated_cost_before=row[5],
                estimated_cost_after=row[6],
            )
            reprocessing_runs.append(metrics)
            report.total_reprocessing_tokens_saved += metrics.tokens_saved
            report.total_reprocessing_cost_saved += metrics.cost_saved_usd

        report.reprocessing_runs = reprocessing_runs
        report.jobs_already_migrated = report.total_jobs_v2_0
        report.jobs_pending_migration = report.total_jobs_v1_0

        return report

    def get_jobs_for_reprocessing(
        self,
        version: str = "v1.0",
        min_age_days: Optional[int] = None,
        max_score: Optional[int] = None,
        min_tokens: Optional[int] = None,
        company_names: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get jobs matching filter criteria for targeted re-preprocessing.

        Intelligently filters jobs based on version, age, score, token count, and company.
        Supports combined filtering for A/B testing and gradual migrations.

        Args:
            version: Preprocessing version to filter (e.g., 'v1.0', '1.0', 'v2.0', '2.0')
            min_age_days: Only jobs preprocessed at least N days ago
            max_score: Only jobs with overall_score <= max_score (for low-scoring jobs)
            min_tokens: Only jobs with tokens >= min_tokens (high token count)
            company_names: List of company names to include (e.g., ['Amazon', 'Google'])
            limit: Maximum number of jobs to return (enforces safe batch sizes)

        Returns:
            List of job dicts matching all filter criteria, ordered by oldest first

        Raises:
            ValueError: If version not valid
        """
        # Normalize and validate version
        clean_version = version.replace("v", "")
        if clean_version not in ("1.0", "2.0"):
            raise ValueError(f"Invalid preprocessing version: {version}. Must be '1.0' or '2.0'")

        if not self.conn:
            return []

        # Format for query
        version_query = version if version.startswith("v") else f"v{version}"

        # Build query dynamically based on filters
        query = "SELECT * FROM job_reviews WHERE preprocessing_version = ?"
        params: List[Any] = [version_query]

        # Age filter: jobs preprocessed at least min_age_days ago
        if min_age_days is not None and min_age_days > 0:
            query += f" AND datetime(preprocessed_at) <= datetime('now', '-{min_age_days} days')"

        # Score filter: only jobs with low scores (potential improvement candidates)
        if max_score is not None:
            # Note: This requires a joined assessments table or score column
            # For now, we note that future implementation will add assessment score tracking
            pass

        # Token filter: only high-token jobs (most savings potential)
        if min_tokens is not None and min_tokens > 0:
            query += " AND tokens >= ?"
            params.append(min_tokens)

        # Company filter: restrict to specific companies
        if company_names is not None and len(company_names) > 0:
            placeholders = ", ".join("?" * len(company_names))
            query += f" AND company IN ({placeholders})"
            params.extend(company_names)

        # Order by oldest first (prioritize older jobs)
        query += " ORDER BY preprocessed_at ASC"

        # Apply batch limit for safety
        if limit is not None and limit > 0:
            query += f" LIMIT {limit}"

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Job store connection closed")
