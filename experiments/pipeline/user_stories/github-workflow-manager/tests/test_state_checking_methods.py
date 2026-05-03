"""
Tests for WorkflowRun state-checking methods.

Covers:
- is_terminal() — Run is COMPLETED with conclusion set
- is_successful() — Run is COMPLETED with SUCCESS conclusion
- is_failed() — Run is COMPLETED with FAILURE conclusion
- is_running() — Run status is IN_PROGRESS, REQUESTED, or PENDING
- is_cancelled() — Run is COMPLETED with CANCELLED conclusion

Tests cover:
- All 6 status values × 8 conclusion values = 48 combinations (most relevant tested explicitly)
- Mutually exclusive pairs
- Edge cases (None conclusion, etc.)
"""

import pytest
from datetime import datetime, timezone
from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


# ============================================================================
# TEST HELPERS
# ============================================================================

def _make_run(
    status: WorkflowStatus,
    conclusion: WorkflowConclusion = None,
) -> WorkflowRun:
    """Create a test WorkflowRun with specified status and conclusion."""
    return WorkflowRun(
        id="test-run-1",
        workflow_name="Test",
        branch="main",
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha=None,
        duration_seconds=0.0,
    )


# ============================================================================
# is_terminal() TESTS
# ============================================================================

class TestIsTerminal:
    """Test WorkflowRun.is_terminal() method."""

    def test_is_terminal_completed_with_success(self):
        """is_terminal() True when COMPLETED + SUCCESS."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True

    def test_is_terminal_completed_with_failure(self):
        """is_terminal() True when COMPLETED + FAILURE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_terminal() is True

    def test_is_terminal_completed_with_cancelled(self):
        """is_terminal() True when COMPLETED + CANCELLED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_terminal() is True

    def test_is_terminal_completed_with_skipped(self):
        """is_terminal() True when COMPLETED + SKIPPED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_terminal() is True

    def test_is_terminal_completed_with_timed_out(self):
        """is_terminal() True when COMPLETED + TIMED_OUT."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_terminal() is True

    def test_is_terminal_completed_with_action_required(self):
        """is_terminal() True when COMPLETED + ACTION_REQUIRED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_terminal() is True

    def test_is_terminal_completed_with_neutral(self):
        """is_terminal() True when COMPLETED + NEUTRAL."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_terminal() is True

    def test_is_terminal_completed_with_stale(self):
        """is_terminal() True when COMPLETED + STALE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_terminal() is True

    def test_is_terminal_completed_without_conclusion(self):
        """is_terminal() False when COMPLETED but conclusion is None."""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_terminal() is False

    def test_is_terminal_in_progress(self):
        """is_terminal() False when IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, None)
        assert run.is_terminal() is False

    def test_is_terminal_queued(self):
        """is_terminal() False when QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED, None)
        assert run.is_terminal() is False

    def test_is_terminal_waiting(self):
        """is_terminal() False when WAITING."""
        run = _make_run(WorkflowStatus.WAITING, None)
        assert run.is_terminal() is False

    def test_is_terminal_requested(self):
        """is_terminal() False when REQUESTED."""
        run = _make_run(WorkflowStatus.REQUESTED, None)
        assert run.is_terminal() is False

    def test_is_terminal_pending(self):
        """is_terminal() False when PENDING."""
        run = _make_run(WorkflowStatus.PENDING, None)
        assert run.is_terminal() is False


# ============================================================================
# is_successful() TESTS
# ============================================================================

class TestIsSuccessful:
    """Test WorkflowRun.is_successful() method."""

    def test_is_successful_completed_with_success(self):
        """is_successful() True when COMPLETED + SUCCESS."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    def test_is_successful_completed_without_conclusion(self):
        """is_successful() False when COMPLETED but no conclusion."""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_successful() is False

    def test_is_successful_completed_with_failure(self):
        """is_successful() False when COMPLETED + FAILURE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_successful() is False

    def test_is_successful_completed_with_cancelled(self):
        """is_successful() False when COMPLETED + CANCELLED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False

    def test_is_successful_completed_with_skipped(self):
        """is_successful() False when COMPLETED + SKIPPED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_successful() is False

    def test_is_successful_in_progress(self):
        """is_successful() False when IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, None)
        assert run.is_successful() is False

    def test_is_successful_queued(self):
        """is_successful() False when QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED, None)
        assert run.is_successful() is False

    def test_is_successful_waiting(self):
        """is_successful() False when WAITING."""
        run = _make_run(WorkflowStatus.WAITING, None)
        assert run.is_successful() is False

    def test_is_successful_requested(self):
        """is_successful() False when REQUESTED."""
        run = _make_run(WorkflowStatus.REQUESTED, None)
        assert run.is_successful() is False

    def test_is_successful_pending(self):
        """is_successful() False when PENDING."""
        run = _make_run(WorkflowStatus.PENDING, None)
        assert run.is_successful() is False


# ============================================================================
# is_failed() TESTS
# ============================================================================

class TestIsFailed:
    """Test WorkflowRun.is_failed() method."""

    def test_is_failed_completed_with_failure(self):
        """is_failed() True when COMPLETED + FAILURE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    def test_is_failed_completed_without_conclusion(self):
        """is_failed() False when COMPLETED but no conclusion."""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_failed() is False

    def test_is_failed_completed_with_success(self):
        """is_failed() False when COMPLETED + SUCCESS."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_failed() is False

    def test_is_failed_completed_with_cancelled(self):
        """is_failed() False when COMPLETED + CANCELLED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_failed() is False

    def test_is_failed_completed_with_skipped(self):
        """is_failed() False when COMPLETED + SKIPPED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_failed() is False

    def test_is_failed_in_progress(self):
        """is_failed() False when IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, None)
        assert run.is_failed() is False

    def test_is_failed_queued(self):
        """is_failed() False when QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED, None)
        assert run.is_failed() is False

    def test_is_failed_waiting(self):
        """is_failed() False when WAITING."""
        run = _make_run(WorkflowStatus.WAITING, None)
        assert run.is_failed() is False

    def test_is_failed_requested(self):
        """is_failed() False when REQUESTED."""
        run = _make_run(WorkflowStatus.REQUESTED, None)
        assert run.is_failed() is False

    def test_is_failed_pending(self):
        """is_failed() False when PENDING."""
        run = _make_run(WorkflowStatus.PENDING, None)
        assert run.is_failed() is False


# ============================================================================
# is_running() TESTS
# ============================================================================

class TestIsRunning:
    """Test WorkflowRun.is_running() method."""

    def test_is_running_in_progress(self):
        """is_running() True when IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, None)
        assert run.is_running() is True

    def test_is_running_requested(self):
        """is_running() True when REQUESTED."""
        run = _make_run(WorkflowStatus.REQUESTED, None)
        assert run.is_running() is True

    def test_is_running_pending(self):
        """is_running() True when PENDING."""
        run = _make_run(WorkflowStatus.PENDING, None)
        assert run.is_running() is True

    def test_is_running_completed(self):
        """is_running() False when COMPLETED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_running() is False

    def test_is_running_queued(self):
        """is_running() False when QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED, None)
        assert run.is_running() is False

    def test_is_running_waiting(self):
        """is_running() False when WAITING."""
        run = _make_run(WorkflowStatus.WAITING, None)
        assert run.is_running() is False


# ============================================================================
# is_cancelled() TESTS
# ============================================================================

class TestIsCancelled:
    """Test WorkflowRun.is_cancelled() method."""

    def test_is_cancelled_completed_with_cancelled(self):
        """is_cancelled() True when COMPLETED + CANCELLED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    def test_is_cancelled_completed_without_conclusion(self):
        """is_cancelled() False when COMPLETED but no conclusion."""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_cancelled() is False

    def test_is_cancelled_completed_with_success(self):
        """is_cancelled() False when COMPLETED + SUCCESS."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_cancelled() is False

    def test_is_cancelled_completed_with_failure(self):
        """is_cancelled() False when COMPLETED + FAILURE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_cancelled() is False

    def test_is_cancelled_completed_with_skipped(self):
        """is_cancelled() False when COMPLETED + SKIPPED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_cancelled() is False

    def test_is_cancelled_in_progress(self):
        """is_cancelled() False when IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, None)
        assert run.is_cancelled() is False

    def test_is_cancelled_queued(self):
        """is_cancelled() False when QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED, None)
        assert run.is_cancelled() is False

    def test_is_cancelled_waiting(self):
        """is_cancelled() False when WAITING."""
        run = _make_run(WorkflowStatus.WAITING, None)
        assert run.is_cancelled() is False

    def test_is_cancelled_requested(self):
        """is_cancelled() False when REQUESTED."""
        run = _make_run(WorkflowStatus.REQUESTED, None)
        assert run.is_cancelled() is False

    def test_is_cancelled_pending(self):
        """is_cancelled() False when PENDING."""
        run = _make_run(WorkflowStatus.PENDING, None)
        assert run.is_cancelled() is False


# ============================================================================
# MUTUALLY EXCLUSIVE PAIR TESTS
# ============================================================================

class TestMutuallyExclusivePairs:
    """Test that mutually exclusive state pairs cannot both be True."""

    def test_is_terminal_and_is_running_mutually_exclusive_running(self):
        """is_terminal() and is_running() cannot both be True (running case)."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, None)
        assert run.is_terminal() is False
        assert run.is_running() is True

    def test_is_terminal_and_is_running_mutually_exclusive_terminal(self):
        """is_terminal() and is_running() cannot both be True (terminal case)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True
        assert run.is_running() is False

    def test_is_successful_and_is_failed_mutually_exclusive_success(self):
        """is_successful() and is_failed() cannot both be True (success case)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True
        assert run.is_failed() is False

    def test_is_successful_and_is_failed_mutually_exclusive_failure(self):
        """is_successful() and is_failed() cannot both be True (failure case)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_successful() is False
        assert run.is_failed() is True

    def test_is_successful_and_is_cancelled_mutually_exclusive_success(self):
        """is_successful() and is_cancelled() cannot both be True (success case)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True
        assert run.is_cancelled() is False

    def test_is_successful_and_is_cancelled_mutually_exclusive_cancelled(self):
        """is_successful() and is_cancelled() cannot both be True (cancelled case)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False
        assert run.is_cancelled() is True

    def test_is_failed_and_is_cancelled_mutually_exclusive_failure(self):
        """is_failed() and is_cancelled() cannot both be True (failure case)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_failed() is True
        assert run.is_cancelled() is False

    def test_is_failed_and_is_cancelled_mutually_exclusive_cancelled(self):
        """is_failed() and is_cancelled() cannot both be True (cancelled case)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_failed() is False
        assert run.is_cancelled() is True


# ============================================================================
# SUBSET RELATIONSHIP TESTS
# ============================================================================

class TestSubsetRelationships:
    """Test that specific methods are subsets of is_terminal()."""

    def test_is_successful_implies_is_terminal(self):
        """If is_successful() True, then is_terminal() True."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True
        assert run.is_terminal() is True

    def test_is_failed_implies_is_terminal(self):
        """If is_failed() True, then is_terminal() True."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_failed() is True
        assert run.is_terminal() is True

    def test_is_cancelled_implies_is_terminal(self):
        """If is_cancelled() True, then is_terminal() True."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True
        assert run.is_terminal() is True


# ============================================================================
# EDGE CASES AND NON-SPECIFIC CONCLUSIONS
# ============================================================================

class TestNonSpecificTerminalStates:
    """Test terminal states that aren't covered by specific methods."""

    def test_is_terminal_with_skipped_conclusion(self):
        """is_terminal() True for SKIPPED (not covered by specific method)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_terminal() is True
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_is_terminal_with_timed_out_conclusion(self):
        """is_terminal() True for TIMED_OUT (not covered by specific method)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_terminal() is True
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_is_terminal_with_action_required_conclusion(self):
        """is_terminal() True for ACTION_REQUIRED (not covered by specific method)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_terminal() is True
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_is_terminal_with_neutral_conclusion(self):
        """is_terminal() True for NEUTRAL (not covered by specific method)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_terminal() is True
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_is_terminal_with_stale_conclusion(self):
        """is_terminal() True for STALE (not covered by specific method)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_terminal() is True
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False


# ============================================================================
# COMPREHENSIVE STATUS × CONCLUSION MATRIX TESTS
# ============================================================================

class TestAllStatusConclusionCombinations:
    """Test key combinations across all statuses and conclusions."""

    @pytest.mark.parametrize(
        "status,conclusion,expect_terminal",
        [
            # COMPLETED with each conclusion
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS, True),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE, True),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED, True),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED, True),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT, True),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED, True),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL, True),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE, True),
            # COMPLETED without conclusion
            (WorkflowStatus.COMPLETED, None, False),
            # Other statuses are not terminal
            (WorkflowStatus.IN_PROGRESS, None, False),
            (WorkflowStatus.QUEUED, None, False),
            (WorkflowStatus.WAITING, None, False),
            (WorkflowStatus.REQUESTED, None, False),
            (WorkflowStatus.PENDING, None, False),
        ],
    )
    def test_is_terminal_all_combinations(self, status, conclusion, expect_terminal):
        """is_terminal() correctly identifies all terminal states."""
        run = _make_run(status, conclusion)
        assert run.is_terminal() is expect_terminal

    @pytest.mark.parametrize(
        "status,conclusion,expect_running",
        [
            # Active statuses are running
            (WorkflowStatus.IN_PROGRESS, None, True),
            (WorkflowStatus.REQUESTED, None, True),
            (WorkflowStatus.PENDING, None, True),
            # Inactive statuses are not running
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS, False),
            (WorkflowStatus.QUEUED, None, False),
            (WorkflowStatus.WAITING, None, False),
        ],
    )
    def test_is_running_all_combinations(self, status, conclusion, expect_running):
        """is_running() correctly identifies all running states."""
        run = _make_run(status, conclusion)
        assert run.is_running() is expect_running
