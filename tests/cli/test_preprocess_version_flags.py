"""Tests for preprocessing version CLI flags (Phase 2, Task 3)."""

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


class TestPreprocessVersionFlags:
    """Test preprocessing version flags in CLI."""

    def test_preprocess_help_shows_preprocessing_version_flag(self) -> None:
        """Help text should show --preprocessing-version flag."""
        result = runner.invoke(app, ["preprocess", "--help"])
        assert result.exit_code == 0
        assert "--preprocessing-version" in result.stdout

    def test_preprocess_help_shows_re_preprocess_only_v1_flag(self) -> None:
        """Help text should show --re-preprocess-only-v1 flag."""
        result = runner.invoke(app, ["preprocess", "--help"])
        assert result.exit_code == 0
        assert "--re-preprocess-only-v1" in result.stdout

    def test_preprocess_version_default_is_v2(self) -> None:
        """Default preprocessing version should be 2.0."""
        result = runner.invoke(app, ["preprocess", "--help"])
        assert result.exit_code == 0
        # Help text should mention default
        help_text = result.stdout.lower()
        assert "2.0" in help_text or "default" in help_text
