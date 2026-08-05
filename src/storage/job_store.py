"""Job storage and management for ATS Playground."""

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

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

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Job store connection closed")
