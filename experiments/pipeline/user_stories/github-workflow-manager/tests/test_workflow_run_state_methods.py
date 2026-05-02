"""
Tests for WorkflowRun state-checking methods.

Covers:
- is_terminal() — terminal state detection
- is_running() — running/in-progress state detection
- is_successful() — successful conclusion detection
- is_failed() — failure conclusion detection
- is_cancelled() — cancellation detection
- Mutual exclusivity guarantees
- Edge cases (inconsistent state combinations)
- All enum values
"""

import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


# ============================================================================
# TEST HELPERS
# ============================================================================

def _make_run(status: WorkflowStatus, conclusion: WorkflowConclusion = None) -> WorkflowRun:
    """Create a test WorkflowRun with given status and conclusion."""
    return WorkflowRun(
        id="test-run-1",
        workflow_name="TestWorkflow",
        branch="main",
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123def456",
        duration_seconds=0.0,
    )


# ============================================================================
# TEST IS_TERMINAL()
# ============================================================================

class TestIsTerminal:
    """Test WorkflowRun.is_terminal() method."""

    def test_completed_status_is_terminal(self):
        """status=COMPLETED returns True regardless of conclusion."""
        for conclusion in [None, WorkflowConclusion.SUCCESS, WorkflowConclusion.FAILURE]:
            run = _make_run(WorkflowStatus.COMPLETED, conclusion)
            assert run.is_terminal() is True

    def test_queued_status_is_not_terminal(self):
        """status=QUEUED returns False."""
        run = _make_run(WorkflowStatus.QUEUED, None)
        assert run.is_terminal() is False

    def test_in_progress_status_is_not_terminal(self):
        """status=IN_PROGRESS returns False."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, None)
        assert run.is_terminal() is False

    def test_waiting_status_is_not_terminal(self):
        """status=WAITING returns False."""
        run = _make_run(WorkflowStatus.WAITING, None)
        assert run.is_terminal() is False

    def test_requested_status_is_not_terminal(self):
        """status=REQUESTED returns False."""
        run = _make_run(WorkflowStatus.REQUESTED, None)
        assert run.is_terminal() is False

    def test_pending_status_is_not_terminal(self):
        """status=PENDING returns False."""
        run = _make_run(WorkflowStatus.PENDING, None)
        assert run.is_terminal() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.QUEUED,
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.WAITING,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
    ])
    def test_all_non_terminal_statuses(self, status):
        """All non-COMPLETED statuses return False."""
        run = _make_run(status, None)
        assert run.is_terminal() is False

    def test_completed_with_all_conclusions(self):
        """COMPLETED is terminal with all possible conclusions."""
        conclusions = [
            None,
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


# ============================================================================
# TEST IS_RUNNING()
# ============================================================================

class TestIsRunning:
    """Test WorkflowRun.is_running() method."""

    def test_in_progress_status_is_running(self):
        """status=IN_PROGRESS returns True."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, None)
        assert run.is_running() is True

    def test_queued_status_is_running(self):
        """status=QUEUED returns True."""
        run = _make_run(WorkflowStatus.QUEUED, None)
        assert run.is_running() is True

    def test_requested_status_is_running(self):
        """status=REQUESTED returns True."""
        run = _make_run(WorkflowStatus.REQUESTED, None)
        assert run.is_running() is True

    def test_pending_status_is_running(self):
        """status=PENDING returns True."""
        run = _make_run(WorkflowStatus.PENDING, None)
        assert run.is_running() is True

    def test_waiting_status_is_running(self):
        """status=WAITING returns True."""
        run = _make_run(WorkflowStatus.WAITING, None)
        assert run.is_running() is True

    def test_completed_status_is_not_running(self):
        """status=COMPLETED returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_running() is False

    @pytest.mark.parametrize("status", [
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.QUEUED,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
        WorkflowStatus.WAITING,
    ])
    def test_all_running_statuses(self, status):
        """All running statuses return True."""
        run = _make_run(status, None)
        assert run.is_running() is True

    def test_running_with_all_conclusions(self):
        """Running statuses return True with any conclusion."""
        running_statuses = [
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.QUEUED,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
            WorkflowStatus.WAITING,
        ]
        conclusions = [
            None,
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.CANCELLED,
        ]
        for status in running_statuses:
            for conclusion in conclusions:
                run = _make_run(status, conclusion)
                assert run.is_running() is True


# ============================================================================
# TEST IS_SUCCESSFUL()
# ============================================================================

class TestIsSuccessful:
    """Test WorkflowRun.is_successful() method."""

    def test_success_conclusion_is_successful(self):
        """conclusion=SUCCESS returns True."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    def test_failure_conclusion_is_not_successful(self):
        """conclusion=FAILURE returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_successful() is False

    def test_cancelled_conclusion_is_not_successful(self):
        """conclusion=CANCELLED returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False

    def test_skipped_conclusion_is_not_successful(self):
        """conclusion=SKIPPED returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_successful() is False

    def test_timed_out_conclusion_is_not_successful(self):
        """conclusion=TIMED_OUT returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_successful() is False

    def test_action_required_conclusion_is_not_successful(self):
        """conclusion=ACTION_REQUIRED returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_successful() is False

    def test_neutral_conclusion_is_not_successful(self):
        """conclusion=NEUTRAL returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_successful() is False

    def test_stale_conclusion_is_not_successful(self):
        """conclusion=STALE returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_successful() is False

    def test_none_conclusion_is_not_successful(self):
        """conclusion=None returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_successful() is False

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.FAILURE,
        WorkflowConclusion.CANCELLED,
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
    ])
    def test_all_non_success_conclusions(self, conclusion):
        """All non-SUCCESS conclusions return False."""
        run = _make_run(WorkflowStatus.COMPLETED, conclusion)
        assert run.is_successful() is False

    def test_success_with_all_statuses(self):
        """conclusion=SUCCESS returns True with any status."""
        statuses = [
            WorkflowStatus.COMPLETED,
            WorkflowStatus.QUEUED,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
        ]
        for status in statuses:
            run = _make_run(status, WorkflowConclusion.SUCCESS)
            assert run.is_successful() is True


# ============================================================================
# TEST IS_FAILED()
# ============================================================================

class TestIsFailed:
    """Test WorkflowRun.is_failed() method."""

    def test_failure_conclusion_is_failed(self):
        """conclusion=FAILURE returns True."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    def test_success_conclusion_is_not_failed(self):
        """conclusion=SUCCESS returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_failed() is False

    def test_cancelled_conclusion_is_not_failed(self):
        """conclusion=CANCELLED returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_failed() is False

    def test_skipped_conclusion_is_not_failed(self):
        """conclusion=SKIPPED returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_failed() is False

    def test_timed_out_conclusion_is_not_failed(self):
        """conclusion=TIMED_OUT returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_failed() is False

    def test_action_required_conclusion_is_not_failed(self):
        """conclusion=ACTION_REQUIRED returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_failed() is False

    def test_neutral_conclusion_is_not_failed(self):
        """conclusion=NEUTRAL returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_failed() is False

    def test_stale_conclusion_is_not_failed(self):
        """conclusion=STALE returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_failed() is False

    def test_none_conclusion_is_not_failed(self):
        """conclusion=None returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_failed() is False

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.SUCCESS,
        WorkflowConclusion.CANCELLED,
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
    ])
    def test_all_non_failure_conclusions(self, conclusion):
        """All non-FAILURE conclusions return False."""
        run = _make_run(WorkflowStatus.COMPLETED, conclusion)
        assert run.is_failed() is False

    def test_failure_with_all_statuses(self):
        """conclusion=FAILURE returns True with any status."""
        statuses = [
            WorkflowStatus.COMPLETED,
            WorkflowStatus.QUEUED,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
        ]
        for status in statuses:
            run = _make_run(status, WorkflowConclusion.FAILURE)
            assert run.is_failed() is True


# ============================================================================
# TEST IS_CANCELLED()
# ============================================================================

class TestIsCancelled:
    """Test WorkflowRun.is_cancelled() method."""

    def test_cancelled_conclusion_is_cancelled(self):
        """conclusion=CANCELLED returns True."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_cancelled() is True

    def test_success_conclusion_is_not_cancelled(self):
        """conclusion=SUCCESS returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_cancelled() is False

    def test_failure_conclusion_is_not_cancelled(self):
        """conclusion=FAILURE returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_cancelled() is False

    def test_skipped_conclusion_is_not_cancelled(self):
        """conclusion=SKIPPED returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_cancelled() is False

    def test_timed_out_conclusion_is_not_cancelled(self):
        """conclusion=TIMED_OUT returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_cancelled() is False

    def test_action_required_conclusion_is_not_cancelled(self):
        """conclusion=ACTION_REQUIRED returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_cancelled() is False

    def test_neutral_conclusion_is_not_cancelled(self):
        """conclusion=NEUTRAL returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_cancelled() is False

    def test_stale_conclusion_is_not_cancelled(self):
        """conclusion=STALE returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_cancelled() is False

    def test_none_conclusion_is_not_cancelled(self):
        """conclusion=None returns False."""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_cancelled() is False

    @pytest.mark.parametrize("conclusion", [
        WorkflowConclusion.SUCCESS,
        WorkflowConclusion.FAILURE,
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
    ])
    def test_all_non_cancelled_conclusions(self, conclusion):
        """All non-CANCELLED conclusions return False."""
        run = _make_run(WorkflowStatus.COMPLETED, conclusion)
        assert run.is_cancelled() is False

    def test_cancelled_with_all_statuses(self):
        """conclusion=CANCELLED returns True with any status."""
        statuses = [
            WorkflowStatus.COMPLETED,
            WorkflowStatus.QUEUED,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
        ]
        for status in statuses:
            run = _make_run(status, WorkflowConclusion.CANCELLED)
            assert run.is_cancelled() is True


# ============================================================================
# TEST MUTUAL EXCLUSIVITY
# ============================================================================

class TestMutualExclusivity:
    """Test mutual exclusivity guarantees between state methods."""

    def test_is_terminal_and_is_running_mutually_exclusive(self):
        """is_terminal() and is_running() cannot both be True."""
        statuses = [
            (WorkflowStatus.COMPLETED, False, True),  # (status, expected_running, expected_terminal)
            (WorkflowStatus.IN_PROGRESS, True, False),
            (WorkflowStatus.QUEUED, True, False),
            (WorkflowStatus.REQUESTED, True, False),
            (WorkflowStatus.PENDING, True, False),
            (WorkflowStatus.WAITING, True, False),
        ]
        for status, expected_running, expected_terminal in statuses:
            run = _make_run(status, None)
            assert run.is_running() is expected_running
            assert run.is_terminal() is expected_terminal
            # Verify they're not both True
            assert not (run.is_running() and run.is_terminal())

    def test_is_successful_and_is_failed_mutually_exclusive(self):
        """is_successful() and is_failed() cannot both be True."""
        conclusions = [
            (WorkflowConclusion.SUCCESS, True, False),  # (conclusion, expected_success, expected_failed)
            (WorkflowConclusion.FAILURE, False, True),
            (WorkflowConclusion.CANCELLED, False, False),
            (WorkflowConclusion.SKIPPED, False, False),
            (WorkflowConclusion.TIMED_OUT, False, False),
            (WorkflowConclusion.ACTION_REQUIRED, False, False),
            (WorkflowConclusion.NEUTRAL, False, False),
            (WorkflowConclusion.STALE, False, False),
            (None, False, False),
        ]
        for conclusion, expected_success, expected_failed in conclusions:
            run = _make_run(WorkflowStatus.COMPLETED, conclusion)
            assert run.is_successful() is expected_success
            assert run.is_failed() is expected_failed
            # Verify they're not both True
            assert not (run.is_successful() and run.is_failed())

    def test_terminal_running_all_combinations(self):
        """For all statuses, exactly one of is_terminal() or is_running() is True."""
        all_statuses = [
            WorkflowStatus.COMPLETED,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.QUEUED,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
            WorkflowStatus.WAITING,
        ]
        for status in all_statuses:
            run = _make_run(status, None)
            is_term = run.is_terminal()
            is_run = run.is_running()
            # Exactly one should be True
            assert (is_term and not is_run) or (not is_term and is_run)

    def test_success_failure_all_conclusions(self):
        """For all conclusions, at most one of is_successful() or is_failed() is True."""
        all_conclusions = [
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
        for conclusion in all_conclusions:
            run = _make_run(WorkflowStatus.COMPLETED, conclusion)
            is_succ = run.is_successful()
            is_fail = run.is_failed()
            # Not both True
            assert not (is_succ and is_fail)


# ============================================================================
# TEST EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and logically inconsistent but valid state combinations."""

    def test_in_progress_with_success_conclusion(self):
        """IN_PROGRESS status with SUCCESS conclusion (inconsistent but valid)."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, WorkflowConclusion.SUCCESS)
        assert run.is_running() is True
        assert run.is_terminal() is False
        assert run.is_successful() is True
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_in_progress_with_failure_conclusion(self):
        """IN_PROGRESS status with FAILURE conclusion (inconsistent but valid)."""
        run = _make_run(WorkflowStatus.IN_PROGRESS, WorkflowConclusion.FAILURE)
        assert run.is_running() is True
        assert run.is_terminal() is False
        assert run.is_successful() is False
        assert run.is_failed() is True
        assert run.is_cancelled() is False

    def test_queued_with_cancelled_conclusion(self):
        """QUEUED status with CANCELLED conclusion (inconsistent but valid)."""
        run = _make_run(WorkflowStatus.QUEUED, WorkflowConclusion.CANCELLED)
        assert run.is_running() is True
        assert run.is_terminal() is False
        assert run.is_cancelled() is True
        assert run.is_successful() is False
        assert run.is_failed() is False

    def test_completed_without_conclusion(self):
        """COMPLETED status without conclusion (valid edge case)."""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_terminal() is True
        assert run.is_running() is False
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_completed_with_success_conclusion(self):
        """COMPLETED status with SUCCESS conclusion (normal case)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True
        assert run.is_running() is False
        assert run.is_successful() is True
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_completed_with_failure_conclusion(self):
        """COMPLETED status with FAILURE conclusion (normal case)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_terminal() is True
        assert run.is_running() is False
        assert run.is_successful() is False
        assert run.is_failed() is True
        assert run.is_cancelled() is False

    def test_completed_with_cancelled_conclusion(self):
        """COMPLETED status with CANCELLED conclusion (normal case)."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_terminal() is True
        assert run.is_running() is False
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is True

    def test_waiting_with_no_conclusion(self):
        """WAITING status with no conclusion (expected for running state)."""
        run = _make_run(WorkflowStatus.WAITING, None)
        assert run.is_running() is True
        assert run.is_terminal() is False
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_pending_with_neutral_conclusion(self):
        """PENDING status with NEUTRAL conclusion (inconsistent but valid)."""
        run = _make_run(WorkflowStatus.PENDING, WorkflowConclusion.NEUTRAL)
        assert run.is_running() is True
        assert run.is_terminal() is False
        assert run.is_successful() is False
        assert run.is_failed() is False
        assert run.is_cancelled() is False

    def test_completed_with_all_conclusions_exhaustive(self):
        """COMPLETED with each possible conclusion (exhaustive test)."""
        test_cases = [
            (None, False, False, False, False),
            (WorkflowConclusion.SUCCESS, True, False, False, False),
            (WorkflowConclusion.FAILURE, False, True, False, False),
            (WorkflowConclusion.CANCELLED, False, False, False, True),
            (WorkflowConclusion.SKIPPED, False, False, False, False),
            (WorkflowConclusion.TIMED_OUT, False, False, False, False),
            (WorkflowConclusion.ACTION_REQUIRED, False, False, False, False),
            (WorkflowConclusion.NEUTRAL, False, False, False, False),
            (WorkflowConclusion.STALE, False, False, False, False),
        ]
        for conclusion, exp_success, exp_fail, exp_running, exp_cancelled in test_cases:
            run = _make_run(WorkflowStatus.COMPLETED, conclusion)
            assert run.is_terminal() is True
            assert run.is_running() is False
            assert run.is_successful() is exp_success
            assert run.is_failed() is exp_fail
            assert run.is_cancelled() is exp_cancelled


# ============================================================================
# TEST SUMMARY TABLE (ALL COMBINATIONS)
# ============================================================================

class TestComprehensiveMatrix:
    """Comprehensive matrix of all status/conclusion combinations."""

    @pytest.mark.parametrize("status,conclusion,is_term,is_run,is_succ,is_fail,is_canc", [
        # COMPLETED status (terminal)
        (WorkflowStatus.COMPLETED, None, True, False, False, False, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS, True, False, True, False, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE, True, False, False, True, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED, True, False, False, False, True),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED, True, False, False, False, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT, True, False, False, False, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED, True, False, False, False, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL, True, False, False, False, False),
        (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE, True, False, False, False, False),
        # IN_PROGRESS status (running)
        (WorkflowStatus.IN_PROGRESS, None, False, True, False, False, False),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.SUCCESS, False, True, True, False, False),
        (WorkflowStatus.IN_PROGRESS, WorkflowConclusion.FAILURE, False, True, False, True, False),
        # QUEUED status (running)
        (WorkflowStatus.QUEUED, None, False, True, False, False, False),
        (WorkflowStatus.QUEUED, WorkflowConclusion.SUCCESS, False, True, True, False, False),
        # REQUESTED status (running)
        (WorkflowStatus.REQUESTED, None, False, True, False, False, False),
        (WorkflowStatus.REQUESTED, WorkflowConclusion.CANCELLED, False, True, False, False, True),
        # PENDING status (running)
        (WorkflowStatus.PENDING, None, False, True, False, False, False),
        # WAITING status (running)
        (WorkflowStatus.WAITING, None, False, True, False, False, False),
        (WorkflowStatus.WAITING, WorkflowConclusion.FAILURE, False, True, False, True, False),
    ])
    def test_state_matrix(
        self,
        status,
        conclusion,
        is_term,
        is_run,
        is_succ,
        is_fail,
        is_canc,
    ):
        """Test comprehensive matrix of state combinations."""
        run = _make_run(status, conclusion)
        assert run.is_terminal() is is_term, f"is_terminal() failed for {status}/{conclusion}"
        assert run.is_running() is is_run, f"is_running() failed for {status}/{conclusion}"
        assert run.is_successful() is is_succ, f"is_successful() failed for {status}/{conclusion}"
        assert run.is_failed() is is_fail, f"is_failed() failed for {status}/{conclusion}"
        assert run.is_cancelled() is is_canc, f"is_cancelled() failed for {status}/{conclusion}"
