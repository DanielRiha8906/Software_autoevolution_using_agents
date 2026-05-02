import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.cli.interactive_menu import _fmt_run, _add_run


def _make_run(
    run_id: str = "run-1",
    branch: str = "main",
    duration_seconds: float = 0.0,
) -> WorkflowRun:
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch=branch,
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def mock_service():
    storage = MagicMock()
    storage.load.return_value = []
    svc = WorkflowRunService(storage)
    return svc


def test_fmt_run_includes_duration_seconds():
    """Verify _fmt_run includes duration_seconds in output."""
    run = _make_run("run-1", "main", duration_seconds=78.9)
    output = _fmt_run(run)
    assert "duration_seconds: 78.9" in output


def test_fmt_run_duration_zero():
    """Verify _fmt_run formats zero duration correctly."""
    run = _make_run("run-1", "main", duration_seconds=0.0)
    output = _fmt_run(run)
    assert "duration_seconds: 0.0" in output


@patch("builtins.input")
def test_add_run_with_duration_input(mock_input, mock_service):
    """Test _add_run with duration input from user."""
    mock_input.side_effect = [
        "TestWorkflow",  # workflow name
        "main",           # branch
        "1",              # status choice (first option)
        "0",              # conclusion choice (skip)
        "",               # run_number (skip)
        "",               # commit_sha (skip)
        "50.25",          # duration_seconds
    ]

    _add_run(mock_service)

    runs = mock_service.list_runs()
    assert len(runs) == 1
    assert runs[0].duration_seconds == 50.25


@patch("builtins.input")
def test_add_run_with_default_duration(mock_input, mock_service):
    """Test _add_run with default duration (0.0) when pressing Enter."""
    mock_input.side_effect = [
        "TestWorkflow",  # workflow name
        "main",           # branch
        "1",              # status choice (first option)
        "0",              # conclusion choice (skip)
        "",               # run_number (skip)
        "",               # commit_sha (skip)
        "",               # duration_seconds (empty = use default)
    ]

    _add_run(mock_service)

    runs = mock_service.list_runs()
    assert len(runs) == 1
    assert runs[0].duration_seconds == 0.0


@patch("builtins.input")
def test_add_run_with_float_duration(mock_input, mock_service):
    """Test _add_run with float duration input."""
    mock_input.side_effect = [
        "TestWorkflow",  # workflow name
        "develop",        # branch
        "2",              # status choice
        "0",              # conclusion choice (skip)
        "123",            # run_number
        "abc789",         # commit_sha
        "100.5678",       # duration_seconds
    ]

    _add_run(mock_service)

    runs = mock_service.list_runs()
    assert len(runs) == 1
    assert runs[0].duration_seconds == 100.5678
