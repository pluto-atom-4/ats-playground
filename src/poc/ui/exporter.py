"""Export selected jobs to JSON file."""

import json
from pathlib import Path

from src.poc.ui.loader import Job


def ensure_work_dir(path: Path = Path("data/work/selected.json")) -> None:
    """Ensure the work directory exists. Create if needed.

    Args:
        path: Full path to output file (includes filename).
    """
    path.parent.mkdir(parents=True, exist_ok=True)


def export_jobs(
    jobs: list[Job],
    output_path: Path = Path("data/work/selected.json"),
) -> Path:
    """Export jobs to JSON file.

    Creates parent directory if needed. Always overwrites existing file.

    Args:
        jobs: List of Job dicts to export.
        output_path: Destination file path.

    Returns:
        The output_path (for chaining or verification).

    Raises:
        OSError: If directory creation or file write fails.
    """
    ensure_work_dir(output_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    return output_path
