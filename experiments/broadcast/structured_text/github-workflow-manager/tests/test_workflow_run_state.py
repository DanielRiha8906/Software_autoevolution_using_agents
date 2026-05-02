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
        id="test-run",
        workflow_name="CI",
        branch="main",
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=60.0,
    )


class TestIsRunning:
    """Test is_running() method."""

    def test_is_running_with_queued(self):
        """Queued status should be running."""
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_running() is True

    def test_is_running_with_in_progress(self):
        """In progress status should be running."""
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_running() is True

    def test_is_running_with_waiting(self):
        """Waiting status should be running."""
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_running() is True

    def test_is_running_with_requested(self):
        """Requested status should be running."""
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_running() is True

    def test_is_running_with_pending(self):
        """Pending status should be running."""
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_running() is True

    def test_is_running_with_completed(self):
        """Completed status should not be running."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_running() is False


class TestIsTerminal:
    """Test is_terminal() method."""

    def test_is_terminal_with_completed(self):
        """Completed status should be terminal."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True

    def test_is_terminal_with_completed_failure(self):
        """Completed status with failure conclusion should be terminal."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_terminal() is True

    def test_is_terminal_with_completed_cancelled(self):
        """Completed status with cancelled conclusion should be terminal."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_terminal() is True

    def test_is_terminal_with_queued(self):
        """Queued status should not be terminal."""
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_terminal() is False

    def test_is_terminal_with_in_progress(self):
        """In progress status should not be terminal."""
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_terminal() is False

    def test_is_terminal_with_waiting(self):
        """Waiting status should not be terminal."""
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_terminal() is False

    def test_is_terminal_with_requested(self):
        """Requested status should not be terminal."""
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_terminal() is False

    def test_is_terminal_with_pending(self):
        """Pending status should not be terminal."""
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_terminal() is False


class TestIsSuccessful:
    """Test is_successful() method."""

    def test_is_successful_with_completed_success(self):
        """Completed with success conclusion should be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    def test_is_successful_with_completed_failure(self):
        """Completed with failure conclusion should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_successful() is False

    def test_is_successful_with_completed_cancelled(self):
        """Completed with cancelled conclusion should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False

    def test_is_successful_with_completed_skipped(self):
        """Completed with skipped conclusion should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_successful() is False

    def test_is_successful_with_completed_timed_out(self):
        """Completed with timed_out conclusion should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_successful() is False

    def test_is_successful_with_completed_action_required(self):
        """Completed with action_required conclusion should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_successful() is False

    def test_is_successful_with_completed_neutral(self):
        """Completed with neutral conclusion should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_successful() is False

    def test_is_successful_with_completed_stale(self):
        """Completed with stale conclusion should not be successful."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_successful() is False

    def test_is_successful_with_queued(self):
        """Queued status should not be successful."""
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_successful() is False

    def test_is_successful_with_in_progress(self):
        """In progress status should not be successful."""
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_successful() is False

    def test_is_successful_with_waiting(self):
        """Waiting status should not be successful."""
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_successful() is False

    def test_is_successful_with_requested(self):
        """Requested status should not be successful."""
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_successful() is False

    def test_is_successful_with_pending(self):
        """Pending status should not be successful."""
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_successful() is False


class TestIsFailed:
    """Test is_failed() method."""

    def test_is_failed_with_completed_failure(self):
        """Completed with failure conclusion should be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    def test_is_failed_with_completed_timed_out(self):
        """Completed with timed_out conclusion should be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_failed() is True

    def test_is_failed_with_completed_success(self):
        """Completed with success conclusion should not be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_failed() is False

    def test_is_failed_with_completed_cancelled(self):
        """Completed with cancelled conclusion should not be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_failed() is False

    def test_is_failed_with_completed_skipped(self):
        """Completed with skipped conclusion should not be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_failed() is False

    def test_is_failed_with_completed_action_required(self):
        """Completed with action_required conclusion should not be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_failed() is False

    def test_is_failed_with_completed_neutral(self):
        """Completed with neutral conclusion should not be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_failed() is False

    def test_is_failed_with_completed_stale(self):
        """Completed with stale conclusion should not be failed."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_failed() is False

    def test_is_failed_with_queued(self):
        """Queued status should not be failed."""
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_failed() is False

    def test_is_failed_with_in_progress(self):
        """In progress status should not be failed."""
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_failed() is False

    def test_is_failed_with_waiting(self):
        """Waiting status should not be failed."""
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_failed() is False

    def test_is_failed_with_requested(self):
        """Requested status should not be failed."""
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_failed() is False

    def test_is_failed_with_pending(self):
        """Pending status should not be failed."""
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_failed() is False


class TestIsCancelled:
    """Test is_cancelled() method."""

    def test_is_cancelled_with_cancelled_conclusion(self):
        """Cancelled conclusion should be cancelled."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    def test_is_cancelled_with_success_conclusion(self):
        """Success conclusion should not be cancelled."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_failure_conclusion(self):
        """Failure conclusion should not be cancelled."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_skipped_conclusion(self):
        """Skipped conclusion should not be cancelled."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_timed_out_conclusion(self):
        """Timed out conclusion should not be cancelled."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_action_required_conclusion(self):
        """Action required conclusion should not be cancelled."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_neutral_conclusion(self):
        """Neutral conclusion should not be cancelled."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_stale_conclusion(self):
        """Stale conclusion should not be cancelled."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_cancelled() is False

    def test_is_cancelled_with_no_conclusion(self):
        """No conclusion should not be cancelled."""
        run = _make_run(WorkflowStatus.QUEUED, None)
        assert run.is_cancelled() is False


class TestMutualExclusivity:
    """Test mutual exclusivity constraints."""

    def test_is_terminal_and_is_running_are_mutually_exclusive(self):
        """is_terminal() and is_running() must be mutually exclusive."""
        # Test all statuses
        for status in WorkflowStatus:
            run = _make_run(status, WorkflowConclusion.SUCCESS)
            is_terminal = run.is_terminal()
            is_running = run.is_running()
            # They should never both be True
            assert not (is_terminal and is_running), (
                f"Status {status}: both is_terminal() and is_running() are True"
            )

    def test_is_successful_and_is_failed_are_mutually_exclusive(self):
        """is_successful() and is_failed() must be mutually exclusive."""
        # Test all status + conclusion combinations
        for status in WorkflowStatus:
            for conclusion in WorkflowConclusion:
                run = _make_run(status, conclusion)
                is_successful = run.is_successful()
                is_failed = run.is_failed()
                # They should never both be True
                assert not (is_successful and is_failed), (
                    f"Status {status}, Conclusion {conclusion}: "
                    "both is_successful() and is_failed() are True"
                )
