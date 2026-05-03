"""Tests for export/import CLI commands."""

import pytest
import json
import sys
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch
from io import StringIO

from src.models.workflow_run import WorkflowRun
from src.models.workflow_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.cli.workflow_cli import build_parser, run_cli


def _make_run(
    run_id: str = "run-1",
    workflow_name: str = "CI",
    branch: str = "main",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    created_at: datetime = None,
    updated_at: datetime = None,
    run_number: int = 1,
    commit_sha: str = "abc123",
    duration_seconds: float = 10.0,
) -> WorkflowRun:
    """Helper to create a WorkflowRun."""
    if created_at is None:
        created_at = datetime(2026, 5, 3, 10, 0, 0)
    return WorkflowRun(
        id=run_id,
        workflow_name=workflow_name,
        branch=branch,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        updated_at=updated_at,
        run_number=run_number,
        commit_sha=commit_sha,
        duration_seconds=duration_seconds,
    )


def _make_attempt(
    attempt_id: str = "attempt-1",
    run_id: str = "run-1",
    attempt_number: int = 1,
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    started_at: datetime = None,
    completed_at: datetime = None,
    duration_seconds: float = 5.0,
    logs_url: str = "https://logs.example.com",
) -> WorkflowRunAttempt:
    """Helper to create a WorkflowRunAttempt."""
    if started_at is None:
        started_at = datetime(2026, 5, 3, 10, 0, 0)
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=duration_seconds,
        logs_url=logs_url,
    )


@pytest.fixture
def parser():
    """Create the argument parser."""
    return build_parser()


@pytest.fixture
def mock_run_service():
    """Mock WorkflowRunService."""
    service = MagicMock()
    service.list_runs.return_value = []
    return service


@pytest.fixture
def mock_attempt_service():
    """Mock WorkflowAttemptService."""
    service = MagicMock()
    service.list_attempts.return_value = []
    return service


@pytest.fixture
def mock_portability_service():
    """Mock WorkflowDataPortabilityService."""
    service = MagicMock()
    return service


class TestParserExportCommand:
    """Test argument parser for export command."""

    def test_parser_export_runs_required_output(self, parser):
        """Export runs command requires --output flag."""
        with pytest.raises(SystemExit):
            parser.parse_args(["export", "runs"])

    def test_parser_export_runs_with_output(self, parser):
        """Export runs command accepts --output flag."""
        args = parser.parse_args(["export", "runs", "--output", "/path/to/file.json"])
        assert args.command == "export"
        assert args.export_command == "runs"
        assert args.output == "/path/to/file.json"

    def test_parser_export_runs_with_output_short_flag(self, parser):
        """Export runs command accepts -o short flag."""
        args = parser.parse_args(["export", "runs", "-o", "/path/to/file.json"])
        assert args.command == "export"
        assert args.export_command == "runs"
        assert args.output == "/path/to/file.json"

    def test_parser_export_attempts_required_output(self, parser):
        """Export attempts command requires --output flag."""
        with pytest.raises(SystemExit):
            parser.parse_args(["export", "attempts"])

    def test_parser_export_attempts_with_output(self, parser):
        """Export attempts command accepts --output flag."""
        args = parser.parse_args(["export", "attempts", "--output", "/path/to/file.json"])
        assert args.command == "export"
        assert args.export_command == "attempts"
        assert args.output == "/path/to/file.json"


class TestParserImportCommand:
    """Test argument parser for import command."""

    def test_parser_import_runs_required_input(self, parser):
        """Import runs command requires --input flag."""
        with pytest.raises(SystemExit):
            parser.parse_args(["import", "runs"])

    def test_parser_import_runs_with_input(self, parser):
        """Import runs command accepts --input flag."""
        args = parser.parse_args(["import", "runs", "--input", "/path/to/file.json"])
        assert args.command == "import"
        assert args.import_command == "runs"
        assert args.input == "/path/to/file.json"
        assert args.skip_duplicates is False

    def test_parser_import_runs_with_input_short_flag(self, parser):
        """Import runs command accepts -i short flag."""
        args = parser.parse_args(["import", "runs", "-i", "/path/to/file.json"])
        assert args.command == "import"
        assert args.import_command == "runs"
        assert args.input == "/path/to/file.json"

    def test_parser_import_runs_with_skip_duplicates(self, parser):
        """Import runs command accepts --skip-duplicates flag."""
        args = parser.parse_args(["import", "runs", "--input", "/path/to/file.json", "--skip-duplicates"])
        assert args.command == "import"
        assert args.import_command == "runs"
        assert args.input == "/path/to/file.json"
        assert args.skip_duplicates is True

    def test_parser_import_attempts_required_input(self, parser):
        """Import attempts command requires --input flag."""
        with pytest.raises(SystemExit):
            parser.parse_args(["import", "attempts"])

    def test_parser_import_attempts_with_input(self, parser):
        """Import attempts command accepts --input flag."""
        args = parser.parse_args(["import", "attempts", "--input", "/path/to/file.json"])
        assert args.command == "import"
        assert args.import_command == "attempts"
        assert args.input == "/path/to/file.json"
        assert args.skip_duplicates is False

    def test_parser_import_attempts_with_skip_duplicates(self, parser):
        """Import attempts command accepts --skip-duplicates flag."""
        args = parser.parse_args(["import", "attempts", "--input", "/path/to/file.json", "--skip-duplicates"])
        assert args.command == "import"
        assert args.import_command == "attempts"
        assert args.input == "/path/to/file.json"
        assert args.skip_duplicates is True


class TestRunCliExportRuns:
    """Test run_cli for export runs command."""

    def test_export_runs_success(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Export runs command prints success message."""
        mock_portability_service.export_runs.return_value = 2

        output_file = tmp_path / "export.json"
        run_cli(
            mock_run_service,
            mock_attempt_service,
            None,
            mock_portability_service,
            args=["export", "runs", "-o", str(output_file)],
        )

        captured = capsys.readouterr()
        assert "Exported 2 run(s)" in captured.out
        assert str(output_file) in captured.out
        mock_portability_service.export_runs.assert_called_once_with(str(output_file))

    def test_export_runs_zero_runs(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Export runs with zero runs prints success message."""
        mock_portability_service.export_runs.return_value = 0

        output_file = tmp_path / "export.json"
        run_cli(
            mock_run_service,
            mock_attempt_service,
            None,
            mock_portability_service,
            args=["export", "runs", "-o", str(output_file)],
        )

        captured = capsys.readouterr()
        assert "Exported 0 run(s)" in captured.out

    def test_export_runs_no_service_raises_error(self, mock_run_service, mock_attempt_service, capsys, tmp_path):
        """Export runs without portability service prints error."""
        output_file = tmp_path / "export.json"

        with pytest.raises(SystemExit):
            run_cli(
                mock_run_service,
                mock_attempt_service,
                None,
                None,  # No portability service
                args=["export", "runs", "-o", str(output_file)],
            )

        captured = capsys.readouterr()
        assert "not initialized" in captured.err

    def test_export_runs_service_error(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Export runs handles service errors gracefully."""
        mock_portability_service.export_runs.side_effect = IOError("Permission denied")

        output_file = tmp_path / "export.json"

        with pytest.raises(SystemExit):
            run_cli(
                mock_run_service,
                mock_attempt_service,
                None,
                mock_portability_service,
                args=["export", "runs", "-o", str(output_file)],
            )

        captured = capsys.readouterr()
        assert "Error exporting data" in captured.err


class TestRunCliExportAttempts:
    """Test run_cli for export attempts command."""

    def test_export_attempts_success(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Export attempts command prints success message."""
        mock_portability_service.export_attempts.return_value = 3

        output_file = tmp_path / "export.json"
        run_cli(
            mock_run_service,
            mock_attempt_service,
            None,
            mock_portability_service,
            args=["export", "attempts", "-o", str(output_file)],
        )

        captured = capsys.readouterr()
        assert "Exported 3 attempt(s)" in captured.out
        assert str(output_file) in captured.out
        mock_portability_service.export_attempts.assert_called_once_with(str(output_file))

    def test_export_attempts_zero_attempts(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Export attempts with zero attempts prints success message."""
        mock_portability_service.export_attempts.return_value = 0

        output_file = tmp_path / "export.json"
        run_cli(
            mock_run_service,
            mock_attempt_service,
            None,
            mock_portability_service,
            args=["export", "attempts", "-o", str(output_file)],
        )

        captured = capsys.readouterr()
        assert "Exported 0 attempt(s)" in captured.out

    def test_export_attempts_service_error(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Export attempts handles service errors gracefully."""
        mock_portability_service.export_attempts.side_effect = ValueError("Invalid path")

        output_file = tmp_path / "export.json"

        with pytest.raises(SystemExit):
            run_cli(
                mock_run_service,
                mock_attempt_service,
                None,
                mock_portability_service,
                args=["export", "attempts", "-o", str(output_file)],
            )

        captured = capsys.readouterr()
        assert "Error exporting data" in captured.err


class TestRunCliImportRuns:
    """Test run_cli for import runs command."""

    def test_import_runs_success(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Import runs command prints success message."""
        mock_portability_service.import_runs.return_value = {
            "imported": [_make_run("run-1"), _make_run("run-2")],
            "skipped": [],
            "count": 2,
            "successful": 2,
            "failed": 0,
        }

        input_file = tmp_path / "import.json"
        input_file.write_text("[]")

        run_cli(
            mock_run_service,
            mock_attempt_service,
            None,
            mock_portability_service,
            args=["import", "runs", "-i", str(input_file)],
        )

        captured = capsys.readouterr()
        assert "Imported 2 run(s)" in captured.out
        mock_portability_service.import_runs.assert_called_once_with(str(input_file), skip_duplicates=False)

    def test_import_runs_with_skip_duplicates(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Import runs with skip_duplicates flag."""
        mock_portability_service.import_runs.return_value = {
            "imported": [_make_run("run-2")],
            "skipped": [{"id": "run-1"}],
            "count": 2,
            "successful": 1,
            "failed": 0,
        }

        input_file = tmp_path / "import.json"
        input_file.write_text("[]")

        run_cli(
            mock_run_service,
            mock_attempt_service,
            None,
            mock_portability_service,
            args=["import", "runs", "-i", str(input_file), "--skip-duplicates"],
        )

        captured = capsys.readouterr()
        assert "Imported 1 run(s)" in captured.out
        assert "Skipped 1 duplicate run(s)" in captured.out
        mock_portability_service.import_runs.assert_called_once_with(str(input_file), skip_duplicates=True)

    def test_import_runs_with_failures(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Import runs prints failure counts."""
        mock_portability_service.import_runs.return_value = {
            "imported": [_make_run("run-1")],
            "skipped": [],
            "count": 2,
            "successful": 1,
            "failed": 1,
        }

        input_file = tmp_path / "import.json"
        input_file.write_text("[]")

        run_cli(
            mock_run_service,
            mock_attempt_service,
            None,
            mock_portability_service,
            args=["import", "runs", "-i", str(input_file)],
        )

        captured = capsys.readouterr()
        assert "Imported 1 run(s)" in captured.out
        assert "Failed to import 1 run(s)" in captured.out

    def test_import_runs_no_service_raises_error(self, mock_run_service, mock_attempt_service, capsys, tmp_path):
        """Import runs without portability service prints error."""
        input_file = tmp_path / "import.json"
        input_file.write_text("[]")

        with pytest.raises(SystemExit):
            run_cli(
                mock_run_service,
                mock_attempt_service,
                None,
                None,  # No portability service
                args=["import", "runs", "-i", str(input_file)],
            )

        captured = capsys.readouterr()
        assert "not initialized" in captured.err

    def test_import_runs_service_error(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Import runs handles service errors gracefully."""
        mock_portability_service.import_runs.side_effect = IOError("File not found")

        input_file = tmp_path / "import.json"

        with pytest.raises(SystemExit):
            run_cli(
                mock_run_service,
                mock_attempt_service,
                None,
                mock_portability_service,
                args=["import", "runs", "-i", str(input_file)],
            )

        captured = capsys.readouterr()
        assert "Error importing data" in captured.err


class TestRunCliImportAttempts:
    """Test run_cli for import attempts command."""

    def test_import_attempts_success(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Import attempts command prints success message."""
        mock_portability_service.import_attempts.return_value = {
            "imported": [_make_attempt("attempt-1"), _make_attempt("attempt-2")],
            "skipped": [],
            "count": 2,
            "successful": 2,
            "failed": 0,
        }

        input_file = tmp_path / "import.json"
        input_file.write_text("[]")

        run_cli(
            mock_run_service,
            mock_attempt_service,
            None,
            mock_portability_service,
            args=["import", "attempts", "-i", str(input_file)],
        )

        captured = capsys.readouterr()
        assert "Imported 2 attempt(s)" in captured.out
        mock_portability_service.import_attempts.assert_called_once_with(str(input_file), skip_duplicates=False)

    def test_import_attempts_with_skip_duplicates(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Import attempts with skip_duplicates flag."""
        mock_portability_service.import_attempts.return_value = {
            "imported": [_make_attempt("attempt-2", attempt_number=2)],
            "skipped": [{"id": "attempt-1"}],
            "count": 2,
            "successful": 1,
            "failed": 0,
        }

        input_file = tmp_path / "import.json"
        input_file.write_text("[]")

        run_cli(
            mock_run_service,
            mock_attempt_service,
            None,
            mock_portability_service,
            args=["import", "attempts", "-i", str(input_file), "--skip-duplicates"],
        )

        captured = capsys.readouterr()
        assert "Imported 1 attempt(s)" in captured.out
        assert "Skipped 1 duplicate attempt(s)" in captured.out
        mock_portability_service.import_attempts.assert_called_once_with(str(input_file), skip_duplicates=True)

    def test_import_attempts_with_failures(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Import attempts prints failure counts."""
        mock_portability_service.import_attempts.return_value = {
            "imported": [_make_attempt("attempt-1")],
            "skipped": [],
            "count": 2,
            "successful": 1,
            "failed": 1,
        }

        input_file = tmp_path / "import.json"
        input_file.write_text("[]")

        run_cli(
            mock_run_service,
            mock_attempt_service,
            None,
            mock_portability_service,
            args=["import", "attempts", "-i", str(input_file)],
        )

        captured = capsys.readouterr()
        assert "Imported 1 attempt(s)" in captured.out
        assert "Failed to import 1 attempt(s)" in captured.out

    def test_import_attempts_service_error(self, mock_run_service, mock_attempt_service, mock_portability_service, capsys, tmp_path):
        """Import attempts handles service errors gracefully."""
        mock_portability_service.import_attempts.side_effect = ValueError("Invalid JSON")

        input_file = tmp_path / "import.json"

        with pytest.raises(SystemExit):
            run_cli(
                mock_run_service,
                mock_attempt_service,
                None,
                mock_portability_service,
                args=["import", "attempts", "-i", str(input_file)],
            )

        captured = capsys.readouterr()
        assert "Error importing data" in captured.err


class TestCLIIntegration:
    """Integration tests for CLI export/import workflow."""

    def test_help_includes_export_command(self, parser):
        """Help text includes export command."""
        # The parser should have export as a valid command
        args = parser.parse_args(["export", "runs", "-o", "test.json"])
        assert args.command == "export"

    def test_help_includes_import_command(self, parser):
        """Help text includes import command."""
        # The parser should have import as a valid command
        args = parser.parse_args(["import", "runs", "-i", "test.json"])
        assert args.command == "import"
