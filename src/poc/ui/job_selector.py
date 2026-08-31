"""TUI job selector application using Textual."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Input, SelectionList, Static

from src.poc.ui.exporter import export_jobs
from src.poc.ui.loader import Job, load_jobs

DEFAULT_OUTPUT_PATH = Path("data/work/selected.json")


def format_job_row(job: Job) -> str:
    """Format a job for display in SelectionList (title | company | location | status).

    Args:
        job: Job to format.

    Returns:
        Formatted string with pipe-separated fields, column-aligned.
    """
    # Use fixed column widths for alignment
    title = job["title"][:40].ljust(40)
    company = job["company"][:20].ljust(20)
    location = job["location"][:20].ljust(20)
    status = job["status"][:15].ljust(15)

    return f"{title} | {company} | {location} | {status}"


class WarningBanner(Static):
    """Static widget to display loading warnings."""

    DEFAULT_CSS = """
    WarningBanner {
        width: 100%;
        height: auto;
        background: $warning;
        color: $text;
        border: solid $warning;
        content-align: left middle;
        padding: 0 1;
    }
    """

    def __init__(self, warnings: list[str]) -> None:
        """Initialize with warnings."""
        super().__init__()
        self.warnings = warnings

    def render(self) -> str:
        """Render warning messages."""
        if not self.warnings:
            return ""
        msg = f"⚠ {len(self.warnings)} warning(s): {'; '.join(self.warnings[:2])}"
        if len(self.warnings) > 2:
            msg += f" (+{len(self.warnings) - 2} more)"
        return msg


class JobSelectorApp(App):
    """Main TUI application for selecting jobs."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear_selection", "Clear"),
        ("a", "select_all", "Select All"),
        ("e", "export_selected", "Export"),
    ]

    CSS = """
    Screen {
        layout: vertical;
    }

    Header {
        height: 1;
        background: $boost;
        color: $text;
    }

    #job_list {
        height: 1fr;
        border: solid $primary;
    }

    #filter_input {
        height: 3;
        border: solid $accent;
    }

    #status_bar {
        height: 1;
        background: $boost;
        color: $text;
    }

    Footer {
        height: auto;
    }
    """

    def __init__(
        self,
        jobs: list[Job] | None = None,
        warnings: list[str] | None = None,
        output_path: Path = DEFAULT_OUTPUT_PATH,
    ) -> None:
        """Initialize with jobs and output path.

        Args:
            jobs: Optional list of jobs (loaded from disk if not provided).
            warnings: Optional list of warnings from loading.
            output_path: Path where to save selected jobs.
        """
        super().__init__()
        self.output_path = output_path
        self.all_jobs = jobs or []
        self.all_warnings = warnings or []
        self.filter_text = ""
        self.selected_ids: set[str] = set()
        self._job_id_to_index: dict[str, int] = {}

    def compose(self) -> ComposeResult:
        """Compose the UI widgets."""
        yield Header(show_clock=False)

        if self.all_warnings:
            yield WarningBanner(self.all_warnings)

        with Container(id="main_container"):
            yield Input(
                id="filter_input",
                placeholder="Type to filter jobs (title/company/location)...",
            )

            yield SelectionList[str](id="job_list")

            yield Static(id="status_bar", classes="status_bar")

        yield Footer()

    def on_mount(self) -> None:
        """Load jobs and populate selection list."""
        # Load jobs if not provided at init
        if not self.all_jobs:
            result = load_jobs()
            self.all_jobs = result.jobs
            self.all_warnings = result.warnings

        # Initial population
        self._update_job_list()
        self._update_status_bar()

    def _update_job_list(self) -> None:
        """Populate job list based on current filter."""
        job_list = self.query_one("#job_list", SelectionList)
        job_list.clear_options()
        self._job_id_to_index.clear()

        # Filter jobs
        filtered_jobs = self._get_filtered_jobs()

        # Add formatted job options
        for idx, job in enumerate(filtered_jobs):
            row_text = format_job_row(job)
            job_id = job["id"]
            # Store mapping from job ID to current index
            self._job_id_to_index[job_id] = idx
            # Add option with job ID as value
            job_list.add_option((row_text, job_id))

    def _get_filtered_jobs(self) -> list[Job]:
        """Get jobs matching current filter."""
        if not self.filter_text:
            return self.all_jobs

        filter_lower = self.filter_text.lower()
        return [
            job
            for job in self.all_jobs
            if any(filter_lower in field.lower() for field in [job["title"], job["company"], job["location"]])
        ]

    def _update_status_bar(self) -> None:
        """Update status bar with selection count."""
        filtered = self._get_filtered_jobs()
        status_bar = self.query_one("#status_bar", Static)
        selected_count = len([j for j in filtered if j["id"] in self.selected_ids])
        status_bar.update(
            f"Jobs: {len(filtered)} of {len(self.all_jobs)} | Selected: {selected_count} | "
            f"[a] Select All | [c] Clear | [e] Export | [q] Quit"
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input changes."""
        self.filter_text = event.value
        self._update_job_list()
        self._update_status_bar()

    def action_select_all(self) -> None:
        """Select all visible jobs."""
        filtered = self._get_filtered_jobs()
        self.selected_ids.update(job["id"] for job in filtered)

        self._update_status_bar()

    def action_clear_selection(self) -> None:
        """Clear all selections."""
        self.selected_ids.clear()

        self._update_status_bar()

    def action_export_selected(self) -> None:
        """Export selected jobs to JSON file."""
        if not self.selected_ids:
            self.notify("No jobs selected to export.", title="Export", timeout=3)
            return

        # Filter to selected jobs
        selected_jobs = [j for j in self.all_jobs if j["id"] in self.selected_ids]

        # Export
        export_jobs(selected_jobs, self.output_path)
        self.notify(
            f"Exported {len(selected_jobs)} jobs to {self.output_path}",
            title="Export Complete",
            timeout=5,
        )


def main() -> None:
    """Run the job selector TUI."""
    app = JobSelectorApp()
    app.run()


if __name__ == "__main__":
    main()
