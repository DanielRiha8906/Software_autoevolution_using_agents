import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_run(
    status: WorkflowStatus,
    conclusion: WorkflowConclusion = None,
) -> WorkflowRun:
    """Helper to create a WorkflowRun with specified status and conclusion."""
    return WorkflowRun(
        id="test-run-1",
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


# Tests for is_terminal()
class TestIsTerminal:
    def test_is_terminal_completed(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True

    def test_is_terminal_completed_with_failure(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_terminal() is True

    def test_is_terminal_completed_with_cancelled(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_terminal() is True

    def test_is_terminal_queued(self):
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_terminal() is False

    def test_is_terminal_in_progress(self):
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_terminal() is False

    def test_is_terminal_waiting(self):
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_terminal() is False

    def test_is_terminal_requested(self):
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_terminal() is False

    def test_is_terminal_pending(self):
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_terminal() is False


# Tests for is_running()
class TestIsRunning:
    def test_is_running_in_progress(self):
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_running() is True

    def test_is_running_completed(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_running() is False

    def test_is_running_queued(self):
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_running() is False

    def test_is_running_waiting(self):
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_running() is False

    def test_is_running_requested(self):
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_running() is False

    def test_is_running_pending(self):
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_running() is False


# Tests for is_successful()
class TestIsSuccessful:
    def test_is_successful_completed_with_success(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    def test_is_successful_completed_with_failure(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_successful() is False

    def test_is_successful_completed_with_cancelled(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False

    def test_is_successful_in_progress(self):
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_successful() is False

    def test_is_successful_queued(self):
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_successful() is False

    def test_is_successful_completed_with_skipped(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_successful() is False

    def test_is_successful_completed_with_timed_out(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_successful() is False


# Tests for is_failed()
class TestIsFailed:
    def test_is_failed_completed_with_failure(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    def test_is_failed_completed_with_success(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_failed() is False

    def test_is_failed_completed_with_cancelled(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_failed() is False

    def test_is_failed_in_progress(self):
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_failed() is False

    def test_is_failed_queued(self):
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_failed() is False

    def test_is_failed_completed_with_skipped(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_failed() is False


# Tests for is_cancelled()
class TestIsCancelled:
    def test_is_cancelled_with_cancelled_conclusion(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    def test_is_cancelled_in_progress_with_cancelled(self):
        run = _make_run(WorkflowStatus.IN_PROGRESS, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    def test_is_cancelled_with_success_conclusion(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_failure_conclusion(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_no_conclusion(self):
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_skipped_conclusion(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_cancelled() is False


# Mutual exclusivity tests
class TestMutualExclusivity:
    def test_terminal_and_running_mutually_exclusive_completed(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True
        assert run.is_running() is False

    def test_terminal_and_running_mutually_exclusive_running(self):
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_terminal() is False
        assert run.is_running() is True

    def test_terminal_and_running_mutually_exclusive_queued(self):
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_terminal() is False
        assert run.is_running() is False

    def test_successful_and_failed_mutually_exclusive_success(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True
        assert run.is_failed() is False

    def test_successful_and_failed_mutually_exclusive_failure(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_successful() is False
        assert run.is_failed() is True

    def test_successful_and_failed_mutually_exclusive_in_progress(self):
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_successful() is False
        assert run.is_failed() is False

    def test_successful_and_failed_mutually_exclusive_cancelled(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False
        assert run.is_failed() is False


# Edge cases and conclusion combinations
class TestEdgeCases:
    def test_completed_with_skipped_conclusion(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_terminal() is True
        assert run.is_running() is False
        assert run.is_successful() is False
        assert run.is_failed() is False

    def test_completed_with_neutral_conclusion(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_terminal() is True
        assert run.is_successful() is False
        assert run.is_failed() is False

    def test_completed_with_timed_out_conclusion(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_terminal() is True
        assert run.is_successful() is False
        assert run.is_failed() is False

    def test_completed_with_action_required_conclusion(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_terminal() is True
        assert run.is_successful() is False
        assert run.is_failed() is False

    def test_completed_with_stale_conclusion(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_terminal() is True
        assert run.is_successful() is False
        assert run.is_failed() is False
