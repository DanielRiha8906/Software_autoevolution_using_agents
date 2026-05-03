import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_run(
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion | None = WorkflowConclusion.SUCCESS,
) -> WorkflowRun:
    """Create a WorkflowRun with specified status and conclusion."""
    return WorkflowRun(
        id="test-run-1",
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

    def test_is_terminal_when_completed(self):
        run = _make_run(status=WorkflowStatus.COMPLETED)
        assert run.is_terminal() is True

    def test_is_terminal_when_not_completed(self):
        for status in [
            WorkflowStatus.QUEUED,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
        ]:
            run = _make_run(status=status)
            assert run.is_terminal() is False


class TestIsRunning:
    """Tests for is_running() method."""

    def test_is_running_when_in_progress(self):
        run = _make_run(status=WorkflowStatus.IN_PROGRESS)
        assert run.is_running() is True

    def test_is_running_when_not_in_progress(self):
        for status in [
            WorkflowStatus.QUEUED,
            WorkflowStatus.COMPLETED,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
        ]:
            run = _make_run(status=status)
            assert run.is_running() is False


class TestTerminalAndRunningMutuallyExclusive:
    """Tests to verify is_terminal() and is_running() are mutually exclusive."""

    def test_terminal_and_running_never_both_true(self):
        """Verify that a run cannot be both terminal and running."""
        for status in WorkflowStatus:
            run = _make_run(status=status)
            # Both should never be True at the same time
            assert not (run.is_terminal() and run.is_running())

    def test_all_statuses_are_covered(self):
        """Verify terminal and running cover all statuses appropriately."""
        statuses_and_expectations = {
            WorkflowStatus.QUEUED: (False, False),
            WorkflowStatus.IN_PROGRESS: (False, True),
            WorkflowStatus.COMPLETED: (True, False),
            WorkflowStatus.WAITING: (False, False),
            WorkflowStatus.REQUESTED: (False, False),
            WorkflowStatus.PENDING: (False, False),
        }
        for status, (expect_terminal, expect_running) in statuses_and_expectations.items():
            run = _make_run(status=status)
            assert run.is_terminal() is expect_terminal
            assert run.is_running() is expect_running


class TestIsSuccessful:
    """Tests for is_successful() method."""

    def test_is_successful_when_success(self):
        run = _make_run(conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    def test_is_successful_when_not_success(self):
        for conclusion in [
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.CANCELLED,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
        ]:
            run = _make_run(conclusion=conclusion)
            assert run.is_successful() is False

    def test_is_successful_with_no_conclusion(self):
        run = _make_run(conclusion=None)
        assert run.is_successful() is False


class TestIsFailed:
    """Tests for is_failed() method."""

    def test_is_failed_when_failure(self):
        run = _make_run(conclusion=WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    def test_is_failed_when_not_failure(self):
        for conclusion in [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.CANCELLED,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
        ]:
            run = _make_run(conclusion=conclusion)
            assert run.is_failed() is False

    def test_is_failed_with_no_conclusion(self):
        run = _make_run(conclusion=None)
        assert run.is_failed() is False


class TestSuccessfulAndFailedMutuallyExclusive:
    """Tests to verify is_successful() and is_failed() are mutually exclusive."""

    def test_successful_and_failed_never_both_true(self):
        """Verify that a run cannot be both successful and failed."""
        for conclusion in [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.CANCELLED,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
        ]:
            run = _make_run(conclusion=conclusion)
            assert not (run.is_successful() and run.is_failed())

    def test_with_no_conclusion(self):
        """Verify neither method returns True when conclusion is None."""
        run = _make_run(conclusion=None)
        assert run.is_successful() is False
        assert run.is_failed() is False


class TestIsCancelled:
    """Tests for is_cancelled() method."""

    def test_is_cancelled_when_cancelled(self):
        run = _make_run(conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    def test_is_cancelled_when_not_cancelled(self):
        for conclusion in [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
        ]:
            run = _make_run(conclusion=conclusion)
            assert run.is_cancelled() is False

    def test_is_cancelled_with_no_conclusion(self):
        run = _make_run(conclusion=None)
        assert run.is_cancelled() is False


class TestStateMethodsCombinations:
    """Tests for various combinations of state methods."""

    def test_completed_successful_run(self):
        """Test a successful completed run."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
        )
        assert run.is_terminal() is True
        assert run.is_running() is False
        assert run.is_successful() is True
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_completed_failed_run(self):
        """Test a failed completed run."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
        )
        assert run.is_terminal() is True
        assert run.is_running() is False
        assert run.is_successful() is False
        assert run.is_failed() is True
        assert run.is_cancelled() is False

    def test_completed_cancelled_run(self):
        """Test a cancelled completed run."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED,
        )
        assert run.is_terminal() is True
        assert run.is_running() is False
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is True

    def test_in_progress_run(self):
        """Test a run currently in progress."""
        run = _make_run(
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
        )
        assert run.is_terminal() is False
        assert run.is_running() is True
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_queued_run(self):
        """Test a queued run."""
        run = _make_run(
            status=WorkflowStatus.QUEUED,
            conclusion=None,
        )
        assert run.is_terminal() is False
        assert run.is_running() is False
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False
