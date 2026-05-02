"""
Tests for WorkflowRun state predicate methods.

Covers:
- is_terminal(): Run has completed and will not change further
- is_successful(): Run completed successfully (status=COMPLETED, conclusion=SUCCESS)
- is_failed(): Run failed (status=COMPLETED, conclusion=FAILURE)
- is_running(): Run is still executing (status=IN_PROGRESS or REQUESTED)
- is_cancelled(): Run was cancelled (conclusion=CANCELLED)

Includes edge cases and constraint verification:
- is_terminal() and is_running() are mutually exclusive
- is_successful() and is_failed() are mutually exclusive
- None conclusion values
"""

import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


@pytest.fixture
def base_run():
    """Fixture providing a base WorkflowRun for testing."""
    return WorkflowRun(
        id="run-1",
        workflow_name="CI",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
    )


# ============================================================================
# is_terminal() Tests
# ============================================================================

class TestIsTerminal:
    """Test is_terminal() method for determining if run has terminated."""

    def test_is_terminal_true_when_completed(self, base_run):
        """is_terminal() should return True when status is COMPLETED."""
        assert base_run.status == WorkflowStatus.COMPLETED
        assert base_run.is_terminal() is True

    def test_is_terminal_true_with_success_conclusion(self):
        """is_terminal() should return True with COMPLETED status regardless of conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is True

    def test_is_terminal_true_with_failure_conclusion(self):
        """is_terminal() should return True with COMPLETED status and FAILURE conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is True

    def test_is_terminal_true_with_cancelled_conclusion(self):
        """is_terminal() should return True with COMPLETED status and CANCELLED conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is True

    def test_is_terminal_true_with_none_conclusion(self):
        """is_terminal() should return True with COMPLETED status even if conclusion is None."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is True

    def test_is_terminal_false_when_in_progress(self):
        """is_terminal() should return False when status is IN_PROGRESS."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is False

    def test_is_terminal_false_when_queued(self):
        """is_terminal() should return False when status is QUEUED."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.QUEUED,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is False

    def test_is_terminal_false_when_requested(self):
        """is_terminal() should return False when status is REQUESTED."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.REQUESTED,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is False

    def test_is_terminal_false_when_waiting(self):
        """is_terminal() should return False when status is WAITING."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.WAITING,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is False

    def test_is_terminal_false_when_pending(self):
        """is_terminal() should return False when status is PENDING."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.PENDING,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is False


# ============================================================================
# is_successful() Tests
# ============================================================================

class TestIsSuccessful:
    """Test is_successful() method for determining if run succeeded."""

    def test_is_successful_true_when_completed_with_success(self, base_run):
        """is_successful() should return True when status=COMPLETED and conclusion=SUCCESS."""
        assert base_run.status == WorkflowStatus.COMPLETED
        assert base_run.conclusion == WorkflowConclusion.SUCCESS
        assert base_run.is_successful() is True

    def test_is_successful_false_with_failure_conclusion(self):
        """is_successful() should return False with FAILURE conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False

    def test_is_successful_false_with_cancelled_conclusion(self):
        """is_successful() should return False with CANCELLED conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False

    def test_is_successful_false_with_skipped_conclusion(self):
        """is_successful() should return False with SKIPPED conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SKIPPED,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False

    def test_is_successful_false_with_timed_out_conclusion(self):
        """is_successful() should return False with TIMED_OUT conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.TIMED_OUT,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False

    def test_is_successful_false_with_action_required_conclusion(self):
        """is_successful() should return False with ACTION_REQUIRED conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.ACTION_REQUIRED,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False

    def test_is_successful_false_with_none_conclusion(self):
        """is_successful() should return False when conclusion is None."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False

    def test_is_successful_false_when_in_progress(self):
        """is_successful() should return False when status is IN_PROGRESS."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False

    def test_is_successful_false_when_queued(self):
        """is_successful() should return False when status is QUEUED."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.QUEUED,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False

    def test_is_successful_false_when_requested(self):
        """is_successful() should return False when status is REQUESTED."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.REQUESTED,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False


# ============================================================================
# is_failed() Tests
# ============================================================================

class TestIsFailed:
    """Test is_failed() method for determining if run failed."""

    def test_is_failed_true_when_completed_with_failure(self):
        """is_failed() should return True when status=COMPLETED and conclusion=FAILURE."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_failed() is True

    def test_is_failed_false_with_success_conclusion(self):
        """is_failed() should return False with SUCCESS conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_failed() is False

    def test_is_failed_false_with_cancelled_conclusion(self):
        """is_failed() should return False with CANCELLED conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_failed() is False

    def test_is_failed_false_with_skipped_conclusion(self):
        """is_failed() should return False with SKIPPED conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SKIPPED,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_failed() is False

    def test_is_failed_false_with_timed_out_conclusion(self):
        """is_failed() should return False with TIMED_OUT conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.TIMED_OUT,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_failed() is False

    def test_is_failed_false_with_none_conclusion(self):
        """is_failed() should return False when conclusion is None."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_failed() is False

    def test_is_failed_false_when_in_progress(self):
        """is_failed() should return False when status is IN_PROGRESS."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_failed() is False

    def test_is_failed_false_when_queued(self):
        """is_failed() should return False when status is QUEUED."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.QUEUED,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_failed() is False


# ============================================================================
# is_running() Tests
# ============================================================================

class TestIsRunning:
    """Test is_running() method for determining if run is still executing."""

    def test_is_running_true_when_in_progress(self):
        """is_running() should return True when status is IN_PROGRESS."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_running() is True

    def test_is_running_true_when_requested(self):
        """is_running() should return True when status is REQUESTED."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.REQUESTED,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_running() is True

    def test_is_running_false_when_completed(self):
        """is_running() should return False when status is COMPLETED."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_running() is False

    def test_is_running_false_when_queued(self):
        """is_running() should return False when status is QUEUED."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.QUEUED,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_running() is False

    def test_is_running_false_when_waiting(self):
        """is_running() should return False when status is WAITING."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.WAITING,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_running() is False

    def test_is_running_false_when_pending(self):
        """is_running() should return False when status is PENDING."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.PENDING,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_running() is False


# ============================================================================
# is_cancelled() Tests
# ============================================================================

class TestIsCancelled:
    """Test is_cancelled() method for determining if run was cancelled."""

    def test_is_cancelled_true_with_cancelled_conclusion(self):
        """is_cancelled() should return True when conclusion is CANCELLED."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_cancelled() is True

    def test_is_cancelled_true_with_cancelled_in_progress(self):
        """is_cancelled() should return True with CANCELLED conclusion even if not completed."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=WorkflowConclusion.CANCELLED,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_cancelled() is True

    def test_is_cancelled_false_with_success_conclusion(self):
        """is_cancelled() should return False with SUCCESS conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_cancelled() is False

    def test_is_cancelled_false_with_failure_conclusion(self):
        """is_cancelled() should return False with FAILURE conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_cancelled() is False

    def test_is_cancelled_false_with_skipped_conclusion(self):
        """is_cancelled() should return False with SKIPPED conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SKIPPED,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_cancelled() is False

    def test_is_cancelled_false_with_none_conclusion(self):
        """is_cancelled() should return False when conclusion is None."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_cancelled() is False


# ============================================================================
# Constraint Verification Tests
# ============================================================================

class TestMutualExclusivityConstraints:
    """Test that constraint invariants hold across all status/conclusion combinations."""

    def test_is_terminal_and_is_running_are_mutually_exclusive_when_completed(self):
        """is_terminal() and is_running() should never both be True."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is True
        assert run.is_running() is False

    def test_is_terminal_and_is_running_are_mutually_exclusive_when_in_progress(self):
        """is_terminal() and is_running() should never both be True."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.IN_PROGRESS,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is False
        assert run.is_running() is True

    def test_is_successful_and_is_failed_are_mutually_exclusive_success(self):
        """is_successful() and is_failed() should never both be True."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is True
        assert run.is_failed() is False

    def test_is_successful_and_is_failed_are_mutually_exclusive_failure(self):
        """is_successful() and is_failed() should never both be True."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False
        assert run.is_failed() is True

    def test_is_successful_and_is_failed_both_false_with_other_conclusion(self):
        """is_successful() and is_failed() should both be False for other conclusions."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_successful() is False
        assert run.is_failed() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_is_terminal_false_for_all_non_completed_statuses(self, status):
        """is_terminal() should return False for all non-COMPLETED statuses."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=status,
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        assert run.is_terminal() is False
        assert not run.is_terminal()

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.SUCCESS,
        WorkflowConclusion.FAILURE,
        WorkflowConclusion.CANCELLED,
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
    ])
    def test_is_cancelled_only_true_for_cancelled_conclusion(self, conclusion):
        """is_cancelled() should only return True for CANCELLED conclusion."""
        run = WorkflowRun(
            id="run-1",
            workflow_name="CI",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=conclusion,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha="abc123",
        )
        if conclusion == WorkflowConclusion.CANCELLED:
            assert run.is_cancelled() is True
        else:
            assert run.is_cancelled() is False
