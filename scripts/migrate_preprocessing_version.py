#!/usr/bin/env python3
"""Idempotent migration: add preprocessing_version column to job_reviews table (Phase 2)."""

import logging
import sqlite3
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_preprocessing_version(db_path: str = "data/ats_playground.db") -> None:
    """Add preprocessing_version column and set defaults.

    Args:
        db_path: Path to SQLite database

    Raises:
        sqlite3.Error: If migration fails
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists (idempotent)
        cursor.execute("PRAGMA table_info(job_reviews)")
        columns = [row[1] for row in cursor.fetchall()]

        if "preprocessing_version" in columns:
            logger.info("✓ preprocessing_version column already exists, skipping")
            return

        # Add column with default
        logger.info("Adding preprocessing_version column...")
        cursor.execute("ALTER TABLE job_reviews ADD COLUMN preprocessing_version TEXT DEFAULT 'v2.0'")

        # Update existing jobs to v1.0 (legacy, no boilerplate removal)
        logger.info("Marking existing jobs as v1.0 (legacy)...")
        cursor.execute("UPDATE job_reviews SET preprocessing_version = 'v1.0' WHERE preprocessing_version IS NULL")

        # Verify
        cursor.execute("SELECT preprocessing_version, COUNT(*) FROM job_reviews GROUP BY preprocessing_version")
        counts = dict(cursor.fetchall())

        logger.info("\n✓ Migration complete:")
        logger.info(f"  v1.0 (legacy): {counts.get('v1.0', 0)} jobs")
        logger.info(f"  v2.0 (new): {counts.get('v2.0', 0)} jobs")

        conn.commit()

    except sqlite3.Error as e:
        logger.error(f"✗ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/ats_playground.db"
    migrate_preprocessing_version(db_path)
