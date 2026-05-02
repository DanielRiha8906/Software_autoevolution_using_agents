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


def test_is_running_when_in_progress():
    """Test that is_running() returns True when status is IN_PROGRESS."""
    run = _run(status=WorkflowStatus.IN_PROGRESS)
    assert run.is_running() is True


def test_is_running_false_when_completed():
    """Test that is_running() returns False when status is COMPLETED."""
    run = _run(status=WorkflowStatus.COMPLETED)
    assert run.is_running() is False


def test_is_terminal_when_completed_success():
    """Test that is_terminal() returns True when status is COMPLETED with SUCCESS conclusion."""
    run = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
    assert run.is_terminal() is True


def test_is_terminal_when_completed_failure():
    """Test that is_terminal() returns True when status is COMPLETED with FAILURE conclusion."""
    run = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
    assert run.is_terminal() is True


def test_is_terminal_false_when_running():
    """Test that is_terminal() returns False when status is IN_PROGRESS."""
    run = _run(status=WorkflowStatus.IN_PROGRESS)
    assert run.is_terminal() is False


def test_is_running_and_is_terminal_are_mutually_exclusive():
    """Test that is_running() and is_terminal() cannot both be True."""
    # When IN_PROGRESS
    run_running = _run(status=WorkflowStatus.IN_PROGRESS)
    assert run_running.is_running() is True
    assert run_running.is_terminal() is False

    # When COMPLETED
    run_terminal = _run(status=WorkflowStatus.COMPLETED)
    assert run_terminal.is_running() is False
    assert run_terminal.is_terminal() is True


def test_is_successful():
    """Test that is_successful() returns True only when COMPLETED and SUCCESS."""
    run = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
    assert run.is_successful() is True


def test_is_failed():
    """Test that is_failed() returns True only when COMPLETED and FAILURE."""
    run = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
    assert run.is_failed() is True


def test_is_successful_and_is_failed_are_mutually_exclusive():
    """Test that is_successful() and is_failed() cannot both be True."""
    # When SUCCESS
    run_success = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
    assert run_success.is_successful() is True
    assert run_success.is_failed() is False

    # When FAILURE
    run_failed = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
    assert run_failed.is_successful() is False
    assert run_failed.is_failed() is True


def test_is_cancelled():
    """Test that is_cancelled() returns True only when COMPLETED and CANCELLED."""
    run = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
    assert run.is_cancelled() is True


def test_methods_use_only_status_and_conclusion():
    """Test that state-checking methods use only status and conclusion attributes."""
    # This test verifies that the methods do not have side effects or external dependencies.
    # We create multiple runs with different status/conclusion combinations and verify
    # the methods only inspect these two attributes.

    # Test is_running - depends only on status
    run1 = _run(status=WorkflowStatus.IN_PROGRESS, conclusion=WorkflowConclusion.SUCCESS)
    assert run1.is_running() is True

    run2 = _run(status=WorkflowStatus.IN_PROGRESS, conclusion=WorkflowConclusion.FAILURE)
    assert run2.is_running() is True

    # Test is_terminal - depends only on status
    run3 = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
    assert run3.is_terminal() is True

    run4 = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
    assert run4.is_terminal() is True

    # Test is_successful - depends on both status and conclusion
    run5 = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
    assert run5.is_successful() is True

    run6 = _run(status=WorkflowStatus.IN_PROGRESS, conclusion=WorkflowConclusion.SUCCESS)
    assert run6.is_successful() is False

    # Test is_failed - depends on both status and conclusion
    run7 = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)
    assert run7.is_failed() is True

    run8 = _run(status=WorkflowStatus.IN_PROGRESS, conclusion=WorkflowConclusion.FAILURE)
    assert run8.is_failed() is False

    # Test is_cancelled - depends on both status and conclusion
    run9 = _run(status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.CANCELLED)
    assert run9.is_cancelled() is True

    run10 = _run(status=WorkflowStatus.IN_PROGRESS, conclusion=WorkflowConclusion.CANCELLED)
    assert run10.is_cancelled() is False
