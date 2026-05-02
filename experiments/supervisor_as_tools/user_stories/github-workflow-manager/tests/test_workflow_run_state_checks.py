import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_run(
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
) -> WorkflowRun:
    """Helper to create a WorkflowRun with specified status and conclusion."""
    return WorkflowRun(
        id="test-run",
        workflow_name="TestWorkflow",
        branch="main",
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )


class TestIsTerminal:
    """Test is_terminal() method."""

    def test_is_terminal_when_completed(self):
        """is_terminal should return True when status is COMPLETED."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True

    def test_is_terminal_when_queued(self):
        """is_terminal should return False when status is QUEUED."""
        run = _make_run(status=WorkflowStatus.QUEUED, conclusion=None)
        assert run.is_terminal() is False

    def test_is_terminal_when_in_progress(self):
        """is_terminal should return False when status is IN_PROGRESS."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_terminal() is False

    def test_is_terminal_when_waiting(self):
        """is_terminal should return False when status is WAITING."""
        run = _make_run(status=WorkflowStatus.WAITING, conclusion=None)
        assert run.is_terminal() is False

    def test_is_terminal_when_requested(self):
        """is_terminal should return False when status is REQUESTED."""
        run = _make_run(status=WorkflowStatus.REQUESTED, conclusion=None)
        assert run.is_terminal() is False

    def test_is_terminal_when_pending(self):
        """is_terminal should return False when status is PENDING."""
        run = _make_run(status=WorkflowStatus.PENDING, conclusion=None)
        assert run.is_terminal() is False


class TestIsRunning:
    """Test is_running() method."""

    def test_is_running_when_in_progress(self):
        """is_running should return True when status is IN_PROGRESS."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_running() is True

    def test_is_running_when_completed(self):
        """is_running should return False when status is COMPLETED."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_running() is False

    def test_is_running_when_queued(self):
        """is_running should return False when status is QUEUED."""
        run = _make_run(status=WorkflowStatus.QUEUED, conclusion=None)
        assert run.is_running() is False

    def test_is_running_when_waiting(self):
        """is_running should return False when status is WAITING."""
        run = _make_run(status=WorkflowStatus.WAITING, conclusion=None)
        assert run.is_running() is False

    def test_is_running_when_requested(self):
        """is_running should return False when status is REQUESTED."""
        run = _make_run(status=WorkflowStatus.REQUESTED, conclusion=None)
        assert run.is_running() is False

    def test_is_running_when_pending(self):
        """is_running should return False when status is PENDING."""
        run = _make_run(status=WorkflowStatus.PENDING, conclusion=None)
        assert run.is_running() is False


class TestIsSuccessful:
    """Test is_successful() method."""

    def test_is_successful_when_success(self):
        """is_successful should return True when conclusion is SUCCESS."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    def test_is_successful_when_failure(self):
        """is_successful should return False when conclusion is FAILURE."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_successful() is False

    def test_is_successful_when_cancelled(self):
        """is_successful should return False when conclusion is CANCELLED."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False

    def test_is_successful_when_skipped(self):
        """is_successful should return False when conclusion is SKIPPED."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SKIPPED)
        assert run.is_successful() is False

    def test_is_successful_when_timed_out(self):
        """is_successful should return False when conclusion is TIMED_OUT."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.TIMED_OUT)
        assert run.is_successful() is False

    def test_is_successful_when_action_required(self):
        """is_successful should return False when conclusion is ACTION_REQUIRED."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_successful() is False

    def test_is_successful_when_neutral(self):
        """is_successful should return False when conclusion is NEUTRAL."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.NEUTRAL)
        assert run.is_successful() is False

    def test_is_successful_when_stale(self):
        """is_successful should return False when conclusion is STALE."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.STALE)
        assert run.is_successful() is False

    def test_is_successful_when_conclusion_is_none(self):
        """is_successful should return False when conclusion is None (not yet concluded)."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_successful() is False


class TestIsFailed:
    """Test is_failed() method."""

    def test_is_failed_when_failure(self):
        """is_failed should return True when conclusion is FAILURE."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    def test_is_failed_when_success(self):
        """is_failed should return False when conclusion is SUCCESS."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_failed() is False

    def test_is_failed_when_cancelled(self):
        """is_failed should return False when conclusion is CANCELLED."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_failed() is False

    def test_is_failed_when_skipped(self):
        """is_failed should return False when conclusion is SKIPPED."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SKIPPED)
        assert run.is_failed() is False

    def test_is_failed_when_timed_out(self):
        """is_failed should return False when conclusion is TIMED_OUT."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.TIMED_OUT)
        assert run.is_failed() is False

    def test_is_failed_when_action_required(self):
        """is_failed should return False when conclusion is ACTION_REQUIRED."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_failed() is False

    def test_is_failed_when_neutral(self):
        """is_failed should return False when conclusion is NEUTRAL."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.NEUTRAL)
        assert run.is_failed() is False

    def test_is_failed_when_stale(self):
        """is_failed should return False when conclusion is STALE."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.STALE)
        assert run.is_failed() is False

    def test_is_failed_when_conclusion_is_none(self):
        """is_failed should return False when conclusion is None (not yet concluded)."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_failed() is False


class TestIsCancelled:
    """Test is_cancelled() method."""

    def test_is_cancelled_when_cancelled(self):
        """is_cancelled should return True when conclusion is CANCELLED."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    def test_is_cancelled_when_success(self):
        """is_cancelled should return False when conclusion is SUCCESS."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_cancelled() is False

    def test_is_cancelled_when_failure(self):
        """is_cancelled should return False when conclusion is FAILURE."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_cancelled() is False

    def test_is_cancelled_when_skipped(self):
        """is_cancelled should return False when conclusion is SKIPPED."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SKIPPED)
        assert run.is_cancelled() is False

    def test_is_cancelled_when_timed_out(self):
        """is_cancelled should return False when conclusion is TIMED_OUT."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.TIMED_OUT)
        assert run.is_cancelled() is False

    def test_is_cancelled_when_action_required(self):
        """is_cancelled should return False when conclusion is ACTION_REQUIRED."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_cancelled() is False

    def test_is_cancelled_when_neutral(self):
        """is_cancelled should return False when conclusion is NEUTRAL."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.NEUTRAL)
        assert run.is_cancelled() is False

    def test_is_cancelled_when_stale(self):
        """is_cancelled should return False when conclusion is STALE."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.STALE)
        assert run.is_cancelled() is False

    def test_is_cancelled_when_conclusion_is_none(self):
        """is_cancelled should return False when conclusion is None (not yet concluded)."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_cancelled() is False


class TestStateCombinations:
    """Test combinations of state-checking methods to ensure they behave correctly together."""

    def test_successful_run_is_terminal_and_successful(self):
        """A successful completed run should be terminal and successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True
        assert run.is_successful() is True
        assert run.is_running() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_failed_run_is_terminal_and_failed(self):
        """A failed completed run should be terminal and failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_terminal() is True
        assert run.is_failed() is True
        assert run.is_running() is False
        assert run.is_successful() is False
        assert run.is_cancelled() is False

    def test_cancelled_run_is_terminal_and_cancelled(self):
        """A cancelled completed run should be terminal and cancelled."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_terminal() is True
        assert run.is_cancelled() is True
        assert run.is_running() is False
        assert run.is_successful() is False
        assert run.is_failed() is False

    def test_in_progress_run_is_running_and_not_terminal(self):
        """An in-progress run should be running and not terminal."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_running() is True
        assert run.is_terminal() is False
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_queued_run_is_not_running_or_terminal(self):
        """A queued run should not be running or terminal."""
        run = _make_run(status=WorkflowStatus.QUEUED, conclusion=None)
        assert run.is_running() is False
        assert run.is_terminal() is False
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False
