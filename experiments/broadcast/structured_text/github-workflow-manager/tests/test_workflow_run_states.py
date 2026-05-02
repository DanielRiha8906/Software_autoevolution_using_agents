import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_run(
    run_id: str = "run-1",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = None,
) -> WorkflowRun:
    """Helper to create a WorkflowRun with specific status and conclusion."""
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
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

    def test_completed_is_terminal(self):
        """A COMPLETED run is in a terminal state."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True

    def test_in_progress_not_terminal(self):
        """An IN_PROGRESS run is not terminal."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS)
        assert run.is_terminal() is False

    def test_queued_not_terminal(self):
        """A QUEUED run is not terminal."""
        run = _make_run(status=WorkflowStatus.QUEUED)
        assert run.is_terminal() is False

    def test_waiting_not_terminal(self):
        """A WAITING run is not terminal."""
        run = _make_run(status=WorkflowStatus.WAITING)
        assert run.is_terminal() is False

    def test_requested_not_terminal(self):
        """A REQUESTED run is not terminal."""
        run = _make_run(status=WorkflowStatus.REQUESTED)
        assert run.is_terminal() is False

    def test_pending_not_terminal(self):
        """A PENDING run is not terminal."""
        run = _make_run(status=WorkflowStatus.PENDING)
        assert run.is_terminal() is False


class TestIsRunning:
    """Tests for is_running() method."""

    def test_in_progress_is_running(self):
        """An IN_PROGRESS run is running."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS)
        assert run.is_running() is True

    def test_queued_is_running(self):
        """A QUEUED run is running."""
        run = _make_run(status=WorkflowStatus.QUEUED)
        assert run.is_running() is True

    def test_waiting_is_running(self):
        """A WAITING run is running."""
        run = _make_run(status=WorkflowStatus.WAITING)
        assert run.is_running() is True

    def test_requested_is_running(self):
        """A REQUESTED run is running."""
        run = _make_run(status=WorkflowStatus.REQUESTED)
        assert run.is_running() is True

    def test_pending_is_running(self):
        """A PENDING run is running."""
        run = _make_run(status=WorkflowStatus.PENDING)
        assert run.is_running() is True

    def test_completed_not_running(self):
        """A COMPLETED run is not running."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_running() is False


class TestIsSuccessful:
    """Tests for is_successful() method."""

    def test_completed_with_success_is_successful(self):
        """COMPLETED with SUCCESS conclusion is successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    def test_completed_with_failure_not_successful(self):
        """COMPLETED with FAILURE conclusion is not successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_successful() is False

    def test_completed_with_timed_out_not_successful(self):
        """COMPLETED with TIMED_OUT conclusion is not successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.TIMED_OUT)
        assert run.is_successful() is False

    def test_completed_with_action_required_not_successful(self):
        """COMPLETED with ACTION_REQUIRED conclusion is not successful."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.ACTION_REQUIRED
        )
        assert run.is_successful() is False

    def test_completed_with_cancelled_not_successful(self):
        """COMPLETED with CANCELLED conclusion is not successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False

    def test_completed_with_skipped_not_successful(self):
        """COMPLETED with SKIPPED conclusion is not successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SKIPPED)
        assert run.is_successful() is False

    def test_completed_with_neutral_not_successful(self):
        """COMPLETED with NEUTRAL conclusion is not successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.NEUTRAL)
        assert run.is_successful() is False

    def test_completed_with_stale_not_successful(self):
        """COMPLETED with STALE conclusion is not successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.STALE)
        assert run.is_successful() is False

    def test_in_progress_not_successful(self):
        """An IN_PROGRESS run is not successful."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS)
        assert run.is_successful() is False

    def test_queued_not_successful(self):
        """A QUEUED run is not successful."""
        run = _make_run(status=WorkflowStatus.QUEUED)
        assert run.is_successful() is False


class TestIsFailed:
    """Tests for is_failed() method."""

    def test_completed_with_failure_is_failed(self):
        """COMPLETED with FAILURE conclusion is failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    def test_completed_with_timed_out_is_failed(self):
        """COMPLETED with TIMED_OUT conclusion is failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.TIMED_OUT)
        assert run.is_failed() is True

    def test_completed_with_action_required_is_failed(self):
        """COMPLETED with ACTION_REQUIRED conclusion is failed."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.ACTION_REQUIRED
        )
        assert run.is_failed() is True

    def test_completed_with_success_not_failed(self):
        """COMPLETED with SUCCESS conclusion is not failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_failed() is False

    def test_completed_with_cancelled_not_failed(self):
        """COMPLETED with CANCELLED conclusion is not failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_failed() is False

    def test_completed_with_skipped_not_failed(self):
        """COMPLETED with SKIPPED conclusion is not failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SKIPPED)
        assert run.is_failed() is False

    def test_completed_with_neutral_not_failed(self):
        """COMPLETED with NEUTRAL conclusion is not failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.NEUTRAL)
        assert run.is_failed() is False

    def test_completed_with_stale_not_failed(self):
        """COMPLETED with STALE conclusion is not failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.STALE)
        assert run.is_failed() is False

    def test_in_progress_not_failed(self):
        """An IN_PROGRESS run is not failed."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS)
        assert run.is_failed() is False

    def test_queued_not_failed(self):
        """A QUEUED run is not failed."""
        run = _make_run(status=WorkflowStatus.QUEUED)
        assert run.is_failed() is False


class TestIsCancelled:
    """Tests for is_cancelled() method."""

    def test_cancelled_conclusion_is_cancelled(self):
        """A run with CANCELLED conclusion is cancelled."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    def test_success_conclusion_not_cancelled(self):
        """A run with SUCCESS conclusion is not cancelled."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_cancelled() is False

    def test_failure_conclusion_not_cancelled(self):
        """A run with FAILURE conclusion is not cancelled."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_cancelled() is False

    def test_no_conclusion_not_cancelled(self):
        """A run with no conclusion is not cancelled."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS)
        assert run.is_cancelled() is False


class TestStateExclusivity:
    """Tests for mutual exclusivity of state methods."""

    def test_terminal_and_running_mutually_exclusive_completed(self):
        """A COMPLETED run should be terminal and not running."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True
        assert run.is_running() is False

    def test_terminal_and_running_mutually_exclusive_in_progress(self):
        """An IN_PROGRESS run should be running and not terminal."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS)
        assert run.is_running() is True
        assert run.is_terminal() is False

    def test_terminal_and_running_mutually_exclusive_queued(self):
        """A QUEUED run should be running and not terminal."""
        run = _make_run(status=WorkflowStatus.QUEUED)
        assert run.is_running() is True
        assert run.is_terminal() is False

    def test_successful_and_failed_mutually_exclusive_success(self):
        """A successful run should not be failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True
        assert run.is_failed() is False

    def test_successful_and_failed_mutually_exclusive_failure(self):
        """A failed run should not be successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_failed() is True
        assert run.is_successful() is False

    def test_successful_and_failed_mutually_exclusive_timed_out(self):
        """A timed out run should not be successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.TIMED_OUT)
        assert run.is_failed() is True
        assert run.is_successful() is False

    def test_successful_and_failed_mutually_exclusive_action_required(self):
        """A run with action required should not be successful."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.ACTION_REQUIRED
        )
        assert run.is_failed() is True
        assert run.is_successful() is False
