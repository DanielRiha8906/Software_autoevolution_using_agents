import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_run(
    run_id: str = "run-1",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
) -> WorkflowRun:
    """Helper to create a WorkflowRun instance for testing."""
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
    """Test is_terminal() method - should return True only for COMPLETED status."""

    def test_terminal_with_success(self):
        """COMPLETED + SUCCESS is terminal."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True

    def test_terminal_with_failure(self):
        """COMPLETED + FAILURE is terminal."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_terminal() is True

    def test_terminal_with_cancelled(self):
        """COMPLETED + CANCELLED is terminal."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_terminal() is True

    def test_terminal_with_skipped(self):
        """COMPLETED + SKIPPED is terminal."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SKIPPED)
        assert run.is_terminal() is True

    def test_terminal_with_timed_out(self):
        """COMPLETED + TIMED_OUT is terminal."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.TIMED_OUT)
        assert run.is_terminal() is True

    def test_terminal_with_action_required(self):
        """COMPLETED + ACTION_REQUIRED is terminal."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_terminal() is True

    def test_terminal_with_neutral(self):
        """COMPLETED + NEUTRAL is terminal."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.NEUTRAL)
        assert run.is_terminal() is True

    def test_terminal_with_stale(self):
        """COMPLETED + STALE is terminal."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.STALE)
        assert run.is_terminal() is True

    def test_not_terminal_queued(self):
        """QUEUED is not terminal."""
        run = _make_run(status=WorkflowStatus.QUEUED, conclusion=None)
        assert run.is_terminal() is False

    def test_not_terminal_in_progress(self):
        """IN_PROGRESS is not terminal."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_terminal() is False

    def test_not_terminal_waiting(self):
        """WAITING is not terminal."""
        run = _make_run(status=WorkflowStatus.WAITING, conclusion=None)
        assert run.is_terminal() is False

    def test_not_terminal_requested(self):
        """REQUESTED is not terminal."""
        run = _make_run(status=WorkflowStatus.REQUESTED, conclusion=None)
        assert run.is_terminal() is False

    def test_not_terminal_pending(self):
        """PENDING is not terminal."""
        run = _make_run(status=WorkflowStatus.PENDING, conclusion=None)
        assert run.is_terminal() is False


class TestIsRunning:
    """Test is_running() method - should return True for QUEUED, IN_PROGRESS, WAITING."""

    def test_running_queued(self):
        """QUEUED is running."""
        run = _make_run(status=WorkflowStatus.QUEUED, conclusion=None)
        assert run.is_running() is True

    def test_running_in_progress(self):
        """IN_PROGRESS is running."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_running() is True

    def test_running_waiting(self):
        """WAITING is running."""
        run = _make_run(status=WorkflowStatus.WAITING, conclusion=None)
        assert run.is_running() is True

    def test_not_running_requested(self):
        """REQUESTED is not running."""
        run = _make_run(status=WorkflowStatus.REQUESTED, conclusion=None)
        assert run.is_running() is False

    def test_not_running_pending(self):
        """PENDING is not running."""
        run = _make_run(status=WorkflowStatus.PENDING, conclusion=None)
        assert run.is_running() is False

    def test_not_running_completed(self):
        """COMPLETED is not running."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_running() is False


class TestIsSuccessful:
    """Test is_successful() method - should return True only for COMPLETED + SUCCESS."""

    def test_successful_completed_success(self):
        """COMPLETED + SUCCESS is successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    def test_not_successful_completed_failure(self):
        """COMPLETED + FAILURE is not successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_successful() is False

    def test_not_successful_completed_cancelled(self):
        """COMPLETED + CANCELLED is not successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False

    def test_not_successful_completed_skipped(self):
        """COMPLETED + SKIPPED is not successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SKIPPED)
        assert run.is_successful() is False

    def test_not_successful_completed_timed_out(self):
        """COMPLETED + TIMED_OUT is not successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.TIMED_OUT)
        assert run.is_successful() is False

    def test_not_successful_completed_action_required(self):
        """COMPLETED + ACTION_REQUIRED is not successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_successful() is False

    def test_not_successful_completed_neutral(self):
        """COMPLETED + NEUTRAL is not successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.NEUTRAL)
        assert run.is_successful() is False

    def test_not_successful_completed_stale(self):
        """COMPLETED + STALE is not successful."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.STALE)
        assert run.is_successful() is False

    def test_not_successful_queued(self):
        """QUEUED is not successful."""
        run = _make_run(status=WorkflowStatus.QUEUED, conclusion=None)
        assert run.is_successful() is False

    def test_not_successful_in_progress(self):
        """IN_PROGRESS is not successful."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_successful() is False


class TestIsFailed:
    """Test is_failed() method - should return True only for COMPLETED + FAILURE."""

    def test_failed_completed_failure(self):
        """COMPLETED + FAILURE is failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    def test_not_failed_completed_success(self):
        """COMPLETED + SUCCESS is not failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_failed() is False

    def test_not_failed_completed_cancelled(self):
        """COMPLETED + CANCELLED is not failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_failed() is False

    def test_not_failed_completed_skipped(self):
        """COMPLETED + SKIPPED is not failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SKIPPED)
        assert run.is_failed() is False

    def test_not_failed_completed_timed_out(self):
        """COMPLETED + TIMED_OUT is not failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.TIMED_OUT)
        assert run.is_failed() is False

    def test_not_failed_completed_action_required(self):
        """COMPLETED + ACTION_REQUIRED is not failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_failed() is False

    def test_not_failed_completed_neutral(self):
        """COMPLETED + NEUTRAL is not failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.NEUTRAL)
        assert run.is_failed() is False

    def test_not_failed_completed_stale(self):
        """COMPLETED + STALE is not failed."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.STALE)
        assert run.is_failed() is False

    def test_not_failed_queued(self):
        """QUEUED is not failed."""
        run = _make_run(status=WorkflowStatus.QUEUED, conclusion=None)
        assert run.is_failed() is False

    def test_not_failed_in_progress(self):
        """IN_PROGRESS is not failed."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_failed() is False


class TestIsCancelled:
    """Test is_cancelled() method - should return True only for COMPLETED + CANCELLED."""

    def test_cancelled_completed_cancelled(self):
        """COMPLETED + CANCELLED is cancelled."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    def test_not_cancelled_completed_success(self):
        """COMPLETED + SUCCESS is not cancelled."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_cancelled() is False

    def test_not_cancelled_completed_failure(self):
        """COMPLETED + FAILURE is not cancelled."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_cancelled() is False

    def test_not_cancelled_completed_skipped(self):
        """COMPLETED + SKIPPED is not cancelled."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SKIPPED)
        assert run.is_cancelled() is False

    def test_not_cancelled_completed_timed_out(self):
        """COMPLETED + TIMED_OUT is not cancelled."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.TIMED_OUT)
        assert run.is_cancelled() is False

    def test_not_cancelled_completed_action_required(self):
        """COMPLETED + ACTION_REQUIRED is not cancelled."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_cancelled() is False

    def test_not_cancelled_completed_neutral(self):
        """COMPLETED + NEUTRAL is not cancelled."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.NEUTRAL)
        assert run.is_cancelled() is False

    def test_not_cancelled_completed_stale(self):
        """COMPLETED + STALE is not cancelled."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.STALE)
        assert run.is_cancelled() is False

    def test_not_cancelled_queued(self):
        """QUEUED is not cancelled."""
        run = _make_run(status=WorkflowStatus.QUEUED, conclusion=None)
        assert run.is_cancelled() is False

    def test_not_cancelled_in_progress(self):
        """IN_PROGRESS is not cancelled."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_cancelled() is False


class TestMutualExclusivityConstraints:
    """Test mutual exclusivity constraints between state methods."""

    def test_terminal_and_running_never_both_true_completed(self):
        """COMPLETED + SUCCESS: is_terminal() True, is_running() False."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True
        assert run.is_running() is False

    def test_terminal_and_running_never_both_true_queued(self):
        """QUEUED: is_terminal() False, is_running() True."""
        run = _make_run(status=WorkflowStatus.QUEUED, conclusion=None)
        assert run.is_terminal() is False
        assert run.is_running() is True

    def test_terminal_and_running_never_both_true_in_progress(self):
        """IN_PROGRESS: is_terminal() False, is_running() True."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_terminal() is False
        assert run.is_running() is True

    def test_terminal_and_running_never_both_true_waiting(self):
        """WAITING: is_terminal() False, is_running() True."""
        run = _make_run(status=WorkflowStatus.WAITING, conclusion=None)
        assert run.is_terminal() is False
        assert run.is_running() is True

    def test_terminal_and_running_never_both_true_requested(self):
        """REQUESTED: is_terminal() False, is_running() False."""
        run = _make_run(status=WorkflowStatus.REQUESTED, conclusion=None)
        assert run.is_terminal() is False
        assert run.is_running() is False

    def test_terminal_and_running_never_both_true_pending(self):
        """PENDING: is_terminal() False, is_running() False."""
        run = _make_run(status=WorkflowStatus.PENDING, conclusion=None)
        assert run.is_terminal() is False
        assert run.is_running() is False

    def test_successful_and_failed_never_both_true_success(self):
        """COMPLETED + SUCCESS: is_successful() True, is_failed() False."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True
        assert run.is_failed() is False

    def test_successful_and_failed_never_both_true_failure(self):
        """COMPLETED + FAILURE: is_successful() False, is_failed() True."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_successful() is False
        assert run.is_failed() is True

    def test_successful_and_failed_never_both_true_cancelled(self):
        """COMPLETED + CANCELLED: both False."""
        run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False
        assert run.is_failed() is False

    def test_successful_and_failed_never_both_true_queued(self):
        """QUEUED: both False."""
        run = _make_run(status=WorkflowStatus.QUEUED, conclusion=None)
        assert run.is_successful() is False
        assert run.is_failed() is False


class TestEdgeCases:
    """Test edge cases and invalid combinations."""

    def test_invalid_queued_with_success_conclusion(self):
        """QUEUED + SUCCESS should be detectable as invalid (is_running() True, is_successful() False)."""
        run = _make_run(status=WorkflowStatus.QUEUED, conclusion=WorkflowConclusion.SUCCESS)
        # QUEUED should be running, not successful (conclusion should be None for running states)
        assert run.is_running() is True
        assert run.is_successful() is False

    def test_invalid_in_progress_with_failure_conclusion(self):
        """IN_PROGRESS + FAILURE should be detectable as invalid (is_running() True, is_failed() False)."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_running() is True
        assert run.is_failed() is False

    def test_invalid_waiting_with_cancelled_conclusion(self):
        """WAITING + CANCELLED should be detectable as invalid (is_running() True, is_cancelled() False)."""
        run = _make_run(status=WorkflowStatus.WAITING, conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_running() is True
        assert run.is_cancelled() is False

    def test_invalid_requested_with_conclusion(self):
        """REQUESTED + SUCCESS should be detectable as invalid (not running, not successful)."""
        run = _make_run(status=WorkflowStatus.REQUESTED, conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_running() is False
        assert run.is_successful() is False

    def test_invalid_pending_with_conclusion(self):
        """PENDING + FAILURE should be detectable as invalid (not running, not failed)."""
        run = _make_run(status=WorkflowStatus.PENDING, conclusion=WorkflowConclusion.FAILURE)
        assert run.is_running() is False
        assert run.is_failed() is False

    def test_all_terminal_conclusions_are_mutually_exclusive_success_vs_failure(self):
        """SUCCESS and FAILURE cannot both be True on same run."""
        success_run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        failure_run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
        assert success_run.is_successful() and not failure_run.is_successful()
        assert failure_run.is_failed() and not success_run.is_failed()

    def test_all_terminal_conclusions_are_mutually_exclusive_success_vs_cancelled(self):
        """SUCCESS and CANCELLED cannot both be True on same run."""
        success_run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        cancelled_run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
        assert success_run.is_successful() and not cancelled_run.is_successful()
        assert cancelled_run.is_cancelled() and not success_run.is_cancelled()

    def test_completed_with_any_conclusion_is_terminal(self):
        """All 8 terminal conclusions with COMPLETED status should be terminal."""
        conclusions = [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.CANCELLED,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
        ]
        for conclusion in conclusions:
            run = _make_run(status=WorkflowStatus.COMPLETED, conclusion=conclusion)
            assert run.is_terminal() is True, f"COMPLETED + {conclusion} should be terminal"

    def test_all_running_statuses_are_not_terminal(self):
        """All 5 running statuses should not be terminal."""
        running_statuses = [
            WorkflowStatus.QUEUED,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
        ]
        for status in running_statuses:
            run = _make_run(status=status, conclusion=None)
            assert run.is_terminal() is False, f"{status} should not be terminal"
