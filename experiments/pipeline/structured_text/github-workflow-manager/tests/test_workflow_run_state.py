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
        workflow_name="Test",
        branch="main",
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )


class TestIsRunning:
    """Test is_running() method across all status/conclusion combinations."""

    def test_is_running_true_when_in_progress(self):
        """is_running() returns True only when status is IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_running() is True

    def test_is_running_false_for_queued(self):
        """is_running() returns False when status is QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_running() is False

    def test_is_running_false_for_completed(self):
        """is_running() returns False when status is COMPLETED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_running() is False

    def test_is_running_false_for_waiting(self):
        """is_running() returns False when status is WAITING."""
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_running() is False

    def test_is_running_false_for_requested(self):
        """is_running() returns False when status is REQUESTED."""
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_running() is False

    def test_is_running_false_for_pending(self):
        """is_running() returns False when status is PENDING."""
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_running() is False


class TestIsTerminal:
    """Test is_terminal() method across all status/conclusion combinations."""

    def test_is_terminal_true_when_completed(self):
        """is_terminal() returns True only when status is COMPLETED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_terminal() is True

    def test_is_terminal_false_for_queued(self):
        """is_terminal() returns False when status is QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_terminal() is False

    def test_is_terminal_false_for_in_progress(self):
        """is_terminal() returns False when status is IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_terminal() is False

    def test_is_terminal_false_for_waiting(self):
        """is_terminal() returns False when status is WAITING."""
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_terminal() is False

    def test_is_terminal_false_for_requested(self):
        """is_terminal() returns False when status is REQUESTED."""
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_terminal() is False

    def test_is_terminal_false_for_pending(self):
        """is_terminal() returns False when status is PENDING."""
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_terminal() is False


class TestMutualExclusivityRunningVsTerminal:
    """Test that is_running() and is_terminal() are mutually exclusive."""

    def test_running_and_terminal_never_both_true(self):
        """is_running() and is_terminal() are never both True."""
        for status in WorkflowStatus:
            for conclusion in [*WorkflowConclusion, None]:
                run = _make_run(status, conclusion)
                assert not (run.is_running() and run.is_terminal()), (
                    f"Both is_running() and is_terminal() are True "
                    f"for status={status}, conclusion={conclusion}"
                )

    def test_at_least_one_true_for_active_states(self):
        """For active states (IN_PROGRESS or COMPLETED), exactly one is True."""
        # IN_PROGRESS: is_running() True, is_terminal() False
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_running() is True
        assert run.is_terminal() is False

        # COMPLETED: is_running() False, is_terminal() True
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_running() is False
        assert run.is_terminal() is True


class TestIsSuccessful:
    """Test is_successful() method across all status/conclusion combinations."""

    def test_is_successful_true_for_completed_success(self):
        """is_successful() returns True only for COMPLETED + SUCCESS."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_successful() is True

    def test_is_successful_false_for_completed_failure(self):
        """is_successful() returns False for COMPLETED + FAILURE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_successful() is False

    def test_is_successful_false_for_completed_cancelled(self):
        """is_successful() returns False for COMPLETED + CANCELLED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_successful() is False

    def test_is_successful_false_for_completed_skipped(self):
        """is_successful() returns False for COMPLETED + SKIPPED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_successful() is False

    def test_is_successful_false_for_completed_timed_out(self):
        """is_successful() returns False for COMPLETED + TIMED_OUT."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_successful() is False

    def test_is_successful_false_for_completed_action_required(self):
        """is_successful() returns False for COMPLETED + ACTION_REQUIRED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_successful() is False

    def test_is_successful_false_for_completed_neutral(self):
        """is_successful() returns False for COMPLETED + NEUTRAL."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_successful() is False

    def test_is_successful_false_for_completed_stale(self):
        """is_successful() returns False for COMPLETED + STALE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_successful() is False

    def test_is_successful_false_for_completed_no_conclusion(self):
        """is_successful() returns False for COMPLETED with no conclusion."""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_successful() is False

    def test_is_successful_false_for_in_progress(self):
        """is_successful() returns False for IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_successful() is False

    def test_is_successful_false_for_queued(self):
        """is_successful() returns False for QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_successful() is False

    def test_is_successful_false_for_waiting(self):
        """is_successful() returns False for WAITING."""
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_successful() is False

    def test_is_successful_false_for_requested(self):
        """is_successful() returns False for REQUESTED."""
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_successful() is False

    def test_is_successful_false_for_pending(self):
        """is_successful() returns False for PENDING."""
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_successful() is False


class TestIsFailed:
    """Test is_failed() method across all status/conclusion combinations."""

    def test_is_failed_true_for_completed_failure(self):
        """is_failed() returns True only for COMPLETED + FAILURE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
        assert run.is_failed() is True

    def test_is_failed_false_for_completed_success(self):
        """is_failed() returns False for COMPLETED + SUCCESS."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
        assert run.is_failed() is False

    def test_is_failed_false_for_completed_cancelled(self):
        """is_failed() returns False for COMPLETED + CANCELLED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
        assert run.is_failed() is False

    def test_is_failed_false_for_completed_skipped(self):
        """is_failed() returns False for COMPLETED + SKIPPED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
        assert run.is_failed() is False

    def test_is_failed_false_for_completed_timed_out(self):
        """is_failed() returns False for COMPLETED + TIMED_OUT."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
        assert run.is_failed() is False

    def test_is_failed_false_for_completed_action_required(self):
        """is_failed() returns False for COMPLETED + ACTION_REQUIRED."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
        assert run.is_failed() is False

    def test_is_failed_false_for_completed_neutral(self):
        """is_failed() returns False for COMPLETED + NEUTRAL."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
        assert run.is_failed() is False

    def test_is_failed_false_for_completed_stale(self):
        """is_failed() returns False for COMPLETED + STALE."""
        run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
        assert run.is_failed() is False

    def test_is_failed_false_for_completed_no_conclusion(self):
        """is_failed() returns False for COMPLETED with no conclusion."""
        run = _make_run(WorkflowStatus.COMPLETED, None)
        assert run.is_failed() is False

    def test_is_failed_false_for_in_progress(self):
        """is_failed() returns False for IN_PROGRESS."""
        run = _make_run(WorkflowStatus.IN_PROGRESS)
        assert run.is_failed() is False

    def test_is_failed_false_for_queued(self):
        """is_failed() returns False for QUEUED."""
        run = _make_run(WorkflowStatus.QUEUED)
        assert run.is_failed() is False

    def test_is_failed_false_for_waiting(self):
        """is_failed() returns False for WAITING."""
        run = _make_run(WorkflowStatus.WAITING)
        assert run.is_failed() is False

    def test_is_failed_false_for_requested(self):
        """is_failed() returns False for REQUESTED."""
        run = _make_run(WorkflowStatus.REQUESTED)
        assert run.is_failed() is False

    def test_is_failed_false_for_pending(self):
        """is_failed() returns False for PENDING."""
        run = _make_run(WorkflowStatus.PENDING)
        assert run.is_failed() is False


class TestMutualExclusivitySuccessfulVsFailed:
    """Test that is_successful() and is_failed() are mutually exclusive."""

    def test_successful_and_failed_never_both_true(self):
        """is_successful() and is_failed() are never both True."""
        for status in WorkflowStatus:
            for conclusion in [*WorkflowConclusion, None]:
                run = _make_run(status, conclusion)
                assert not (run.is_successful() and run.is_failed()), (
                    f"Both is_successful() and is_failed() are True "
                    f"for status={status}, conclusion={conclusion}"
                )

    def test_at_most_one_true_for_completed(self):
        """For COMPLETED status, at most one of is_successful() or is_failed() is True."""
        conclusions = [
            (WorkflowConclusion.SUCCESS, True, False),
            (WorkflowConclusion.FAILURE, False, True),
            (WorkflowConclusion.CANCELLED, False, False),
            (WorkflowConclusion.SKIPPED, False, False),
            (WorkflowConclusion.TIMED_OUT, False, False),
            (WorkflowConclusion.ACTION_REQUIRED, False, False),
            (WorkflowConclusion.NEUTRAL, False, False),
            (WorkflowConclusion.STALE, False, False),
            (None, False, False),
        ]
        for conclusion, expected_success, expected_failure in conclusions:
            run = _make_run(WorkflowStatus.COMPLETED, conclusion)
            assert run.is_successful() is expected_success, (
                f"is_successful() mismatch for conclusion={conclusion}"
            )
            assert run.is_failed() is expected_failure, (
                f"is_failed() mismatch for conclusion={conclusion}"
            )


class TestIsCancelled:
    """Test is_cancelled() method across all status/conclusion combinations."""

    def test_is_cancelled_true_for_cancelled_conclusion(self):
        """is_cancelled() returns True when conclusion is CANCELLED."""
        for status in WorkflowStatus:
            run = _make_run(status, WorkflowConclusion.CANCELLED)
            assert run.is_cancelled() is True, (
                f"is_cancelled() should be True for status={status}, "
                f"conclusion=CANCELLED"
            )

    def test_is_cancelled_false_for_success(self):
        """is_cancelled() returns False for SUCCESS conclusion."""
        for status in WorkflowStatus:
            run = _make_run(status, WorkflowConclusion.SUCCESS)
            assert run.is_cancelled() is False

    def test_is_cancelled_false_for_failure(self):
        """is_cancelled() returns False for FAILURE conclusion."""
        for status in WorkflowStatus:
            run = _make_run(status, WorkflowConclusion.FAILURE)
            assert run.is_cancelled() is False

    def test_is_cancelled_false_for_skipped(self):
        """is_cancelled() returns False for SKIPPED conclusion."""
        for status in WorkflowStatus:
            run = _make_run(status, WorkflowConclusion.SKIPPED)
            assert run.is_cancelled() is False

    def test_is_cancelled_false_for_timed_out(self):
        """is_cancelled() returns False for TIMED_OUT conclusion."""
        for status in WorkflowStatus:
            run = _make_run(status, WorkflowConclusion.TIMED_OUT)
            assert run.is_cancelled() is False

    def test_is_cancelled_false_for_action_required(self):
        """is_cancelled() returns False for ACTION_REQUIRED conclusion."""
        for status in WorkflowStatus:
            run = _make_run(status, WorkflowConclusion.ACTION_REQUIRED)
            assert run.is_cancelled() is False

    def test_is_cancelled_false_for_neutral(self):
        """is_cancelled() returns False for NEUTRAL conclusion."""
        for status in WorkflowStatus:
            run = _make_run(status, WorkflowConclusion.NEUTRAL)
            assert run.is_cancelled() is False

    def test_is_cancelled_false_for_stale(self):
        """is_cancelled() returns False for STALE conclusion."""
        for status in WorkflowStatus:
            run = _make_run(status, WorkflowConclusion.STALE)
            assert run.is_cancelled() is False

    def test_is_cancelled_false_for_none_conclusion(self):
        """is_cancelled() returns False when conclusion is None."""
        for status in WorkflowStatus:
            run = _make_run(status, None)
            assert run.is_cancelled() is False


class TestComprehensiveCombinations:
    """Comprehensive test of all 54 status/conclusion combinations."""

    def test_all_54_combinations_return_bool_not_truthy(self):
        """All state methods return actual bool (True/False), not truthy/falsy values."""
        for status in WorkflowStatus:
            for conclusion in [*WorkflowConclusion, None]:
                run = _make_run(status, conclusion)

                # Test that return values are actual bools
                assert isinstance(run.is_running(), bool)
                assert isinstance(run.is_terminal(), bool)
                assert isinstance(run.is_successful(), bool)
                assert isinstance(run.is_failed(), bool)
                assert isinstance(run.is_cancelled(), bool)

    def test_all_combinations_are_logically_sound(self):
        """All combinations satisfy logical constraints."""
        for status in WorkflowStatus:
            for conclusion in [*WorkflowConclusion, None]:
                run = _make_run(status, conclusion)

                # Constraint 1: is_running() and is_terminal() are mutually exclusive
                assert not (run.is_running() and run.is_terminal())

                # Constraint 2: is_successful() and is_failed() are mutually exclusive
                assert not (run.is_successful() and run.is_failed())

                # Constraint 3: is_successful() implies is_terminal()
                if run.is_successful():
                    assert run.is_terminal()

                # Constraint 4: is_failed() implies is_terminal()
                if run.is_failed():
                    assert run.is_terminal()
