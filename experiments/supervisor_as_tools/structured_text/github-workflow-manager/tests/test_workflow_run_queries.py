import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_run(status: WorkflowStatus, conclusion: WorkflowConclusion = None) -> WorkflowRun:
    """Create a test WorkflowRun with the given status and conclusion."""
    return WorkflowRun(
        id="test-run-1",
        workflow_name="Test Workflow",
        branch="main",
        status=status,
        conclusion=conclusion,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
    )


# All valid status values
STATUSES = [
    WorkflowStatus.QUEUED,
    WorkflowStatus.IN_PROGRESS,
    WorkflowStatus.COMPLETED,
    WorkflowStatus.WAITING,
    WorkflowStatus.REQUESTED,
    WorkflowStatus.PENDING,
]

# All valid conclusion values
CONCLUSIONS = [
    WorkflowConclusion.SUCCESS,
    WorkflowConclusion.FAILURE,
    WorkflowConclusion.CANCELLED,
    WorkflowConclusion.SKIPPED,
    WorkflowConclusion.TIMED_OUT,
    WorkflowConclusion.ACTION_REQUIRED,
    WorkflowConclusion.NEUTRAL,
    WorkflowConclusion.STALE,
    None,
]


class TestIsTerminal:
    """Test is_terminal() method."""

    @pytest.mark.parametrize("status,conclusion", [
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE),
    ])
    def test_terminal_true_when_completed_with_conclusion(self, status, conclusion):
        run = _make_run(status, conclusion)
        assert run.is_terminal() is True

    @pytest.mark.parametrize("status,conclusion", [
        (WorkflowStatus.QUEUED, None),
        (WorkflowStatus.QUEUED, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.IN_PROGRESS, None),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.FAILURE),
        (WorkflowStatus.WAITING, None),
        (WorkflowStatus.WAITING, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.REQUESTED, None),
        (WorkflowStatus.REQUESTED, WorkflowConclusion.CANCELLED),
        (WorkflowStatus.PENDING, None),
        (WorkflowStatus.PENDING, WorkflowConclusion.SKIPPED),
        (WorkflowStatus.COMPLETED, None),
    ])
    def test_terminal_false_when_not_completed_with_conclusion(self, status, conclusion):
        run = _make_run(status, conclusion)
        assert run.is_terminal() is False


class TestIsRunning:
    """Test is_running() method."""

    @pytest.mark.parametrize("status,conclusion", [
        (WorkflowStatus.QUEUED, None),
        (WorkflowStatus.IN_PROGRESS, None),
        (WorkflowStatus.WAITING, None),
        (WorkflowStatus.REQUESTED, None),
        (WorkflowStatus.PENDING, None),
    ])
    def test_running_true_when_not_completed_without_conclusion(self, status, conclusion):
        run = _make_run(status, conclusion)
        assert run.is_running() is True

    @pytest.mark.parametrize("status,conclusion", [
        (WorkflowStatus.COMPLETED, None),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
        (WorkflowStatus.QUEUED, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.CANCELLED),
        (WorkflowStatus.WAITING, WorkflowConclusion.SKIPPED),
        (WorkflowStatus.REQUESTED, WorkflowConclusion.TIMED_OUT),
        (WorkflowStatus.PENDING, WorkflowConclusion.ACTION_REQUIRED),
    ])
    def test_running_false_when_completed_or_has_conclusion(self, status, conclusion):
        run = _make_run(status, conclusion)
        assert run.is_running() is False


class TestIsSuccessful:
    """Test is_successful() method."""

    def test_successful_true_when_completed_with_success(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    @pytest.mark.parametrize("status,conclusion", [
        (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE),
        (WorkflowStatus.COMPLETED, None),
        (WorkflowStatus.QUEUED, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.WAITING, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.REQUESTED, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.PENDING, WorkflowConclusion.SUCCESS),
    ])
    def test_successful_false_when_not_completed_with_success(self, status, conclusion):
        run = _make_run(status, conclusion)
        assert run.is_successful() is False


class TestIsFailed:
    """Test is_failed() method."""

    def test_failed_true_when_completed_with_failure(self):
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    @pytest.mark.parametrize("status,conclusion", [
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE),
        (WorkflowStatus.COMPLETED, None),
        (WorkflowStatus.QUEUED, WorkflowConclusion.FAILURE),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.FAILURE),
        (WorkflowStatus.WAITING, WorkflowConclusion.FAILURE),
        (WorkflowStatus.REQUESTED, WorkflowConclusion.FAILURE),
        (WorkflowStatus.PENDING, WorkflowConclusion.FAILURE),
    ])
    def test_failed_false_when_not_completed_with_failure(self, status, conclusion):
        run = _make_run(status, conclusion)
        assert run.is_failed() is False


class TestIsCancelled:
    """Test is_cancelled() method."""

    @pytest.mark.parametrize("status", STATUSES)
    def test_cancelled_true_when_conclusion_is_cancelled(self, status):
        run = _make_run(status, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    @pytest.mark.parametrize("status,conclusion", [
        (WorkflowStatus.QUEUED, None),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
        (WorkflowStatus.WAITING, WorkflowConclusion.SKIPPED),
        (WorkflowStatus.REQUESTED, WorkflowConclusion.TIMED_OUT),
        (WorkflowStatus.PENDING, WorkflowConclusion.ACTION_REQUIRED),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE),
    ])
    def test_cancelled_false_when_conclusion_is_not_cancelled(self, status, conclusion):
        run = _make_run(status, conclusion)
        assert run.is_cancelled() is False


class TestMutualExclusivity:
    """Test mutual exclusivity invariants between query methods."""

    @pytest.mark.parametrize("status,conclusion", [
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED),
    ])
    def test_terminal_and_running_mutually_exclusive(self, status, conclusion):
        """Terminal and running states are mutually exclusive."""
        run = _make_run(status, conclusion)
        # If terminal is True, running must be False
        if run.is_terminal():
            assert run.is_running() is False
        # If running is True, terminal must be False
        if run.is_running():
            assert run.is_terminal() is False

    @pytest.mark.parametrize("status,conclusion", [
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
    ])
    def test_successful_and_failed_mutually_exclusive(self, status, conclusion):
        """Successful and failed states are mutually exclusive."""
        run = _make_run(status, conclusion)
        # Both cannot be true at the same time
        assert not (run.is_successful() and run.is_failed())

    @pytest.mark.parametrize("status", STATUSES)
    def test_cancelled_independent_of_other_states(self, status):
        """Cancelled can coexist with other conclusion values only when status/conclusion combo is valid."""
        run = _make_run(status, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    def test_successful_run_never_cancelled(self):
        """A successful run cannot also be cancelled."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True
        assert run.is_cancelled() is False

    def test_failed_run_never_cancelled(self):
        """A failed run cannot also be cancelled."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_failed() is True
        assert run.is_cancelled() is False


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_completed_with_none_conclusion_handled_gracefully(self):
        """COMPLETED status with None conclusion should be handled silently."""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_terminal() is False  # No conclusion, so not terminal
        assert run.is_running() is False  # Completed but has no conclusion
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_non_completed_with_conclusion_handled_gracefully(self):
        """Non-COMPLETED status with a conclusion should be handled silently."""
        run = _make_run(WorkflowStatus.QUEUED, WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is False  # Not completed
        assert run.is_running() is False  # Has conclusion despite not being completed
        assert run.is_successful() is False  # Not completed
        assert run.is_failed() is False  # Not completed
        assert run.is_cancelled() is False

    def test_valid_completed_with_each_conclusion(self):
        """Test all valid conclusion values with COMPLETED status."""
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
            run = _make_run(WorkflowStatus.COMPLETED, conclusion)
            assert run.is_terminal() is True
            assert run.is_running() is False

    def test_all_non_completed_statuses_with_none_conclusion_are_running(self):
        """All non-COMPLETED statuses with None conclusion should be running."""
        non_completed_statuses = [
            WorkflowStatus.QUEUED,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
        ]
        for status in non_completed_statuses:
            run = _make_run(status, None)
            assert run.is_running() is True
            assert run.is_terminal() is False
