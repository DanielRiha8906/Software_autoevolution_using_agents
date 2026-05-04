"""
Tests for interactive menu 'Check run state' option.

Covers:
- Menu includes 'Check run state' option
- _check_run_state() function prompts for run ID
- _check_run_state() displays all state flags for existing run
- _check_run_state() handles non-existent run IDs
- State display formatting
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from io import StringIO

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.cli.interactive_menu import _check_run_state, MENU


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
# MENU TESTS
# ============================================================================

class TestMenuStructure:
    """Test that interactive menu includes state checking option."""

    def test_menu_includes_check_run_state(self):
        """MENU list includes 'Check run state' option."""
        menu_labels = [label for label, _ in MENU]
        assert "Check run state" in menu_labels

    def test_menu_check_run_state_is_callable(self):
        """'Check run state' menu entry has callable handler."""
        for label, handler in MENU:
            if label == "Check run state":
                assert callable(handler)
                assert handler == _check_run_state

    def test_menu_check_run_state_order(self):
        """Menu lists options in expected order."""
        menu_labels = [label for label, _ in MENU]
        expected_labels = [
            "Add workflow run",
            "List all runs",
            "Get run detail",
            "Check run state",
            "Filter runs",
            "Advanced filter runs",
            "Get statistics",
            "Fetch from GitHub",
            "Export runs to JSON",
            "Import runs from JSON",
            "Add workflow run attempt",
            "List all attempts",
            "Get attempt detail",
            "List attempts for run",
            "Exit"
        ]
        assert menu_labels == expected_labels


# ============================================================================
# _check_run_state() TESTS
# ============================================================================

class TestCheckRunStateFunction:
    """Test _check_run_state() menu function."""

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

    def test_check_run_state_prompts_for_run_id(self, service):
        """_check_run_state() prompts user for run ID."""
        with patch("builtins.input", return_value="run-1"):
            with patch("sys.stdout", new_callable=StringIO):
                _check_run_state(service)
                # Function should have called service.get_run_detail
                service.get_run_detail.assert_called_once_with("run-1")

    def test_check_run_state_displays_all_state_flags(self, service):
        """_check_run_state() displays all five state flags."""
        with patch("builtins.input", return_value="run-1"):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                _check_run_state(service)
                output = mock_stdout.getvalue()
                assert "is_terminal" in output
                assert "is_successful" in output
                assert "is_failed" in output
                assert "is_running" in output
                assert "is_cancelled" in output

    def test_check_run_state_shows_correct_values(self, service):
        """_check_run_state() displays correct boolean values."""
        with patch("builtins.input", return_value="run-1"):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                _check_run_state(service)
                output = mock_stdout.getvalue()
                # For a successful run
                assert "is_terminal      : True" in output
                assert "is_successful    : True" in output
                assert "is_failed        : False" in output
                assert "is_running       : False" in output
                assert "is_cancelled     : False" in output

    def test_check_run_state_includes_run_id_in_header(self, service):
        """_check_run_state() includes run ID in output."""
        with patch("builtins.input", return_value="run-1"):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                _check_run_state(service)
                output = mock_stdout.getvalue()
                assert "Run State: run-1" in output or "run-1" in output


# ============================================================================
# _check_run_state() - NON-EXISTENT RUN ID
# ============================================================================

class TestCheckRunStateNotFound:
    """Test _check_run_state() when run ID not found."""

    def test_check_run_state_not_found_prints_error(self):
        """_check_run_state() shows error message for non-existent run."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = None

        with patch("builtins.input", return_value="nonexistent-id"):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                _check_run_state(service)
                output = mock_stdout.getvalue()
                assert "No run found" in output

    def test_check_run_state_not_found_does_not_crash(self):
        """_check_run_state() handles non-existent run ID gracefully."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = None

        with patch("builtins.input", return_value="nonexistent-id"):
            with patch("sys.stdout", new_callable=StringIO):
                # Should not raise exception
                _check_run_state(service)

    def test_check_run_state_not_found_calls_service(self):
        """_check_run_state() calls service.get_run_detail() even if not found."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = None

        with patch("builtins.input", return_value="missing-id"):
            with patch("sys.stdout", new_callable=StringIO):
                _check_run_state(service)
                service.get_run_detail.assert_called_once_with("missing-id")


# ============================================================================
# _check_run_state() - VARIOUS RUN STATES
# ============================================================================

class TestCheckRunStateVariousStates:
    """Test _check_run_state() with different run states."""

    def test_check_run_state_failed_run(self):
        """_check_run_state() shows correct values for failed run."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-2",
            WorkflowStatus.COMPLETED,
            WorkflowConclusion.FAILURE
        )

        with patch("builtins.input", return_value="run-2"):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                _check_run_state(service)
                output = mock_stdout.getvalue()
                assert "is_terminal      : True" in output
                assert "is_successful    : False" in output
                assert "is_failed        : True" in output

    def test_check_run_state_cancelled_run(self):
        """_check_run_state() shows correct values for cancelled run."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-3",
            WorkflowStatus.COMPLETED,
            WorkflowConclusion.CANCELLED
        )

        with patch("builtins.input", return_value="run-3"):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                _check_run_state(service)
                output = mock_stdout.getvalue()
                assert "is_terminal      : True" in output
                assert "is_cancelled     : True" in output
                assert "is_successful    : False" in output

    def test_check_run_state_running_run(self):
        """_check_run_state() shows correct values for running run."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-4",
            WorkflowStatus.IN_PROGRESS,
            None
        )

        with patch("builtins.input", return_value="run-4"):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                _check_run_state(service)
                output = mock_stdout.getvalue()
                assert "is_terminal      : False" in output
                assert "is_running       : True" in output

    def test_check_run_state_pending_run(self):
        """_check_run_state() shows correct values for pending run."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-5",
            WorkflowStatus.PENDING,
            None
        )

        with patch("builtins.input", return_value="run-5"):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                _check_run_state(service)
                output = mock_stdout.getvalue()
                assert "is_running       : True" in output

    def test_check_run_state_requested_run(self):
        """_check_run_state() shows correct values for requested run."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-6",
            WorkflowStatus.REQUESTED,
            None
        )

        with patch("builtins.input", return_value="run-6"):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                _check_run_state(service)
                output = mock_stdout.getvalue()
                assert "is_running       : True" in output
                assert "is_terminal      : False" in output


# ============================================================================
# _check_run_state() - INPUT HANDLING
# ============================================================================

class TestCheckRunStateInputHandling:
    """Test _check_run_state() input/output handling."""

    def test_check_run_state_strips_whitespace_from_input(self):
        """_check_run_state() handles input with extra whitespace."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run("run-1")

        with patch("builtins.input", return_value="  run-1  "):
            with patch("sys.stdout", new_callable=StringIO):
                _check_run_state(service)
                # Service should be called with stripped value
                service.get_run_detail.assert_called_once()

    def test_check_run_state_empty_input_handled(self):
        """_check_run_state() handles empty run ID input."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = None

        with patch("builtins.input", return_value=""):
            with patch("sys.stdout", new_callable=StringIO):
                _check_run_state(service)
                # Should call service.get_run_detail with empty string
                service.get_run_detail.assert_called_once_with("")


# ============================================================================
# _check_run_state() - EDGE CASES
# ============================================================================

class TestCheckRunStateEdgeCases:
    """Test edge cases for _check_run_state()."""

    def test_check_run_state_with_special_characters_in_id(self):
        """_check_run_state() works with special characters in run ID."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run("run-id-with-dashes-123")

        with patch("builtins.input", return_value="run-id-with-dashes-123"):
            with patch("sys.stdout", new_callable=StringIO):
                _check_run_state(service)
                service.get_run_detail.assert_called_once_with("run-id-with-dashes-123")

    def test_check_run_state_run_with_no_conclusion(self):
        """_check_run_state() handles run with no conclusion."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-7",
            WorkflowStatus.COMPLETED,
            None
        )

        with patch("builtins.input", return_value="run-7"):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                _check_run_state(service)
                output = mock_stdout.getvalue()
                # COMPLETED + None = not terminal
                assert "is_terminal      : False" in output

    def test_check_run_state_queued_run(self):
        """_check_run_state() handles QUEUED state."""
        service = MagicMock(spec=WorkflowRunService)
        service.get_run_detail.return_value = _make_run(
            "run-8",
            WorkflowStatus.QUEUED,
            None
        )

        with patch("builtins.input", return_value="run-8"):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                _check_run_state(service)
                output = mock_stdout.getvalue()
                assert "is_terminal      : False" in output
                assert "is_running       : False" in output
