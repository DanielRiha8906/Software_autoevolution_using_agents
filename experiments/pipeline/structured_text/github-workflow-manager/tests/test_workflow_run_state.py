"""
Comprehensive tests for WorkflowRun state query methods.

Tests all state combinations and verifies mutual exclusivity invariants.
"""
from datetime import datetime

import pytest

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def create_run(
    status: WorkflowStatus,
    conclusion: WorkflowConclusion | None = None,
) -> WorkflowRun:
    """Helper to create a WorkflowRun with specified state."""
    return WorkflowRun(
        id="test-run-001",
        workflow_name="test-workflow",
        branch="main",
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        run_number=42,
        commit_sha="abc123",
        duration_seconds=10.5,
    )


# ============================================================================
# is_running() Tests
# ============================================================================


class TestIsRunning:
    """Tests for is_running() method."""

    @pytest.mark.parametrize(
        "status",
        [
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
        ],
    )
    def test_is_running_true(self, status: WorkflowStatus):
        """is_running() returns True for active execution statuses."""
        run = create_run(status=status, conclusion=None)
        assert run.is_running() is True

    @pytest.mark.parametrize(
        "status",
        [
            WorkflowStatus.QUEUED,
            WorkflowStatus.PENDING,
        ],
    )
    def test_is_running_false_non_terminal_not_executing(
        self, status: WorkflowStatus
    ):
        """is_running() returns False for QUEUED and PENDING statuses."""
        run = create_run(status=status, conclusion=None)
        assert run.is_running() is False

    @pytest.mark.parametrize(
        "conclusion",
        [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.CANCELLED,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
        ],
    )
    def test_is_running_false_completed(self, conclusion: WorkflowConclusion):
        """is_running() returns False for COMPLETED status."""
        run = create_run(status=WorkflowStatus.COMPLETED, conclusion=conclusion)
        assert run.is_running() is False


# ============================================================================
# is_terminal() Tests
# ============================================================================


class TestIsTerminal:
    """Tests for is_terminal() method."""

    @pytest.mark.parametrize(
        "conclusion",
        [
            WorkflowConclusion.SUCCESS,
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.CANCELLED,
            WorkflowConclusion.SKIPPED,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
            WorkflowConclusion.NEUTRAL,
            WorkflowConclusion.STALE,
        ],
    )
    def test_is_terminal_true_completed(self, conclusion: WorkflowConclusion):
        """is_terminal() returns True for any COMPLETED status."""
        run = create_run(status=WorkflowStatus.COMPLETED, conclusion=conclusion)
        assert run.is_terminal() is True

    @pytest.mark.parametrize(
        "status",
        [
            WorkflowStatus.QUEUED,
            WorkflowStatus.PENDING,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
        ],
    )
    def test_is_terminal_false_not_completed(self, status: WorkflowStatus):
        """is_terminal() returns False for non-COMPLETED statuses."""
        run = create_run(status=status, conclusion=None)
        assert run.is_terminal() is False


# ============================================================================
# is_successful() Tests
# ============================================================================


class TestIsSuccessful:
    """Tests for is_successful() method."""

    def test_is_successful_true(self):
        """is_successful() returns True only for COMPLETED + SUCCESS."""
        run = create_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
        )
        assert run.is_successful() is True

    @pytest.mark.parametrize(
        "status,conclusion",
        [
            (WorkflowStatus.QUEUED, None),
            (WorkflowStatus.PENDING, None),
            (WorkflowStatus.IN_PROGRESS, None),
            (WorkflowStatus.WAITING, None),
            (WorkflowStatus.REQUESTED, None),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE),
        ],
    )
    def test_is_successful_false(
        self, status: WorkflowStatus, conclusion: WorkflowConclusion | None
    ):
        """is_successful() returns False for all other state combinations."""
        run = create_run(status=status, conclusion=conclusion)
        assert run.is_successful() is False


# ============================================================================
# is_failed() Tests
# ============================================================================


class TestIsFailed:
    """Tests for is_failed() method."""

    @pytest.mark.parametrize(
        "conclusion",
        [
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
        ],
    )
    def test_is_failed_true(self, conclusion: WorkflowConclusion):
        """is_failed() returns True for failure-related conclusions."""
        run = create_run(status=WorkflowStatus.COMPLETED, conclusion=conclusion)
        assert run.is_failed() is True

    @pytest.mark.parametrize(
        "status,conclusion",
        [
            (WorkflowStatus.QUEUED, None),
            (WorkflowStatus.PENDING, None),
            (WorkflowStatus.IN_PROGRESS, None),
            (WorkflowStatus.WAITING, None),
            (WorkflowStatus.REQUESTED, None),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE),
        ],
    )
    def test_is_failed_false(
        self, status: WorkflowStatus, conclusion: WorkflowConclusion | None
    ):
        """is_failed() returns False for all other state combinations."""
        run = create_run(status=status, conclusion=conclusion)
        assert run.is_failed() is False


# ============================================================================
# is_cancelled() Tests
# ============================================================================


class TestIsCancelled:
    """Tests for is_cancelled() method."""

    def test_is_cancelled_true(self):
        """is_cancelled() returns True only for COMPLETED + CANCELLED."""
        run = create_run(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.CANCELLED,
        )
        assert run.is_cancelled() is True

    @pytest.mark.parametrize(
        "status,conclusion",
        [
            (WorkflowStatus.QUEUED, None),
            (WorkflowStatus.PENDING, None),
            (WorkflowStatus.IN_PROGRESS, None),
            (WorkflowStatus.WAITING, None),
            (WorkflowStatus.REQUESTED, None),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE),
        ],
    )
    def test_is_cancelled_false(
        self, status: WorkflowStatus, conclusion: WorkflowConclusion | None
    ):
        """is_cancelled() returns False for all other state combinations."""
        run = create_run(status=status, conclusion=conclusion)
        assert run.is_cancelled() is False


# ============================================================================
# Mutual Exclusivity Tests
# ============================================================================


class TestMutualExclusivity:
    """Tests verifying mutual exclusivity invariants."""

    @pytest.mark.parametrize(
        "status,conclusion",
        [
            (WorkflowStatus.QUEUED, None),
            (WorkflowStatus.PENDING, None),
            (WorkflowStatus.IN_PROGRESS, None),
            (WorkflowStatus.WAITING, None),
            (WorkflowStatus.REQUESTED, None),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE),
        ],
    )
    def test_running_and_terminal_mutually_exclusive(
        self, status: WorkflowStatus, conclusion: WorkflowConclusion | None
    ):
        """is_running() and is_terminal() are always mutually exclusive."""
        run = create_run(status=status, conclusion=conclusion)
        assert (run.is_running() and run.is_terminal()) is False

    @pytest.mark.parametrize(
        "status,conclusion",
        [
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE),
        ],
    )
    def test_successful_and_failed_mutually_exclusive(
        self, status: WorkflowStatus, conclusion: WorkflowConclusion
    ):
        """is_successful() and is_failed() are always mutually exclusive."""
        run = create_run(status=status, conclusion=conclusion)
        assert (run.is_successful() and run.is_failed()) is False

    @pytest.mark.parametrize(
        "status,conclusion",
        [
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE),
        ],
    )
    def test_successful_and_cancelled_mutually_exclusive(
        self, status: WorkflowStatus, conclusion: WorkflowConclusion
    ):
        """is_successful() and is_cancelled() are always mutually exclusive."""
        run = create_run(status=status, conclusion=conclusion)
        assert (run.is_successful() and run.is_cancelled()) is False

    @pytest.mark.parametrize(
        "status,conclusion",
        [
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL),
            (WorkflowStatus.COMPLETED, WorkflowConclusion.STALE),
        ],
    )
    def test_failed_and_cancelled_mutually_exclusive(
        self, status: WorkflowStatus, conclusion: WorkflowConclusion
    ):
        """is_failed() and is_cancelled() are always mutually exclusive."""
        run = create_run(status=status, conclusion=conclusion)
        assert (run.is_failed() and run.is_cancelled()) is False
