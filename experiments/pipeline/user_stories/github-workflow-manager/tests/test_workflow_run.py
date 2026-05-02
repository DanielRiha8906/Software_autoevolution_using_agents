import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_run(
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    run_id: str = "run-1",
) -> WorkflowRun:
    """Helper to create a WorkflowRun with custom status and conclusion."""
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
        duration_seconds=0.0,
    )


class TestIsTerminal:
    """Test is_terminal() method."""

    def test_is_terminal_with_completed_success(self):
        """is_terminal() returns True for COMPLETED/SUCCESS."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True

    def test_is_terminal_with_completed_failure(self):
        """is_terminal() returns True for COMPLETED/FAILURE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_terminal() is True

    def test_is_terminal_with_completed_cancelled(self):
        """is_terminal() returns True for COMPLETED/CANCELLED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_terminal() is True

    def test_is_terminal_with_completed_skipped(self):
        """is_terminal() returns True for COMPLETED/SKIPPED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_terminal() is True

    def test_is_terminal_with_completed_timed_out(self):
        """is_terminal() returns True for COMPLETED/TIMED_OUT."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_terminal() is True

    def test_is_terminal_with_completed_action_required(self):
        """is_terminal() returns True for COMPLETED/ACTION_REQUIRED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_terminal() is True

    def test_is_terminal_with_completed_neutral(self):
        """is_terminal() returns True for COMPLETED/NEUTRAL."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_terminal() is True

    def test_is_terminal_with_completed_stale(self):
        """is_terminal() returns True for COMPLETED/STALE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_terminal() is True

    def test_is_terminal_with_in_progress(self):
        """is_terminal() returns False for IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, None)
        assert run.is_terminal() is False

    def test_is_terminal_with_queued(self):
        """is_terminal() returns False for QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED, None)
        assert run.is_terminal() is False

    def test_is_terminal_with_waiting(self):
        """is_terminal() returns False for WAITING."""
        run = _make_run(WorkflowStatus.WAITING, None)
        assert run.is_terminal() is False

    def test_is_terminal_with_pending(self):
        """is_terminal() returns False for PENDING."""
        run = _make_run(WorkflowStatus.PENDING, None)
        assert run.is_terminal() is False

    def test_is_terminal_with_requested(self):
        """is_terminal() returns False for REQUESTED."""
        run = _make_run(WorkflowStatus.REQUESTED, None)
        assert run.is_terminal() is False


class TestIsRunning:
    """Test is_running() method."""

    def test_is_running_with_in_progress(self):
        """is_running() returns True for IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, None)
        assert run.is_running() is True

    def test_is_running_with_completed(self):
        """is_running() returns False for COMPLETED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_running() is False

    def test_is_running_with_queued(self):
        """is_running() returns False for QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED, None)
        assert run.is_running() is False

    def test_is_running_with_waiting(self):
        """is_running() returns False for WAITING."""
        run = _make_run(WorkflowStatus.WAITING, None)
        assert run.is_running() is False

    def test_is_running_with_pending(self):
        """is_running() returns False for PENDING."""
        run = _make_run(WorkflowStatus.PENDING, None)
        assert run.is_running() is False

    def test_is_running_with_requested(self):
        """is_running() returns False for REQUESTED."""
        run = _make_run(WorkflowStatus.REQUESTED, None)
        assert run.is_running() is False


class TestIsSuccessful:
    """Test is_successful() method."""

    def test_is_successful_with_success_conclusion(self):
        """is_successful() returns True for COMPLETED/SUCCESS."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    def test_is_successful_with_failure_conclusion(self):
        """is_successful() returns False for COMPLETED/FAILURE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_successful() is False

    def test_is_successful_with_cancelled_conclusion(self):
        """is_successful() returns False for COMPLETED/CANCELLED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False

    def test_is_successful_with_skipped_conclusion(self):
        """is_successful() returns False for COMPLETED/SKIPPED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_successful() is False

    def test_is_successful_with_timed_out_conclusion(self):
        """is_successful() returns False for COMPLETED/TIMED_OUT."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_successful() is False

    def test_is_successful_with_action_required_conclusion(self):
        """is_successful() returns False for COMPLETED/ACTION_REQUIRED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_successful() is False

    def test_is_successful_with_neutral_conclusion(self):
        """is_successful() returns False for COMPLETED/NEUTRAL."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_successful() is False

    def test_is_successful_with_stale_conclusion(self):
        """is_successful() returns False for COMPLETED/STALE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_successful() is False

    def test_is_successful_with_in_progress(self):
        """is_successful() returns False for IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, None)
        assert run.is_successful() is False

    def test_is_successful_with_queued(self):
        """is_successful() returns False for QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED, None)
        assert run.is_successful() is False


class TestIsFailed:
    """Test is_failed() method."""

    def test_is_failed_with_failure_conclusion(self):
        """is_failed() returns True for COMPLETED/FAILURE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    def test_is_failed_with_timed_out_conclusion(self):
        """is_failed() returns True for COMPLETED/TIMED_OUT."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_failed() is True

    def test_is_failed_with_action_required_conclusion(self):
        """is_failed() returns True for COMPLETED/ACTION_REQUIRED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_failed() is True

    def test_is_failed_with_success_conclusion(self):
        """is_failed() returns False for COMPLETED/SUCCESS."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_failed() is False

    def test_is_failed_with_cancelled_conclusion(self):
        """is_failed() returns False for COMPLETED/CANCELLED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_failed() is False

    def test_is_failed_with_skipped_conclusion(self):
        """is_failed() returns False for COMPLETED/SKIPPED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_failed() is False

    def test_is_failed_with_neutral_conclusion(self):
        """is_failed() returns False for COMPLETED/NEUTRAL."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_failed() is False

    def test_is_failed_with_stale_conclusion(self):
        """is_failed() returns False for COMPLETED/STALE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_failed() is False

    def test_is_failed_with_in_progress(self):
        """is_failed() returns False for IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, None)
        assert run.is_failed() is False

    def test_is_failed_with_queued(self):
        """is_failed() returns False for QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED, None)
        assert run.is_failed() is False


class TestIsCancelled:
    """Test is_cancelled() method."""

    def test_is_cancelled_with_cancelled_conclusion(self):
        """is_cancelled() returns True for COMPLETED/CANCELLED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    def test_is_cancelled_with_success_conclusion(self):
        """is_cancelled() returns False for COMPLETED/SUCCESS."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_failure_conclusion(self):
        """is_cancelled() returns False for COMPLETED/FAILURE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_skipped_conclusion(self):
        """is_cancelled() returns False for COMPLETED/SKIPPED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_timed_out_conclusion(self):
        """is_cancelled() returns False for COMPLETED/TIMED_OUT."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_action_required_conclusion(self):
        """is_cancelled() returns False for COMPLETED/ACTION_REQUIRED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_neutral_conclusion(self):
        """is_cancelled() returns False for COMPLETED/NEUTRAL."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_stale_conclusion(self):
        """is_cancelled() returns False for COMPLETED/STALE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_in_progress(self):
        """is_cancelled() returns False for IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, None)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_queued(self):
        """is_cancelled() returns False for QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED, None)
        assert run.is_cancelled() is False


class TestMutualExclusivity:
    """Test mutual exclusivity constraints."""

    def test_terminal_and_running_are_mutually_exclusive(self):
        """is_terminal() and is_running() are never both True."""
        # Test all statuses - terminal and running should never both be True
        for status in WorkflowStatus:
            if status == WorkflowStatus.COMPLETED:
                run = _make_run(status, WorkflowConclusion.SUCCESS)
                assert run.is_terminal() is True
                assert run.is_running() is False
            else:
                run = _make_run(status, None)
                assert run.is_terminal() is False
                if status == WorkflowStatus.IN_PROGRESS:
                    assert run.is_running() is True
                else:
                    assert run.is_running() is False

    def test_successful_and_failed_are_mutually_exclusive(self):
        """is_successful() and is_failed() are never both True."""
        # Test all conclusions with COMPLETED status
        for conclusion in WorkflowConclusion:
            run = _make_run(WorkflowStatus.COMPLETED, conclusion)
            is_successful = run.is_successful()
            is_failed = run.is_failed()
            # They should never both be True
            assert not (is_successful and is_failed), (
                f"is_successful() and is_failed() both True for {conclusion}"
            )
