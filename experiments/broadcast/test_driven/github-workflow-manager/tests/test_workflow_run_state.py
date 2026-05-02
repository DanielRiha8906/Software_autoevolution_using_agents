import pytest
from datetime import datetime, timezone
from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _run(**kwargs):
    defaults = dict(
        id="run-1", workflow_name="CI", branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime.now(timezone.utc),
        updated_at=None, run_number=1, commit_sha=None,
    )
    defaults.update(kwargs)
    return WorkflowRun(**defaults)


# is_running() tests
def test_is_running_true_when_in_progress():
    assert _run(status=WorkflowStatus.IN_PROGRESS).is_running()


def test_is_running_false_when_completed():
    assert not _run(status=WorkflowStatus.COMPLETED).is_running()


def test_is_running_false_when_queued():
    assert not _run(status=WorkflowStatus.QUEUED).is_running()


# is_terminal() tests
def test_is_terminal_true_when_completed():
    assert _run(status=WorkflowStatus.COMPLETED).is_terminal()


def test_is_terminal_false_when_in_progress():
    assert not _run(status=WorkflowStatus.IN_PROGRESS).is_terminal()


def test_is_terminal_false_when_queued():
    assert not _run(status=WorkflowStatus.QUEUED).is_terminal()


# is_successful() tests
def test_is_successful_true_when_completed_with_success():
    assert _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS).is_successful()


def test_is_successful_false_when_completed_with_failure():
    assert not _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE).is_successful()


def test_is_successful_false_when_completed_with_cancelled():
    assert not _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED).is_successful()


def test_is_successful_false_when_in_progress():
    assert not _run(status=WorkflowStatus.IN_PROGRESS, conclusion=WorkflowConclusion.SUCCESS).is_successful()


# is_failed() tests
def test_is_failed_true_when_completed_with_failure():
    assert _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE).is_failed()


def test_is_failed_false_when_completed_with_success():
    assert not _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS).is_failed()


def test_is_failed_false_when_completed_with_cancelled():
    assert not _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED).is_failed()


def test_is_failed_false_when_in_progress():
    assert not _run(status=WorkflowStatus.IN_PROGRESS, conclusion=WorkflowConclusion.FAILURE).is_failed()


# is_cancelled() tests
def test_is_cancelled_true_when_completed_with_cancelled():
    assert _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED).is_cancelled()


def test_is_cancelled_false_when_completed_with_success():
    assert not _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS).is_cancelled()


def test_is_cancelled_false_when_completed_with_failure():
    assert not _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE).is_cancelled()


def test_is_cancelled_false_when_in_progress():
    assert not _run(status=WorkflowStatus.IN_PROGRESS, conclusion=WorkflowConclusion.CANCELLED).is_cancelled()


# Mutual exclusivity tests
def test_is_terminal_and_is_running_mutually_exclusive():
    """is_terminal() and is_running() must be mutually exclusive"""
    run_completed = _run(status=WorkflowStatus.COMPLETED)
    run_in_progress = _run(status=WorkflowStatus.IN_PROGRESS)

    # When terminal, not running
    assert run_completed.is_terminal()
    assert not run_completed.is_running()

    # When running, not terminal
    assert run_in_progress.is_running()
    assert not run_in_progress.is_terminal()


def test_is_successful_and_is_failed_mutually_exclusive():
    """is_successful() and is_failed() must be mutually exclusive"""
    run_success = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
    run_failed = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)

    # When successful, not failed
    assert run_success.is_successful()
    assert not run_success.is_failed()

    # When failed, not successful
    assert run_failed.is_failed()
    assert not run_failed.is_successful()
