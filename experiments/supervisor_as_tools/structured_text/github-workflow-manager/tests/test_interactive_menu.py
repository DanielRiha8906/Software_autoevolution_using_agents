import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import io
import sys

from src.cli.interactive_menu import (
    _prompt_datetime,
    _filter_by_duration_interactive,
    _filter_by_created_interactive,
    _advanced_filter_menu,
)
from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.services.attempt_service import AttemptService
from src.services.statistics_service import StatisticsService
from src.services.data_portability_service import DataPortabilityService


def _make_run(run_id: str = "run-1", duration: float = 10.0) -> WorkflowRun:
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch="main",
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


def test_prompt_datetime_valid_input():
    """Test _prompt_datetime with valid ISO 8601 input."""
    iso_string = "2026-05-03T12:00:00"
    with patch("builtins.input", return_value=iso_string):
        result = _prompt_datetime("Test date")
    assert result == datetime.fromisoformat(iso_string)


def test_prompt_datetime_valid_date_only():
    """Test _prompt_datetime with date-only input."""
    iso_string = "2026-05-03"
    with patch("builtins.input", return_value=iso_string):
        result = _prompt_datetime("Test date")
    assert result == datetime.fromisoformat(iso_string)


def test_prompt_datetime_blank_input():
    """Test _prompt_datetime with blank input returns None."""
    with patch("builtins.input", return_value=""):
        result = _prompt_datetime("Test date")
    assert result is None


def test_prompt_datetime_invalid_input_then_valid(capsys):
    """Test _prompt_datetime re-prompts on invalid input."""
    iso_string = "2026-05-03T12:00:00"
    with patch("builtins.input", side_effect=["invalid-date", iso_string]):
        result = _prompt_datetime("Test date")
    assert result == datetime.fromisoformat(iso_string)
    captured = capsys.readouterr()
    assert "Invalid format" in captured.out


def test_filter_by_duration_interactive(service, attempt_service, statistics_service, portability_service, capsys):
    """Test _filter_by_duration_interactive calls service correctly."""
    r1 = _make_run("r1", duration=5.0)
    r2 = _make_run("r2", duration=15.0)
    service.add_workflow_run(r1)
    service.add_workflow_run(r2)

    # Input: min=10.0, max=blank (unlimited)
    with patch("builtins.input", side_effect=["10.0", ""]):
        _filter_by_duration_interactive(service, attempt_service, statistics_service, portability_service)

    captured = capsys.readouterr()
    assert "r2" in captured.out
    assert "1 matching run(s)" in captured.out


def test_filter_by_created_interactive(service, attempt_service, statistics_service, portability_service, capsys):
    """Test _filter_by_created_interactive calls service correctly."""
    now = datetime.now(timezone.utc)
    before = now - timedelta(hours=1)
    after = now + timedelta(hours=1)

    r1 = _make_run("r1")
    r1.created_at = before
    r2 = _make_run("r2")
    r2.created_at = after

    service.add_workflow_run(r1)
    service.add_workflow_run(r2)

    iso_now = now.isoformat()
    # Input: created_after=now, created_before=blank
    with patch("builtins.input", side_effect=[iso_now, ""]):
        _filter_by_created_interactive(service, attempt_service, statistics_service, portability_service)

    captured = capsys.readouterr()
    assert "r2" in captured.out


def test_advanced_filter_menu_navigation(service, attempt_service, statistics_service, portability_service, capsys):
    """Test _advanced_filter_menu navigates correctly."""
    r1 = _make_run("r1", duration=5.0)
    service.add_workflow_run(r1)

    # Simulate: choose "Back to main menu" immediately
    with patch("builtins.input", side_effect=["6"]):
        _advanced_filter_menu(service, attempt_service, statistics_service, portability_service)

    # Should return without error
    captured = capsys.readouterr()
    # Just verify it didn't crash
    assert True


def test_filter_by_duration_interactive_with_invalid_max(service, attempt_service, statistics_service, portability_service, capsys):
    """Test _filter_by_duration_interactive handles invalid max gracefully."""
    r1 = _make_run("r1", duration=5.0)
    service.add_workflow_run(r1)

    # Input: min=10.0, max=invalid
    with patch("builtins.input", side_effect=["10.0", "not-a-number"]):
        _filter_by_duration_interactive(service, attempt_service, statistics_service, portability_service)

    captured = capsys.readouterr()
    assert "Invalid float" in captured.out


def test_filter_by_duration_interactive_no_matching_runs(service, attempt_service, statistics_service, portability_service, capsys):
    """Test _filter_by_duration_interactive with no matching runs."""
    r1 = _make_run("r1", duration=5.0)
    service.add_workflow_run(r1)

    # Input: min=100.0, max=blank (no matches)
    with patch("builtins.input", side_effect=["100.0", ""]):
        _filter_by_duration_interactive(service, attempt_service, statistics_service, portability_service)

    captured = capsys.readouterr()
    assert "No matching runs" in captured.out
