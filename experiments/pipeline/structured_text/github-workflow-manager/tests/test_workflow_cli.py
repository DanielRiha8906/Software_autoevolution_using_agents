import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.cli.workflow_cli import run_cli, _fmt_run


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
    run = _make_run("run-1", "main", duration_seconds=42.5)
    output = _fmt_run(run)
    assert "duration_seconds: 42.5" in output


def test_fmt_run_duration_zero():
    """Verify _fmt_run formats zero duration correctly."""
    run = _make_run("run-1", "main", duration_seconds=0.0)
    output = _fmt_run(run)
    assert "duration_seconds: 0.0" in output


def test_cli_add_with_duration_seconds(mock_service, capsys):
    """Test CLI add command with --duration-seconds flag."""
    args = [
        "add",
        "--name", "TestWorkflow",
        "--branch", "main",
        "--status", "completed",
        "--conclusion", "success",
        "--duration-seconds", "123.45",
    ]
    run_cli(mock_service, args=args)
    captured = capsys.readouterr()
    assert "Added run" in captured.out

    # Verify the run was added with the correct duration
    runs = mock_service.list_runs()
    assert len(runs) == 1
    assert runs[0].duration_seconds == 123.45


def test_cli_add_without_duration_seconds_defaults(mock_service, capsys):
    """Test CLI add command without --duration-seconds defaults to 0.0."""
    args = [
        "add",
        "--name", "TestWorkflow",
        "--branch", "main",
        "--status", "completed",
    ]
    run_cli(mock_service, args=args)
    captured = capsys.readouterr()
    assert "Added run" in captured.out

    runs = mock_service.list_runs()
    assert len(runs) == 1
    assert runs[0].duration_seconds == 0.0


def test_cli_add_duration_seconds_float(mock_service, capsys):
    """Test CLI add command with float duration_seconds value."""
    args = [
        "add",
        "--name", "TestWorkflow",
        "--branch", "dev",
        "--status", "in_progress",
        "--duration-seconds", "45.6789",
    ]
    run_cli(mock_service, args=args)
    captured = capsys.readouterr()
    assert "Added run" in captured.out

    runs = mock_service.list_runs()
    assert len(runs) == 1
    assert runs[0].duration_seconds == 45.6789


def test_cli_list_shows_duration_seconds(mock_service, capsys):
    """Test CLI list command includes duration_seconds in output."""
    run = _make_run("run-1", "main", duration_seconds=99.99)
    mock_service.add_workflow_run(run)

    args = ["list"]
    run_cli(mock_service, args=args)
    captured = capsys.readouterr()
    assert "duration_seconds: 99.99" in captured.out


def test_cli_detail_shows_duration_seconds(mock_service, capsys):
    """Test CLI detail command includes duration_seconds in output."""
    run = _make_run("run-detail", "main", duration_seconds=55.5)
    mock_service.add_workflow_run(run)

    args = ["detail", "run-detail"]
    run_cli(mock_service, args=args)
    captured = capsys.readouterr()
    assert "duration_seconds: 55.5" in captured.out
