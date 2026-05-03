"""
Tests for CLI 'check' subcommand integration.

Covers:
- CLI parser recognizes 'check' subcommand with all flags
- check command without flags shows all state flags
- check command with specific flags shows only requested states
- check command handles non-existent run IDs
- check command exits with proper status codes
"""

import pytest
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from io import StringIO

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.cli.workflow_cli import build_parser, run_cli


# ============================================================================
# TEST HELPERS
# ============================================================================

def _make_run(
    run_id: str = "run-1",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
) -> WorkflowRun:
    """Create a test WorkflowRun."""
    return WorkflowRun(
        id=run_id,
        workflow_name="Test",
        branch="main",
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha=None,
        duration_seconds=0.0,
    )


# ============================================================================
# PARSER TESTS
# ============================================================================

class TestCheckCommandParser:
    """Test that build_parser() recognizes check subcommand."""

    def test_parser_has_check_subcommand(self):
        """build_parser() includes 'check' subcommand."""
        parser = build_parser()
        # Try parsing a check command
        args = parser.parse_args(["check", "run-id"])
        assert args.command == "check"
        assert args.run_id == "run-id"

    def test_parser_check_has_is_terminal_flag(self):
        """check subcommand has --is-terminal flag."""
        parser = build_parser()
        args = parser.parse_args(["check", "run-id", "--is-terminal"])
        assert args.command == "check"
        assert args.is_terminal is True

    def test_parser_check_has_is_successful_flag(self):
        """check subcommand has --is-successful flag."""
        parser = build_parser()
        args = parser.parse_args(["check", "run-id", "--is-successful"])
        assert args.command == "check"
        assert args.is_successful is True

    def test_parser_check_has_is_failed_flag(self):
        """check subcommand has --is-failed flag."""
        parser = build_parser()
        args = parser.parse_args(["check", "run-id", "--is-failed"])
        assert args.command == "check"
        assert args.is_failed is True

    def test_parser_check_has_is_running_flag(self):
        """check subcommand has --is-running flag."""
        parser = build_parser()
        args = parser.parse_args(["check", "run-id", "--is-running"])
        assert args.command == "check"
        assert args.is_running is True

    def test_parser_check_has_is_cancelled_flag(self):
        """check subcommand has --is-cancelled flag."""
        parser = build_parser()
        args = parser.parse_args(["check", "run-id", "--is-cancelled"])
        assert args.command == "check"
        assert args.is_cancelled is True

    def test_parser_check_multiple_flags(self):
        """check subcommand accepts multiple flags."""
        parser = build_parser()
        args = parser.parse_args(["check", "run-id", "--is-terminal", "--is-successful"])
        assert args.command == "check"
        assert args.is_terminal is True
        assert args.is_successful is True


# ============================================================================
# CHECK COMMAND - NO FLAGS (SHOW ALL)
# ============================================================================

class TestCheckCommandShowAllStates:
    """Test 'check' command without flags shows all state checks."""

    @pytest.fixture
    def service(self):
        """Mocked service with a successful run."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-1",
            WorkflowStatus.COMPLETED,
            WorkflowConclusion.SUCCESS
        )
        return service

    def test_check_no_flags_shows_all_states(self, service):
        """check <run-id> without flags displays all state flags."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-1"])
            output = mock_stdout.getvalue()
            # Should show all state fields
            assert "is_terminal" in output
            assert "is_successful" in output
            assert "is_failed" in output
            assert "is_running" in output
            assert "is_cancelled" in output

    def test_check_no_flags_shows_correct_values(self, service):
        """check <run-id> shows correct boolean values for successful run."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-1"])
            output = mock_stdout.getvalue()
            # For a successful run
            assert "is_terminal      : True" in output
            assert "is_successful    : True" in output
            assert "is_failed        : False" in output
            assert "is_running       : False" in output
            assert "is_cancelled     : False" in output

    def test_check_no_flags_shows_run_id(self, service):
        """check <run-id> includes the run ID in output."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-1"])
            output = mock_stdout.getvalue()
            assert "run-1" in output


# ============================================================================
# CHECK COMMAND - SPECIFIC FLAGS
# ============================================================================

class TestCheckCommandSpecificFlags:
    """Test 'check' command with specific flags."""

    @pytest.fixture
    def service(self):
        """Mocked service."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-1",
            WorkflowStatus.COMPLETED,
            WorkflowConclusion.SUCCESS
        )
        return service

    def test_check_is_terminal_flag_only(self, service):
        """check --is-terminal shows only is_terminal."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-1", "--is-terminal"])
            output = mock_stdout.getvalue()
            assert "is_terminal" in output
            assert "True" in output

    def test_check_is_successful_flag_only(self, service):
        """check --is-successful shows only is_successful."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-1", "--is-successful"])
            output = mock_stdout.getvalue()
            assert "is_successful" in output
            assert "True" in output

    def test_check_is_failed_flag_only(self, service):
        """check --is-failed shows only is_failed."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-1", "--is-failed"])
            output = mock_stdout.getvalue()
            assert "is_failed" in output
            assert "False" in output

    def test_check_is_running_flag_only(self, service):
        """check --is-running shows only is_running."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-1", "--is-running"])
            output = mock_stdout.getvalue()
            assert "is_running" in output
            assert "False" in output

    def test_check_is_cancelled_flag_only(self, service):
        """check --is-cancelled shows only is_cancelled."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-1", "--is-cancelled"])
            output = mock_stdout.getvalue()
            assert "is_cancelled" in output
            assert "False" in output

    def test_check_multiple_flags(self, service):
        """check with multiple flags shows only requested states."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-1", "--is-terminal", "--is-successful"])
            output = mock_stdout.getvalue()
            assert "is_terminal" in output
            assert "is_successful" in output
            # Should have two lines of output (one per flag)
            lines = [l for l in output.strip().split("\n") if l]
            assert len(lines) >= 2


# ============================================================================
# CHECK COMMAND - DIFFERENT RUN STATES
# ============================================================================

class TestCheckCommandVariousStates:
    """Test 'check' command with runs in different states."""

    def test_check_failed_run(self):
        """check shows correct values for failed run."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-2",
            WorkflowStatus.COMPLETED,
            WorkflowConclusion.FAILURE
        )
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-2"])
            output = mock_stdout.getvalue()
            assert "is_terminal      : True" in output
            assert "is_successful    : False" in output
            assert "is_failed        : True" in output

    def test_check_cancelled_run(self):
        """check shows correct values for cancelled run."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-3",
            WorkflowStatus.COMPLETED,
            WorkflowConclusion.CANCELLED
        )
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-3"])
            output = mock_stdout.getvalue()
            assert "is_terminal      : True" in output
            assert "is_cancelled     : True" in output
            assert "is_successful    : False" in output

    def test_check_running_run(self):
        """check shows correct values for running run."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-4",
            WorkflowStatus.IN_PROGRESS,
            None
        )
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-4"])
            output = mock_stdout.getvalue()
            assert "is_terminal      : False" in output
            assert "is_running       : True" in output


# ============================================================================
# CHECK COMMAND - NON-EXISTENT RUN ID
# ============================================================================

class TestCheckCommandNotFound:
    """Test 'check' command when run ID not found."""

    def test_check_non_existent_run_id_prints_error(self):
        """check with non-existent run ID prints error to stderr."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = None

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                run_cli(service, ["check", "nonexistent-id"])
            assert exc_info.value.code == 1
            output = mock_stderr.getvalue()
            assert "No run found" in output

    def test_check_non_existent_run_id_exits_with_code_1(self):
        """check with non-existent run ID exits with code 1."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = None

        with pytest.raises(SystemExit) as exc_info:
            run_cli(service, ["check", "nonexistent-id"])
        assert exc_info.value.code == 1

    def test_check_non_existent_run_id_calls_get_run_detail(self):
        """check calls service.get_run_detail() with correct run ID."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = None

        with pytest.raises(SystemExit):
            run_cli(service, ["check", "specific-id"])
        service.get_run_detail.assert_called_once_with("specific-id")


# ============================================================================
# CHECK COMMAND - EDGE CASES
# ============================================================================

class TestCheckCommandEdgeCases:
    """Test edge cases for check command."""

    def test_check_run_with_no_conclusion(self):
        """check works for run with None conclusion."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-5",
            WorkflowStatus.COMPLETED,
            None
        )
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-5"])
            output = mock_stdout.getvalue()
            # COMPLETED + None conclusion = not terminal
            assert "is_terminal      : False" in output

    def test_check_queued_run(self):
        """check shows correct state for QUEUED run."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-6",
            WorkflowStatus.QUEUED,
            None
        )
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-6"])
            output = mock_stdout.getvalue()
            assert "is_terminal      : False" in output
            assert "is_running       : False" in output

    def test_check_pending_run(self):
        """check shows correct state for PENDING run."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-7",
            WorkflowStatus.PENDING,
            None
        )
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_cli(service, ["check", "run-7"])
            output = mock_stdout.getvalue()
            assert "is_running       : True" in output
