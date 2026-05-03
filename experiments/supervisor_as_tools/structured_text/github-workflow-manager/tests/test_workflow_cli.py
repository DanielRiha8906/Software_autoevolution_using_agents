import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import sys

from src.cli.workflow_cli import run_cli
from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.services.attempt_service import AttemptService
from src.services.statistics_service import StatisticsService
from src.services.data_portability_service import DataPortabilityService
from src.services.github_fetch_service import GitHubFetchService


def _make_run(run_id: str = "run-1", branch: str = "main", duration: float = 10.0) -> WorkflowRun:
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
        duration_seconds=duration,
    )


@pytest.fixture
def service():
    storage = MagicMock()
    storage.load.return_value = []
    svc = WorkflowRunService(storage)
    return svc


@pytest.fixture
def attempt_service():
    storage = MagicMock()
    storage.load.return_value = []
    svc = AttemptService(storage)
    return svc


@pytest.fixture
def statistics_service(service, attempt_service):
    return StatisticsService(service, attempt_service)


@pytest.fixture
def portability_service():
    return DataPortabilityService()


@pytest.fixture
def github_fetch_service():
    return GitHubFetchService("test-owner", "test-repo")


def test_cli_list_filter_duration_min_max(service, attempt_service, statistics_service, portability_service, github_fetch_service, capsys):
    r1 = _make_run("r1", duration=5.0)
    r2 = _make_run("r2", duration=15.0)
    r3 = _make_run("r3", duration=25.0)

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)

    run_cli(service, attempt_service, statistics_service, portability_service, github_fetch_service, ["list", "--duration-min", "10.0", "--duration-max", "20.0"])
    captured = capsys.readouterr()
    assert "r2" in captured.out
    assert "r1" not in captured.out
    assert "r3" not in captured.out


def test_cli_list_filter_created_after(service, attempt_service, statistics_service, portability_service, github_fetch_service, capsys):
    now = datetime.now(timezone.utc)
    before = now - timedelta(hours=1)
    after = now + timedelta(hours=1)

    r1 = _make_run("r1")
    r1.created_at = before
    r2 = _make_run("r2")
    r2.created_at = after

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)

    # ISO format datetime string
    iso_time = now.isoformat()
    run_cli(service, attempt_service, statistics_service, portability_service, github_fetch_service, ["list", "--created-after", iso_time])
    captured = capsys.readouterr()
    assert "r2" in captured.out
    assert "r1" not in captured.out


def test_cli_list_compound_filters(service, attempt_service, statistics_service, portability_service, github_fetch_service, capsys):
    r1 = _make_run("r1", branch="main", duration=5.0)
    r1.status = WorkflowStatus.COMPLETED

    r2 = _make_run("r2", branch="main", duration=15.0)
    r2.status = WorkflowStatus.COMPLETED

    r3 = _make_run("r3", branch="dev", duration=15.0)
    r3.status = WorkflowStatus.COMPLETED

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)
    service.add_workflow_run(r3)

    run_cli(
        service,
        attempt_service,
        statistics_service,
        portability_service,
        github_fetch_service,
        [
            "list",
            "--branch",
            "main",
            "--duration-min",
            "10.0",
            "--status",
            "completed",
        ],
    )
    captured = capsys.readouterr()
    assert "r2" in captured.out
    assert "r1" not in captured.out
    assert "r3" not in captured.out


def test_cli_list_duration_invalid_range_raises(service, attempt_service, statistics_service, portability_service, github_fetch_service, capsys):
    with pytest.raises(SystemExit) as exc_info:
        run_cli(service, attempt_service, statistics_service, portability_service, github_fetch_service, ["list", "--duration-min", "20.0", "--duration-max", "10.0"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "must be <=" in captured.err


def test_cli_list_duration_negative_min_raises(service, attempt_service, statistics_service, portability_service, github_fetch_service, capsys):
    with pytest.raises(SystemExit) as exc_info:
        run_cli(service, attempt_service, statistics_service, portability_service, github_fetch_service, ["list", "--duration-min", "-1.0"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "non-negative" in captured.err


def test_cli_list_has_attempts_exclusive(service, attempt_service, statistics_service, portability_service, github_fetch_service, capsys):
    with pytest.raises(SystemExit) as exc_info:
        run_cli(
            service,
            attempt_service,
            statistics_service,
            portability_service,
            github_fetch_service,
            ["list", "--has-attempts", "--no-attempts"],
        )
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "cannot be used together" in captured.err


def test_cli_list_created_after_invalid_format(service, attempt_service, statistics_service, portability_service, github_fetch_service, capsys):
    with pytest.raises(SystemExit) as exc_info:
        run_cli(service, attempt_service, statistics_service, portability_service, github_fetch_service, ["list", "--created-after", "invalid-date"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Invalid" in captured.err or "ISO 8601" in captured.err


def test_cli_list_no_runs_found(service, attempt_service, statistics_service, portability_service, github_fetch_service, capsys):
    run_cli(service, attempt_service, statistics_service, portability_service, github_fetch_service, ["list"])
    captured = capsys.readouterr()
    assert "No runs found" in captured.out
