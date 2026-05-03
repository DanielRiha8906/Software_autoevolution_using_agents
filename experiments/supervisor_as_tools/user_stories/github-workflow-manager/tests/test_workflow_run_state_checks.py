"""
Comprehensive tests for WorkflowRun state-checking methods.

Covers:
- is_terminal(): Run is completed regardless of conclusion
- is_running(): Run is in progress
- is_successful(): Run is completed with success conclusion
- is_failed(): Run is completed with failure conclusion
- is_cancelled(): Run is completed with cancelled conclusion
- Mutual exclusivity constraints
- Edge cases (e.g., COMPLETED with None conclusion)
- All WorkflowStatus and WorkflowConclusion values
"""

import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_run(
    status: WorkflowStatus,
    conclusion: WorkflowConclusion = None,
    run_id: str = "run-1"
) -> WorkflowRun:
    """Helper to create WorkflowRun instances with specified status/conclusion."""
    return WorkflowRun(
        id=run_id,
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


# ============================================================================
# is_terminal() Tests
# ============================================================================

class TestIsTerminal:
    """Test is_terminal() method"""

    def test_terminal_when_completed(self):
        """is_terminal() returns True when status is COMPLETED"""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True

    def test_terminal_with_various_conclusions(self):
        """is_terminal() returns True for COMPLETED with any conclusion"""
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

    def test_terminal_with_none_conclusion(self):
        """is_terminal() returns True for COMPLETED even with None conclusion"""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_terminal() is True

    def test_not_terminal_when_queued(self):
        """is_terminal() returns False when status is QUEUED"""
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_terminal() is False

    def test_not_terminal_when_in_progress(self):
        """is_terminal() returns False when status is IN_PROGRESS"""
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_terminal() is False

    def test_not_terminal_when_waiting(self):
        """is_terminal() returns False when status is WAITING"""
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_terminal() is False

    def test_not_terminal_when_requested(self):
        """is_terminal() returns False when status is REQUESTED"""
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_terminal() is False

    def test_not_terminal_when_pending(self):
        """is_terminal() returns False when status is PENDING"""
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_terminal() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_not_terminal_for_non_completed_statuses(self, status):
        """is_terminal() returns False for all non-COMPLETED statuses"""
        run = _make_run(status)
        assert run.is_terminal() is False


# ============================================================================
# is_running() Tests
# ============================================================================

class TestIsRunning:
    """Test is_running() method"""

    def test_running_when_in_progress(self):
        """is_running() returns True when status is IN_PROGRESS"""
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_running() is True

    def test_not_running_when_completed(self):
        """is_running() returns False when status is COMPLETED"""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_running() is False

    def test_not_running_when_queued(self):
        """is_running() returns False when status is QUEUED"""
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_running() is False

    def test_not_running_when_waiting(self):
        """is_running() returns False when status is WAITING"""
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_running() is False

    def test_not_running_when_requested(self):
        """is_running() returns False when status is REQUESTED"""
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_running() is False

    def test_not_running_when_pending(self):
        """is_running() returns False when status is PENDING"""
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_running() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.COMPLETED,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_not_running_for_non_in_progress_statuses(self, status):
        """is_running() returns False for all non-IN_PROGRESS statuses"""
        run = _make_run(status)
        assert run.is_running() is False


# ============================================================================
# is_successful() Tests
# ============================================================================

class TestIsSuccessful:
    """Test is_successful() method"""

    def test_successful_with_completed_and_success(self):
        """is_successful() returns True for COMPLETED + SUCCESS"""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    def test_not_successful_with_completed_and_failure(self):
        """is_successful() returns False for COMPLETED + FAILURE"""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_successful() is False

    def test_not_successful_with_completed_and_cancelled(self):
        """is_successful() returns False for COMPLETED + CANCELLED"""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False

    def test_not_successful_with_completed_and_none_conclusion(self):
        """is_successful() returns False for COMPLETED with None conclusion"""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_successful() is False

    def test_not_successful_with_in_progress_and_success(self):
        """is_successful() returns False for IN_PROGRESS (conclusion irrelevant)"""
        run = _make_run(WorkflowStatus.IN_PROGRESS, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is False

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
    ])
    def test_not_successful_with_other_conclusions(self, conclusion):
        """is_successful() returns False for COMPLETED with non-SUCCESS conclusions"""
        run = _make_run(WorkflowStatus.COMPLETED, conclusion)
        assert run.is_successful() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_not_successful_for_non_completed_statuses(self, status):
        """is_successful() returns False for non-COMPLETED statuses"""
        run = _make_run(status, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is False


# ============================================================================
# is_failed() Tests
# ============================================================================

class TestIsFailed:
    """Test is_failed() method"""

    def test_failed_with_completed_and_failure(self):
        """is_failed() returns True for COMPLETED + FAILURE"""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    def test_not_failed_with_completed_and_success(self):
        """is_failed() returns False for COMPLETED + SUCCESS"""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_failed() is False

    def test_not_failed_with_completed_and_cancelled(self):
        """is_failed() returns False for COMPLETED + CANCELLED"""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_failed() is False

    def test_not_failed_with_completed_and_none_conclusion(self):
        """is_failed() returns False for COMPLETED with None conclusion"""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_failed() is False

    def test_not_failed_with_in_progress_and_failure(self):
        """is_failed() returns False for IN_PROGRESS (conclusion irrelevant)"""
        run = _make_run(WorkflowStatus.IN_PROGRESS, WorkflowConclusion.FAILURE)
        assert run.is_failed() is False

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
    ])
    def test_not_failed_with_other_conclusions(self, conclusion):
        """is_failed() returns False for COMPLETED with non-FAILURE conclusions"""
        run = _make_run(WorkflowStatus.COMPLETED, conclusion)
        assert run.is_failed() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_not_failed_for_non_completed_statuses(self, status):
        """is_failed() returns False for non-COMPLETED statuses"""
        run = _make_run(status, WorkflowConclusion.FAILURE)
        assert run.is_failed() is False


# ============================================================================
# is_cancelled() Tests
# ============================================================================

class TestIsCancelled:
    """Test is_cancelled() method"""

    def test_cancelled_with_completed_and_cancelled(self):
        """is_cancelled() returns True for COMPLETED + CANCELLED"""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    def test_not_cancelled_with_completed_and_success(self):
        """is_cancelled() returns False for COMPLETED + SUCCESS"""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_cancelled() is False

    def test_not_cancelled_with_completed_and_failure(self):
        """is_cancelled() returns False for COMPLETED + FAILURE"""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_cancelled() is False

    def test_not_cancelled_with_completed_and_none_conclusion(self):
        """is_cancelled() returns False for COMPLETED with None conclusion"""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_cancelled() is False

    def test_not_cancelled_with_in_progress_and_cancelled(self):
        """is_cancelled() returns False for IN_PROGRESS (conclusion irrelevant)"""
        run = _make_run(WorkflowStatus.IN_PROGRESS, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is False

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
    ])
    def test_not_cancelled_with_other_conclusions(self, conclusion):
        """is_cancelled() returns False for COMPLETED with non-CANCELLED conclusions"""
        run = _make_run(WorkflowStatus.COMPLETED, conclusion)
        assert run.is_cancelled() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_not_cancelled_for_non_completed_statuses(self, status):
        """is_cancelled() returns False for non-COMPLETED statuses"""
        run = _make_run(status, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is False


# ============================================================================
# Mutual Exclusivity Tests
# ============================================================================

class TestMutualExclusivity:
    """Test mutual exclusivity of state-checking methods"""

    def test_running_excludes_terminal(self):
        """Running and terminal are mutually exclusive"""
        running = _make_run(WorkflowStatus.IN_PROGRESS)
        assert running.is_running() is True
        assert running.is_terminal() is False

    def test_successful_excludes_failed(self):
        """Successful and failed are mutually exclusive"""
        successful = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert successful.is_successful() is True
        assert successful.is_failed() is False

    def test_successful_excludes_cancelled(self):
        """Successful and cancelled are mutually exclusive"""
        successful = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert successful.is_successful() is True
        assert successful.is_cancelled() is False

    def test_failed_excludes_successful(self):
        """Failed and successful are mutually exclusive"""
        failed = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert failed.is_failed() is True
        assert failed.is_successful() is False

    def test_failed_excludes_cancelled(self):
        """Failed and cancelled are mutually exclusive"""
        failed = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert failed.is_failed() is True
        assert failed.is_cancelled() is False

    def test_cancelled_excludes_successful(self):
        """Cancelled and successful are mutually exclusive"""
        cancelled = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert cancelled.is_cancelled() is True
        assert cancelled.is_successful() is False

    def test_cancelled_excludes_failed(self):
        """Cancelled and failed are mutually exclusive"""
        cancelled = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert cancelled.is_cancelled() is True
        assert cancelled.is_failed() is False


# ============================================================================
# Edge Cases and All Status/Conclusion Combinations
# ============================================================================

class TestEdgeCases:
    """Test edge cases and corner scenarios"""

    def test_completed_with_all_conclusion_values(self):
        """is_terminal() returns True for COMPLETED with all conclusion values"""
        conclusions = [
            (WorkflowConclusion.SUCCESS, "SUCCESS"),
            (WorkflowConclusion.FAILURE, "FAILURE"),
            (WorkflowConclusion.CANCELLED, "CANCELLED"),
            (WorkflowConclusion.SKIPPED, "SKIPPED"),
            (WorkflowConclusion.TIMED_OUT, "TIMED_OUT"),
            (WorkflowConclusion.ACTION_REQUIRED, "ACTION_REQUIRED"),
            (WorkflowConclusion.NEUTRAL, "NEUTRAL"),
            (WorkflowConclusion.STALE, "STALE"),
        ]
        for conclusion, name in conclusions:
            run = _make_run(WorkflowStatus.COMPLETED, conclusion)
            assert run.is_terminal() is True, f"Failed for conclusion {name}"

    def test_completed_with_none_conclusion_is_terminal(self):
        """is_terminal() returns True for COMPLETED even with None conclusion"""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_terminal() is True

    def test_completed_with_none_conclusion_not_successful(self):
        """is_successful() returns False for COMPLETED with None conclusion"""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_successful() is False

    def test_completed_with_none_conclusion_not_failed(self):
        """is_failed() returns False for COMPLETED with None conclusion"""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_failed() is False

    def test_completed_with_none_conclusion_not_cancelled(self):
        """is_cancelled() returns False for COMPLETED with None conclusion"""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_cancelled() is False

    def test_all_non_terminal_statuses_are_not_terminal(self):
        """All non-COMPLETED statuses report is_terminal() as False"""
        non_terminal_statuses = [
            WorkflowStatus.QUEUED,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
        ]
        for status in non_terminal_statuses:
            run = _make_run(status)
            assert run.is_terminal() is False, f"Failed for status {status.value}"

    def test_specific_conclusion_only_on_completed(self):
        """Specific conclusion checks only return True for COMPLETED with that conclusion"""
        success_run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        failure_run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        cancelled_run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)

        # Only respective method returns True
        assert success_run.is_successful() is True
        assert success_run.is_failed() is False
        assert success_run.is_cancelled() is False

        assert failure_run.is_failed() is True
        assert failure_run.is_successful() is False
        assert failure_run.is_cancelled() is False

        assert cancelled_run.is_cancelled() is True
        assert cancelled_run.is_successful() is False
        assert cancelled_run.is_failed() is False
