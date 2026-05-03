import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_run(status: WorkflowStatus,
              conclusion: None | WorkflowConclusion = None) -> WorkflowRun:
    """Helper to create a WorkflowRun with given status and conclusion."""
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
        duration_seconds=0.0,
    )


# ============================================================================
# Running State Tests (5 tests)
# ============================================================================

def test_is_queued():
    """Test QUEUED status: running but not terminal."""
    run = _make_run(WorkflowStatus.QUEUED)
    assert run.is_terminal() is False
    assert run.is_running() is True
    assert run.is_successful() is False
    assert run.is_failed() is False
    assert run.is_cancelled() is False


def test_is_in_progress():
    """Test IN_PROGRESS status: running but not terminal."""
    run = _make_run(WorkflowStatus.IN_PROGRESS)
    assert run.is_terminal() is False
    assert run.is_running() is True
    assert run.is_successful() is False
    assert run.is_failed() is False
    assert run.is_cancelled() is False


def test_is_waiting():
    """Test WAITING status: running but not terminal."""
    run = _make_run(WorkflowStatus.WAITING)
    assert run.is_terminal() is False
    assert run.is_running() is True
    assert run.is_successful() is False
    assert run.is_failed() is False
    assert run.is_cancelled() is False


def test_is_requested():
    """Test REQUESTED status: running but not terminal."""
    run = _make_run(WorkflowStatus.REQUESTED)
    assert run.is_terminal() is False
    assert run.is_running() is True
    assert run.is_successful() is False
    assert run.is_failed() is False
    assert run.is_cancelled() is False


def test_is_pending():
    """Test PENDING status: running but not terminal."""
    run = _make_run(WorkflowStatus.PENDING)
    assert run.is_terminal() is False
    assert run.is_running() is True
    assert run.is_successful() is False
    assert run.is_failed() is False
    assert run.is_cancelled() is False


# ============================================================================
# Successful State Test (1 test)
# ============================================================================

def test_is_successful():
    """Test COMPLETED + SUCCESS: terminal and successful."""
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
    assert run.is_terminal() is True
    assert run.is_running() is False
    assert run.is_successful() is True
    assert run.is_failed() is False
    assert run.is_cancelled() is False


# ============================================================================
# Failed State Tests (3 tests)
# ============================================================================

def test_is_failed_with_failure_conclusion():
    """Test COMPLETED + FAILURE: terminal and failed."""
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
    assert run.is_terminal() is True
    assert run.is_running() is False
    assert run.is_successful() is False
    assert run.is_failed() is True
    assert run.is_cancelled() is False


def test_is_failed_with_timed_out_conclusion():
    """Test COMPLETED + TIMED_OUT: terminal and failed."""
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
    assert run.is_terminal() is True
    assert run.is_running() is False
    assert run.is_successful() is False
    assert run.is_failed() is True
    assert run.is_cancelled() is False


def test_is_failed_with_action_required_conclusion():
    """Test COMPLETED + ACTION_REQUIRED: terminal and failed."""
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.ACTION_REQUIRED)
    assert run.is_terminal() is True
    assert run.is_running() is False
    assert run.is_successful() is False
    assert run.is_failed() is True
    assert run.is_cancelled() is False


# ============================================================================
# Other Terminal State Tests (4 tests)
# ============================================================================

def test_is_cancelled():
    """Test COMPLETED + CANCELLED: terminal and cancelled."""
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
    assert run.is_terminal() is True
    assert run.is_running() is False
    assert run.is_successful() is False
    assert run.is_failed() is False
    assert run.is_cancelled() is True


def test_is_skipped():
    """Test COMPLETED + SKIPPED: terminal, neither successful nor failed."""
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SKIPPED)
    assert run.is_terminal() is True
    assert run.is_running() is False
    assert run.is_successful() is False
    assert run.is_failed() is False
    assert run.is_cancelled() is False


def test_is_neutral():
    """Test COMPLETED + NEUTRAL: terminal, neither successful nor failed."""
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.NEUTRAL)
    assert run.is_terminal() is True
    assert run.is_running() is False
    assert run.is_successful() is False
    assert run.is_failed() is False
    assert run.is_cancelled() is False


def test_is_stale():
    """Test COMPLETED + STALE: terminal, neither successful nor failed."""
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.STALE)
    assert run.is_terminal() is True
    assert run.is_running() is False
    assert run.is_successful() is False
    assert run.is_failed() is False
    assert run.is_cancelled() is False


# ============================================================================
# Mutual Exclusivity Constraint Tests (2 tests)
# ============================================================================

def test_terminal_and_running_mutually_exclusive():
    """Test that is_terminal and is_running are mutually exclusive."""
    # Test all running states
    for status in [WorkflowStatus.QUEUED, WorkflowStatus.IN_PROGRESS,
                   WorkflowStatus.WAITING, WorkflowStatus.REQUESTED,
                   WorkflowStatus.PENDING]:
        run = _make_run(status)
        assert run.is_terminal() is not run.is_running(), \
            f"is_terminal and is_running should be opposite for {status}"
        assert run.is_terminal() is False
        assert run.is_running() is True

    # Test all terminal states
    conclusions = [WorkflowConclusion.SUCCESS, WorkflowConclusion.FAILURE,
                   WorkflowConclusion.CANCELLED, WorkflowConclusion.SKIPPED,
                   WorkflowConclusion.TIMED_OUT, WorkflowConclusion.ACTION_REQUIRED,
                   WorkflowConclusion.NEUTRAL, WorkflowConclusion.STALE]
    for conclusion in conclusions:
        run = _make_run(WorkflowStatus.COMPLETED, conclusion)
        assert run.is_terminal() is not run.is_running(), \
            f"is_terminal and is_running should be opposite for COMPLETED + {conclusion}"
        assert run.is_terminal() is True
        assert run.is_running() is False


def test_successful_and_failed_mutually_exclusive():
    """Test that is_successful and is_failed can never both be True."""
    # Generate all possible state combinations
    statuses = [WorkflowStatus.QUEUED, WorkflowStatus.IN_PROGRESS,
                WorkflowStatus.COMPLETED, WorkflowStatus.WAITING,
                WorkflowStatus.REQUESTED, WorkflowStatus.PENDING]
    conclusions = [None, WorkflowConclusion.SUCCESS, WorkflowConclusion.FAILURE,
                   WorkflowConclusion.CANCELLED, WorkflowConclusion.SKIPPED,
                   WorkflowConclusion.TIMED_OUT, WorkflowConclusion.ACTION_REQUIRED,
                   WorkflowConclusion.NEUTRAL, WorkflowConclusion.STALE]

    for status in statuses:
        for conclusion in conclusions:
            # Skip invalid combinations (non-COMPLETED status with conclusion)
            if status != WorkflowStatus.COMPLETED and conclusion is not None:
                continue
            if status == WorkflowStatus.COMPLETED and conclusion is None:
                continue

            run = _make_run(status, conclusion)
            # Both cannot be True
            assert not (run.is_successful() and run.is_failed()), \
                f"is_successful and is_failed should not both be True for {status} + {conclusion}"
