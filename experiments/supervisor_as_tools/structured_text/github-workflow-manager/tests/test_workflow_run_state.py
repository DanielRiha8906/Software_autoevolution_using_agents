import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_run(status, conclusion=None, run_id="test-run"):
    """Helper function to create a WorkflowRun with minimal boilerplate."""
    return WorkflowRun(
        id=run_id,
        workflow_name="Test Workflow",
        branch="main",
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
    )


class TestIsTerminal:
    """Tests for is_terminal() method."""

    def test_is_terminal_completed_status(self):
        """A run with COMPLETED status should be terminal."""
        run = _make_run(WorkflowStatus.COMPLETED)
        assert run.is_terminal() is True

    def test_is_terminal_completed_with_success(self):
        """A run with COMPLETED status and SUCCESS conclusion should be terminal."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True

    def test_is_terminal_completed_with_failure(self):
        """A run with COMPLETED status and FAILURE conclusion should be terminal."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_terminal() is True

    def test_is_not_terminal_queued(self):
        """A run with QUEUED status should not be terminal."""
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_terminal() is False

    def test_is_not_terminal_in_progress(self):
        """A run with IN_PROGRESS status should not be terminal."""
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_terminal() is False

    def test_is_not_terminal_waiting(self):
        """A run with WAITING status should not be terminal."""
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_terminal() is False

    def test_is_not_terminal_requested(self):
        """A run with REQUESTED status should not be terminal."""
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_terminal() is False

    def test_is_not_terminal_pending(self):
        """A run with PENDING status should not be terminal."""
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_terminal() is False


class TestIsRunning:
    """Tests for is_running() method."""

    def test_is_running_queued(self):
        """A run with QUEUED status should be running."""
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_running() is True

    def test_is_running_in_progress(self):
        """A run with IN_PROGRESS status should be running."""
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_running() is True

    def test_is_running_waiting(self):
        """A run with WAITING status should be running."""
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_running() is True

    def test_is_running_requested(self):
        """A run with REQUESTED status should be running."""
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_running() is True

    def test_is_running_pending(self):
        """A run with PENDING status should be running."""
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_running() is True

    def test_is_not_running_completed(self):
        """A run with COMPLETED status should not be running."""
        run = _make_run(WorkflowStatus.COMPLETED)
        assert run.is_running() is False

    def test_is_not_running_completed_with_success(self):
        """A run with COMPLETED status and SUCCESS should not be running."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_running() is False

    def test_is_not_running_completed_with_failure(self):
        """A run with COMPLETED status and FAILURE should not be running."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_running() is False


class TestIsSuccessful:
    """Tests for is_successful() method."""

    def test_is_successful_completed_with_success(self):
        """A run with COMPLETED status and SUCCESS conclusion should be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    def test_is_not_successful_completed_with_failure(self):
        """A run with COMPLETED status and FAILURE should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_successful() is False

    def test_is_not_successful_completed_with_cancelled(self):
        """A run with COMPLETED status and CANCELLED should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False

    def test_is_not_successful_completed_with_skipped(self):
        """A run with COMPLETED status and SKIPPED should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_successful() is False

    def test_is_not_successful_completed_with_timed_out(self):
        """A run with COMPLETED status and TIMED_OUT should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_successful() is False

    def test_is_not_successful_completed_with_action_required(self):
        """A run with COMPLETED status and ACTION_REQUIRED should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_successful() is False

    def test_is_not_successful_completed_with_neutral(self):
        """A run with COMPLETED status and NEUTRAL should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_successful() is False

    def test_is_not_successful_completed_with_stale(self):
        """A run with COMPLETED status and STALE should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_successful() is False

    def test_is_not_successful_in_progress_with_success(self):
        """A run with IN_PROGRESS status cannot be successful (not terminal)."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is False

    def test_is_not_successful_queued_with_success(self):
        """A run with QUEUED status cannot be successful (not terminal)."""
        run = _make_run(WorkflowStatus.QUEUED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is False


class TestIsFailed:
    """Tests for is_failed() method."""

    def test_is_failed_completed_with_failure(self):
        """A run with COMPLETED status and FAILURE conclusion should be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    def test_is_not_failed_completed_with_success(self):
        """A run with COMPLETED status and SUCCESS should not be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_failed() is False

    def test_is_not_failed_completed_with_cancelled(self):
        """A run with COMPLETED status and CANCELLED should not be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_failed() is False

    def test_is_not_failed_completed_with_skipped(self):
        """A run with COMPLETED status and SKIPPED should not be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_failed() is False

    def test_is_not_failed_completed_with_timed_out(self):
        """A run with COMPLETED status and TIMED_OUT should not be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_failed() is False

    def test_is_not_failed_completed_with_action_required(self):
        """A run with COMPLETED status and ACTION_REQUIRED should not be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_failed() is False

    def test_is_not_failed_completed_with_neutral(self):
        """A run with COMPLETED status and NEUTRAL should not be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_failed() is False

    def test_is_not_failed_completed_with_stale(self):
        """A run with COMPLETED status and STALE should not be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_failed() is False

    def test_is_not_failed_in_progress_with_failure(self):
        """A run with IN_PROGRESS status cannot be failed (not terminal)."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, WorkflowConclusion.FAILURE)
        assert run.is_failed() is False

    def test_is_not_failed_queued_with_failure(self):
        """A run with QUEUED status cannot be failed (not terminal)."""
        run = _make_run(WorkflowStatus.QUEUED, WorkflowConclusion.FAILURE)
        assert run.is_failed() is False


class TestIsCancelled:
    """Tests for is_cancelled() method."""

    def test_is_cancelled_completed_with_cancelled(self):
        """A run with COMPLETED status and CANCELLED conclusion should be cancelled."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    def test_is_not_cancelled_completed_with_success(self):
        """A run with COMPLETED status and SUCCESS should not be cancelled."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_cancelled() is False

    def test_is_not_cancelled_completed_with_failure(self):
        """A run with COMPLETED status and FAILURE should not be cancelled."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_cancelled() is False

    def test_is_not_cancelled_in_progress(self):
        """A run with IN_PROGRESS status cannot be cancelled (not terminal)."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is False

    def test_is_not_cancelled_queued(self):
        """A run with QUEUED status cannot be cancelled (not terminal)."""
        run = _make_run(WorkflowStatus.QUEUED, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is False


class TestMutualExclusivity:
    """Tests for mutual exclusivity of state predicates."""

    def test_terminal_and_running_mutually_exclusive(self):
        """A run cannot be both terminal and running."""
        terminal_run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        running_run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert terminal_run.is_terminal() != terminal_run.is_running()
        assert running_run.is_terminal() != running_run.is_running()

    def test_successful_and_failed_mutually_exclusive(self):
        """A run cannot be both successful and failed."""
        success_run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        failed_run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert success_run.is_successful() is True
        assert success_run.is_failed() is False
        assert failed_run.is_successful() is False
        assert failed_run.is_failed() is True

    def test_successful_and_cancelled_mutually_exclusive(self):
        """A run cannot be both successful and cancelled."""
        success_run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        cancelled_run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert success_run.is_successful() is True
        assert success_run.is_cancelled() is False
        assert cancelled_run.is_successful() is False
        assert cancelled_run.is_cancelled() is True

    def test_failed_and_cancelled_mutually_exclusive(self):
        """A run cannot be both failed and cancelled."""
        failed_run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        cancelled_run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert failed_run.is_failed() is True
        assert failed_run.is_cancelled() is False
        assert cancelled_run.is_failed() is False
        assert cancelled_run.is_cancelled() is True

    def test_non_terminal_cannot_be_successful_failed_or_cancelled(self):
        """A non-terminal run cannot be successful, failed, or cancelled."""
        in_progress_run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert in_progress_run.is_running() is True
        assert in_progress_run.is_successful() is False
        assert in_progress_run.is_failed() is False
        assert in_progress_run.is_cancelled() is False

    def test_completed_with_no_conclusion_is_only_terminal(self):
        """A completed run with no conclusion should only be terminal."""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_terminal() is True
        assert run.is_running() is False
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_all_conclusions_are_mutually_exclusive(self):
        """Each conclusion type should be mutually exclusive."""
        success_run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        failed_run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        cancelled_run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)

        # Success run
        assert success_run.is_successful() is True
        assert success_run.is_failed() is False
        assert success_run.is_cancelled() is False

        # Failed run
        assert failed_run.is_successful() is False
        assert failed_run.is_failed() is True
        assert failed_run.is_cancelled() is False

        # Cancelled run
        assert cancelled_run.is_successful() is False
        assert cancelled_run.is_failed() is False
        assert cancelled_run.is_cancelled() is True
