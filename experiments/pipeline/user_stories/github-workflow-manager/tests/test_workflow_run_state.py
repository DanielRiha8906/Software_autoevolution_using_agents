import pytest
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_run(
    status: WorkflowStatus,
    conclusion: WorkflowConclusion = None,
    run_id: str = "run-1",
) -> WorkflowRun:
    """Helper to create a WorkflowRun with given status and conclusion."""
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
        duration_seconds=0.0,
    )


# Group 1: is_running() tests for all running states
def test_is_running_requested():
    run = _make_run(WorkflowStatus.REQUESTED)
    assert run.is_running() is True


def test_is_running_pending():
    run = _make_run(WorkflowStatus.PENDING)
    assert run.is_running() is True


def test_is_running_queued():
    run = _make_run(WorkflowStatus.QUEUED)
    assert run.is_running() is True


def test_is_running_waiting():
    run = _make_run(WorkflowStatus.WAITING)
    assert run.is_running() is True


def test_is_running_in_progress():
    run = _make_run(WorkflowStatus.IN_PROGRESS)
    assert run.is_running() is True


# Group 2: is_terminal() tests for all status values
def test_is_terminal_completed():
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
    assert run.is_terminal() is True


def test_is_terminal_requested():
    run = _make_run(WorkflowStatus.REQUESTED)
    assert run.is_terminal() is False


def test_is_terminal_pending():
    run = _make_run(WorkflowStatus.PENDING)
    assert run.is_terminal() is False


def test_is_terminal_queued():
    run = _make_run(WorkflowStatus.QUEUED)
    assert run.is_terminal() is False


def test_is_terminal_waiting():
    run = _make_run(WorkflowStatus.WAITING)
    assert run.is_terminal() is False


def test_is_terminal_in_progress():
    run = _make_run(WorkflowStatus.IN_PROGRESS)
    assert run.is_terminal() is False


# Group 3: is_successful() and is_failed() tests for all conclusions
def test_is_successful_success():
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
    assert run.is_successful() is True


def test_is_failed_failure():
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE)
    assert run.is_failed() is True


def test_is_failed_timed_out():
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.TIMED_OUT)
    assert run.is_failed() is True


def test_is_cancelled_cancelled():
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED)
    assert run.is_cancelled() is True


# Group 4: Mutual exclusivity - is_terminal() and is_running()
def test_mutual_exclusivity_terminal_and_running_completed():
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
    assert run.is_terminal() is True
    assert run.is_running() is False


def test_mutual_exclusivity_terminal_and_running_running():
    run = _make_run(WorkflowStatus.IN_PROGRESS)
    assert run.is_running() is True
    assert run.is_terminal() is False


# Group 5: Edge cases and non-matching conclusions
def test_non_successful_when_running():
    run = _make_run(WorkflowStatus.IN_PROGRESS)
    assert run.is_successful() is False


def test_non_failed_when_running():
    run = _make_run(WorkflowStatus.IN_PROGRESS)
    assert run.is_failed() is False


def test_non_cancelled_when_running():
    run = _make_run(WorkflowStatus.IN_PROGRESS)
    assert run.is_cancelled() is False


def test_is_cancelled_with_non_cancelled_conclusion():
    run = _make_run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
    assert run.is_cancelled() is False
