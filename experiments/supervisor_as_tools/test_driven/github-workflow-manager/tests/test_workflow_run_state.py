import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_run(
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
) -> WorkflowRun:
    """Factory function to create WorkflowRun instances for testing."""
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


class TestIsRunning:
    """Tests for the is_running() method."""

    def test_is_running_when_in_progress(self):
        """is_running() should return True when status is IN_PROGRESS."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS)
        assert run.is_running() is True

    def test_is_running_false_when_completed(self):
        """is_running() should return False when status is COMPLETED."""
        run = _make_run(status=WorkflowStatus.COMPLETED)
        assert run.is_running() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_is_running_false_for_other_statuses(self, status):
        """is_running() should return False for all non-IN_PROGRESS statuses."""
        run = _make_run(status=status)
        assert run.is_running() is False


class TestIsTerminal:
    """Tests for the is_terminal() method."""

    def test_is_terminal_when_completed_success(self):
        """is_terminal() should return True when status is COMPLETED with SUCCESS conclusion."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
        )
        assert run.is_terminal() is True

    def test_is_terminal_when_completed_failure(self):
        """is_terminal() should return True when status is COMPLETED with FAILURE conclusion."""
        run = _make_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
        )
        assert run.is_terminal() is True

    def test_is_terminal_false_when_running(self):
        """is_terminal() should return False when status is IN_PROGRESS."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_terminal() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_is_terminal_false_for_non_completed_statuses(self, status):
        """is_terminal() should return False for all non-COMPLETED statuses."""
        run = _make_run(status=status, conclusion=None)
        assert run.is_terminal() is False


class TestIsSuccessful:
    """Tests for the is_successful() method."""

    def test_is_successful(self):
        """is_successful() should return True when conclusion is SUCCESS."""
        run = _make_run(conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.FAILURE,
        WorkflowConclusion.CANCELLED,
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
    ])
    def test_is_successful_false_for_other_conclusions(self, conclusion):
        """is_successful() should return False for all non-SUCCESS conclusions."""
        run = _make_run(conclusion=conclusion)
        assert run.is_successful() is False

    def test_is_successful_false_when_no_conclusion(self):
        """is_successful() should return False when conclusion is None."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_successful() is False


class TestIsFailed:
    """Tests for the is_failed() method."""

    def test_is_failed(self):
        """is_failed() should return True when conclusion is FAILURE."""
        run = _make_run(conclusion=WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.SUCCESS,
        WorkflowConclusion.CANCELLED,
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
    ])
    def test_is_failed_false_for_other_conclusions(self, conclusion):
        """is_failed() should return False for all non-FAILURE conclusions."""
        run = _make_run(conclusion=conclusion)
        assert run.is_failed() is False

    def test_is_failed_false_when_no_conclusion(self):
        """is_failed() should return False when conclusion is None."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_failed() is False


class TestIsCancelled:
    """Tests for the is_cancelled() method."""

    def test_is_cancelled(self):
        """is_cancelled() should return True when conclusion is CANCELLED."""
        run = _make_run(conclusion=WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.SUCCESS,
        WorkflowConclusion.FAILURE,
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
    ])
    def test_is_cancelled_false_for_other_conclusions(self, conclusion):
        """is_cancelled() should return False for all non-CANCELLED conclusions."""
        run = _make_run(conclusion=conclusion)
        assert run.is_cancelled() is False

    def test_is_cancelled_false_when_no_conclusion(self):
        """is_cancelled() should return False when conclusion is None."""
        run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
        assert run.is_cancelled() is False


class TestMutualExclusivity:
    """Tests that verify mutually exclusive conditions."""

    def test_is_running_and_is_terminal_are_mutually_exclusive(self):
        """A run cannot be both running and terminal simultaneously."""
        # Test all combinations
        statuses = [WorkflowStatus.QUEUED, WorkflowStatus.IN_PROGRESS,
                    WorkflowStatus.COMPLETED, WorkflowStatus.WAITING]

        for status in statuses:
            run = _make_run(status=status)
            # For any status, is_running() and is_terminal() should not both be True
            assert not (run.is_running() and run.is_terminal()), \
                f"Run with status {status.value} cannot be both running and terminal"

    def test_is_successful_and_is_failed_are_mutually_exclusive(self):
        """A run cannot be both successful and failed simultaneously."""
        conclusions = [WorkflowConclusion.SUCCESS, WorkflowConclusion.FAILURE,
                      WorkflowConclusion.CANCELLED, WorkflowConclusion.SKIPPED]

        for conclusion in conclusions:
            run = _make_run(conclusion=conclusion)
            # For any conclusion, is_successful() and is_failed() should not both be True
            assert not (run.is_successful() and run.is_failed()), \
                f"Run with conclusion {conclusion.value} cannot be both successful and failed"


class TestMethodsUsePureState:
    """Tests that verify methods use only status and conclusion fields."""

    def test_is_running_uses_only_status(self):
        """is_running() should depend only on the status field."""
        run1 = WorkflowRun(
            id="run1",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc",
        )
        run2 = WorkflowRun(
            id="run2",
            workflow_name="Different",
            branch="dev",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            run_number=999,
            commit_sha="xyz",
        )
        # Both should return True because status is the same
        assert run1.is_running() is True
        assert run2.is_running() is True

    def test_is_terminal_uses_only_status(self):
        """is_terminal() should depend only on the status field."""
        run1 = WorkflowRun(
            id="run1",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc",
        )
        run2 = WorkflowRun(
            id="run2",
            workflow_name="Different",
            branch="dev",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            run_number=999,
            commit_sha="xyz",
        )
        # Both should return True because status is the same
        assert run1.is_terminal() is True
        assert run2.is_terminal() is True

    def test_is_successful_uses_only_conclusion(self):
        """is_successful() should depend only on the conclusion field."""
        run1 = WorkflowRun(
            id="run1",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc",
        )
        run2 = WorkflowRun(
            id="run2",
            workflow_name="Different",
            branch="dev",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            run_number=999,
            commit_sha="xyz",
        )
        # Both should return True because conclusion is the same
        assert run1.is_successful() is True
        assert run2.is_successful() is True

    def test_is_failed_uses_only_conclusion(self):
        """is_failed() should depend only on the conclusion field."""
        run1 = WorkflowRun(
            id="run1",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc",
        )
        run2 = WorkflowRun(
            id="run2",
            workflow_name="Different",
            branch="dev",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            run_number=999,
            commit_sha="xyz",
        )
        # Both should return True because conclusion is the same
        assert run1.is_failed() is True
        assert run2.is_failed() is True

    def test_is_cancelled_uses_only_conclusion(self):
        """is_cancelled() should depend only on the conclusion field."""
        run1 = WorkflowRun(
            id="run1",
            workflow_name="Test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc",
        )
        run2 = WorkflowRun(
            id="run2",
            workflow_name="Different",
            branch="dev",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=WorkflowConclusion.CANCELLED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            run_number=999,
            commit_sha="xyz",
        )
        # Both should return True because conclusion is the same
        assert run1.is_cancelled() is True
        assert run2.is_cancelled() is True
