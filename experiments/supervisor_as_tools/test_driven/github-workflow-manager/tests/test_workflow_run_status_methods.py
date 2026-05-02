import pytest
from datetime import datetime, timezone
from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _run(status, conclusion=None):
    return WorkflowRun(
        id="r1", workflow_name="CI", branch="main",
        status=status, conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None, run_number=None, commit_sha=None,
    )


def test_is_running_when_in_progress():
    assert _run(WorkflowStatus.IN_PROGRESS).is_running() is True


def test_is_running_false_when_completed():
    assert _run(WorkflowStatus.COMPLETED).is_running() is False


def test_is_terminal_when_completed_success():
    assert _run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS).is_terminal() is True


def test_is_terminal_when_completed_failure():
    assert _run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE).is_terminal() is True


def test_is_terminal_false_when_running():
    assert _run(WorkflowStatus.IN_PROGRESS).is_terminal() is False


def test_is_running_and_is_terminal_are_mutually_exclusive():
    run = _run(WorkflowStatus.IN_PROGRESS)
    assert not (run.is_running() and run.is_terminal())


def test_is_successful():
    assert _run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS).is_successful() is True


def test_is_failed():
    assert _run(WorkflowStatus.COMPLETED, WorkflowConclusion.FAILURE).is_failed() is True


def test_is_successful_and_is_failed_are_mutually_exclusive():
    run = _run(WorkflowStatus.COMPLETED, WorkflowConclusion.SUCCESS)
    assert not (run.is_successful() and run.is_failed())


def test_is_cancelled():
    assert _run(WorkflowStatus.COMPLETED, WorkflowConclusion.CANCELLED).is_cancelled() is True


def test_methods_use_only_status_and_conclusion():
    import inspect
    source = inspect.getsource(WorkflowRun)
    assert "requests" not in source
    assert "open(" not in source
