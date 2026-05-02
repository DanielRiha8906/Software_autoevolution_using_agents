import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_run(
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = None,
    run_id: str = "run-1"
) -> WorkflowRun:
    """Helper to create a WorkflowRun with specified status and conclusion."""
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


class TestIsRunning:
    """Tests for the is_running() method."""

    def test_is_running_with_in_progress_status(self):
        """is_running() returns True when status is IN_PROGRESS."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS)
        assert run.is_running() is True

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.COMPLETED,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_is_running_with_non_in_progress_status(self, status):
        """is_running() returns False for all non-IN_PROGRESS statuses."""
        run = _make_run(status=status)
        assert run.is_running() is False


class TestIsTerminal:
    """Tests for the is_terminal() method."""

    def test_is_terminal_with_completed_status(self):
        """is_terminal() returns True when status is COMPLETED."""
        run = _make_run(status=WorkflowStatus.COMPLETED)
        assert run.is_terminal() is True

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_is_terminal_with_non_completed_status(self, status):
        """is_terminal() returns False for all non-COMPLETED statuses."""
        run = _make_run(status=status)
        assert run.is_terminal() is False


class TestIsSuccessful:
    """Tests for the is_successful() method."""

    def test_is_successful_with_completed_and_success(self):
        """is_successful() returns True when status is COMPLETED and conclusion is SUCCESS."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS
        )
        assert run.is_successful() is True

    def test_is_successful_with_completed_but_failure(self):
        """is_successful() returns False when status is COMPLETED but conclusion is FAILURE."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE
        )
        assert run.is_successful() is False

    def test_is_successful_with_completed_but_cancelled(self):
        """is_successful() returns False when status is COMPLETED but conclusion is CANCELLED."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED
        )
        assert run.is_successful() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_is_successful_with_non_completed_status(self, status):
        """is_successful() returns False when status is not COMPLETED, regardless of conclusion."""
        run = _make_run(
            status=status,
            conclusion=WorkflowConclusion.SUCCESS
        )
        assert run.is_successful() is False


class TestIsFailed:
    """Tests for the is_failed() method."""

    def test_is_failed_with_completed_and_failure(self):
        """is_failed() returns True when status is COMPLETED and conclusion is FAILURE."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE
        )
        assert run.is_failed() is True

    def test_is_failed_with_completed_but_success(self):
        """is_failed() returns False when status is COMPLETED but conclusion is SUCCESS."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS
        )
        assert run.is_failed() is False

    def test_is_failed_with_completed_but_cancelled(self):
        """is_failed() returns False when status is COMPLETED but conclusion is CANCELLED."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED
        )
        assert run.is_failed() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_is_failed_with_non_completed_status(self, status):
        """is_failed() returns False when status is not COMPLETED, regardless of conclusion."""
        run = _make_run(
            status=status,
            conclusion=WorkflowConclusion.FAILURE
        )
        assert run.is_failed() is False


class TestIsCancelled:
    """Tests for the is_cancelled() method."""

    def test_is_cancelled_with_completed_and_cancelled(self):
        """is_cancelled() returns True when status is COMPLETED and conclusion is CANCELLED."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED
        )
        assert run.is_cancelled() is True

    def test_is_cancelled_with_completed_but_success(self):
        """is_cancelled() returns False when status is COMPLETED but conclusion is SUCCESS."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS
        )
        assert run.is_cancelled() is False

    def test_is_cancelled_with_completed_but_failure(self):
        """is_cancelled() returns False when status is COMPLETED but conclusion is FAILURE."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE
        )
        assert run.is_cancelled() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_is_cancelled_with_non_completed_status(self, status):
        """is_cancelled() returns False when status is not COMPLETED, regardless of conclusion."""
        run = _make_run(
            status=status,
            conclusion=WorkflowConclusion.CANCELLED
        )
        assert run.is_cancelled() is False


class TestMutualExclusivity:
    """Tests for mutual exclusivity of is_running() and is_terminal()."""

    def test_running_and_terminal_mutually_exclusive(self):
        """A WorkflowRun cannot be both running and terminal."""
        # Test with IN_PROGRESS (running)
        run_in_progress = _make_run(status=WorkflowStatus.IN_PROGRESS)
        assert run_in_progress.is_running() is True
        assert run_in_progress.is_terminal() is False

        # Test with COMPLETED (terminal)
        run_completed = _make_run(status=WorkflowStatus.COMPLETED)
        assert run_completed.is_running() is False
        assert run_completed.is_terminal() is True

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_pending_states_are_neither_running_nor_terminal(self, status):
        """Pending states (not IN_PROGRESS or COMPLETED) are neither running nor terminal."""
        run = _make_run(status=status)
        assert run.is_running() is False
        assert run.is_terminal() is False


class TestMethodsUseCorrectFields:
    """Tests verifying methods only use status and conclusion fields."""

    def test_is_running_ignores_other_fields(self):
        """is_running() behavior is independent of non-status fields."""
        run1 = _make_run(
            status=WorkflowStatus.IN_PROGRESS,
            run_id="run-1"
        )
        run2 = _make_run(
            status=WorkflowStatus.IN_PROGRESS,
            run_id="run-2"
        )
        # Same status should give same is_running() result regardless of other fields
        assert run1.is_running() == run2.is_running()

    def test_is_terminal_ignores_other_fields(self):
        """is_terminal() behavior is independent of non-status fields."""
        run1 = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            run_id="run-1"
        )
        run2 = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            run_id="run-2"
        )
        # Same status should give same is_terminal() result regardless of other fields
        assert run1.is_terminal() == run2.is_terminal()

    def test_conclusion_dependent_methods_respect_conclusion(self):
        """Methods that depend on conclusion produce different results with different conclusions."""
        run_success = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS
        )
        run_failure = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE
        )
        run_cancelled = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED
        )

        # is_successful should differ
        assert run_success.is_successful() is True
        assert run_failure.is_successful() is False
        assert run_cancelled.is_successful() is False

        # is_failed should differ
        assert run_success.is_failed() is False
        assert run_failure.is_failed() is True
        assert run_cancelled.is_failed() is False

        # is_cancelled should differ
        assert run_success.is_cancelled() is False
        assert run_failure.is_cancelled() is False
        assert run_cancelled.is_cancelled() is True
