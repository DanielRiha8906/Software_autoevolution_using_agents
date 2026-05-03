"""Tests for CLI filtering capabilities."""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import MagicMock, patch
from io import StringIO

from src.models.workflow_run import WorkflowRun
from src.models.workflow_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.services.workflow_attempt_service import WorkflowAttemptService
from src.cli.workflow_cli import run_cli


def _make_run(
    run_id: str = "run-1",
    branch: str = "main",
    duration_seconds: float = 0.0,
    created_at: datetime = None,
) -> WorkflowRun:
    if created_at is None:
        created_at = datetime(2026, 5, 3, 10, 0, 0, tzinfo=ZoneInfo("UTC"))
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch=branch,
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=created_at,
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=duration_seconds,
    )


def _make_attempt(
    attempt_id: str = "attempt-1",
    run_id: str = "run-1",
    attempt_number: int = 1,
    duration_seconds: float = 0.0,
    started_at: datetime = None,
) -> WorkflowRunAttempt:
    if started_at is None:
        started_at = datetime(2026, 5, 3, 10, 0, 0, tzinfo=ZoneInfo("UTC"))
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        started_at=started_at,
        completed_at=None,
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def run_service():
    storage = MagicMock()
    storage.load.return_value = [
        _make_run("run-1", "main", 10.0),
        _make_run("run-2", "main", 20.0),
        _make_run("run-3", "develop", 30.0),
    ]
    return WorkflowRunService(storage)


@pytest.fixture
def attempt_service():
    storage = MagicMock()
    storage.load.return_value = [
        _make_attempt("attempt-1", "run-1", 1, 10.0),
        _make_attempt("attempt-2", "run-2", 1, 20.0),
    ]
    return WorkflowAttemptService(storage)


class TestCliListWithDurationFilters:
    """Test CLI list command with duration filters."""

    def test_list_with_duration_min(self, run_service, capsys):
        """Test CLI list with --duration-min."""
        run_cli(run_service, args=["list", "--duration-min", "15.0"])
        captured = capsys.readouterr()
        assert "run-2" in captured.out
        assert "run-3" in captured.out

    def test_list_with_duration_max(self, run_service, capsys):
        """Test CLI list with --duration-max."""
        run_cli(run_service, args=["list", "--duration-max", "15.0"])
        captured = capsys.readouterr()
        assert "run-1" in captured.out

    def test_list_with_duration_range(self, run_service, capsys):
        """Test CLI list with both duration bounds."""
        run_cli(run_service, args=["list", "--duration-min", "15.0", "--duration-max", "25.0"])
        captured = capsys.readouterr()
        assert "run-2" in captured.out
        assert "run-3" not in captured.out

    def test_list_no_results_for_duration(self, run_service, capsys):
        """Test CLI list with duration filter returning no results."""
        run_cli(run_service, args=["list", "--duration-min", "100.0"])
        captured = capsys.readouterr()
        assert "No runs found" in captured.out


class TestCliListWithTimestampFilters:
    """Test CLI list command with timestamp filters."""

    def test_list_with_created_after(self, run_service, capsys):
        """Test CLI list with --created-after."""
        run_cli(run_service, args=["list", "--created-after", "2026-05-03T09:00:00"])
        captured = capsys.readouterr()
        # All runs were created at 2026-05-03T10:00:00, so all should be included
        assert "run-1" in captured.out

    def test_list_with_created_before(self, run_service, capsys):
        """Test CLI list with --created-before."""
        run_cli(run_service, args=["list", "--created-before", "2026-05-03T11:00:00"])
        captured = capsys.readouterr()
        assert "run-1" in captured.out

    def test_list_with_created_range(self, run_service, capsys):
        """Test CLI list with created range."""
        run_cli(run_service, args=[
            "list",
            "--created-after", "2026-05-03T09:00:00",
            "--created-before", "2026-05-03T11:00:00",
        ])
        captured = capsys.readouterr()
        assert "run-1" in captured.out

    def test_list_no_results_for_timestamp(self, run_service, capsys):
        """Test CLI list with timestamp filter returning no results."""
        run_cli(run_service, args=["list", "--created-after", "2026-05-04T10:00:00"])
        captured = capsys.readouterr()
        assert "No runs found" in captured.out


class TestCliListWithAttemptFilters:
    """Test CLI list with --with-attempts and --without-attempts."""

    def test_list_with_attempts(self, run_service, attempt_service, capsys):
        """Test CLI list with --with-attempts flag."""
        run_cli(run_service, attempt_service, args=["list", "--with-attempts"])
        captured = capsys.readouterr()
        # Only run-1 and run-2 have attempts
        assert "run-1" in captured.out or "run-2" in captured.out

    def test_list_without_attempts(self, run_service, attempt_service, capsys):
        """Test CLI list with --without-attempts flag."""
        run_cli(run_service, attempt_service, args=["list", "--without-attempts"])
        captured = capsys.readouterr()
        # run-3 has no attempts
        assert "run-3" in captured.out

    def test_list_conflicting_attempt_flags_errors(self, run_service, attempt_service):
        """Test CLI list with both --with-attempts and --without-attempts errors."""
        with pytest.raises(SystemExit) as exc_info:
            run_cli(run_service, attempt_service, args=["list", "--with-attempts", "--without-attempts"])
        assert exc_info.value.code == 1


class TestCliListWithTimezone:
    """Test CLI list with timezone support."""

    def test_list_with_timezone_utc(self, run_service, capsys):
        """Test CLI list with UTC timezone."""
        run_cli(run_service, args=["list", "--created-after", "2026-05-03T10:00:00", "--timezone", "UTC"])
        captured = capsys.readouterr()
        assert "run-1" in captured.out

    def test_list_with_timezone_paris_cest(self, run_service, capsys):
        """Test CLI list with Europe/Paris timezone (CEST)."""
        # 2026-05-03T12:00:00 in CEST (UTC+2) = 2026-05-03T10:00:00 in UTC
        run_cli(run_service, args=[
            "list",
            "--created-after", "2026-05-03T12:00:00",
            "--timezone", "Europe/Paris",
        ])
        captured = capsys.readouterr()
        assert "run-1" in captured.out

    def test_list_invalid_timezone_errors(self, run_service):
        """Test CLI list with invalid timezone raises error."""
        with pytest.raises(SystemExit) as exc_info:
            run_cli(run_service, args=["list", "--created-after", "2026-05-03T10:00:00", "--timezone", "Invalid/Zone"])
        assert exc_info.value.code == 1


class TestCliAttemptListWithDurationFilters:
    """Test CLI attempt list command with duration filters."""

    def test_attempt_list_with_duration_min(self, attempt_service, capsys):
        """Test CLI attempt list with --duration-min."""
        run_cli(None, attempt_service, args=["attempt", "list", "--duration-min", "15.0"])
        captured = capsys.readouterr()
        assert "attempt-2" in captured.out

    def test_attempt_list_with_duration_max(self, attempt_service, capsys):
        """Test CLI attempt list with --duration-max."""
        run_cli(None, attempt_service, args=["attempt", "list", "--duration-max", "15.0"])
        captured = capsys.readouterr()
        assert "attempt-1" in captured.out

    def test_attempt_list_with_duration_range(self, attempt_service, capsys):
        """Test CLI attempt list with both duration bounds."""
        run_cli(None, attempt_service, args=["attempt", "list", "--duration-min", "15.0", "--duration-max", "25.0"])
        captured = capsys.readouterr()
        assert "attempt-2" in captured.out


class TestCliAttemptListWithTimestampFilters:
    """Test CLI attempt list command with timestamp filters."""

    def test_attempt_list_with_started_after(self, attempt_service, capsys):
        """Test CLI attempt list with --started-after."""
        run_cli(None, attempt_service, args=["attempt", "list", "--started-after", "2026-05-03T09:00:00"])
        captured = capsys.readouterr()
        assert "attempt-1" in captured.out

    def test_attempt_list_with_started_before(self, attempt_service, capsys):
        """Test CLI attempt list with --started-before."""
        run_cli(None, attempt_service, args=["attempt", "list", "--started-before", "2026-05-03T11:00:00"])
        captured = capsys.readouterr()
        assert "attempt-1" in captured.out

    def test_attempt_list_with_completed_after(self, attempt_service, capsys):
        """Test CLI attempt list with --completed-after."""
        # Note: our test attempts have completed_at=None, so this returns empty
        run_cli(None, attempt_service, args=["attempt", "list", "--completed-after", "2026-05-03T09:00:00"])
        captured = capsys.readouterr()
        assert "No attempts found" in captured.out

    def test_attempt_list_with_started_range(self, attempt_service, capsys):
        """Test CLI attempt list with started range."""
        run_cli(None, attempt_service, args=[
            "attempt", "list",
            "--started-after", "2026-05-03T09:00:00",
            "--started-before", "2026-05-03T11:00:00",
        ])
        captured = capsys.readouterr()
        assert "attempt-1" in captured.out


class TestCliAttemptListWithTimezone:
    """Test CLI attempt list with timezone support."""

    def test_attempt_list_with_timezone_cest(self, attempt_service, capsys):
        """Test CLI attempt list with CEST timezone."""
        # 2026-05-03T12:00:00 in CEST (UTC+2) = 2026-05-03T10:00:00 in UTC
        run_cli(None, attempt_service, args=[
            "attempt", "list",
            "--started-after", "2026-05-03T12:00:00",
            "--timezone", "Europe/Paris",
        ])
        captured = capsys.readouterr()
        assert "attempt-1" in captured.out


class TestCliListByBranch:
    """Test CLI list filtering by branch."""

    def test_list_filter_by_branch(self, run_service, capsys):
        """Test CLI list with branch filter."""
        run_cli(run_service, args=["list", "--branch", "main"])
        captured = capsys.readouterr()
        assert "run-1" in captured.out
        assert "run-2" in captured.out

    def test_list_branch_no_matches(self, run_service, capsys):
        """Test CLI list branch filter with no matches."""
        run_cli(run_service, args=["list", "--branch", "nonexistent"])
        captured = capsys.readouterr()
        assert "No runs found" in captured.out


class TestCliListByStatus:
    """Test CLI list filtering by status."""

    def test_list_filter_by_status(self, run_service, capsys):
        """Test CLI list with status filter."""
        run_cli(run_service, args=["list", "--status", "completed"])
        captured = capsys.readouterr()
        assert "run-1" in captured.out


class TestCliListCompositeFilters:
    """Test CLI list with multiple filters combined."""

    def test_list_branch_and_duration(self, run_service, capsys):
        """Test CLI list with branch and duration filters."""
        run_cli(run_service, args=[
            "list",
            "--branch", "main",
            "--duration-min", "15.0",
        ])
        captured = capsys.readouterr()
        assert "run-2" in captured.out
        assert "run-1" not in captured.out

    def test_list_duration_and_status(self, run_service, capsys):
        """Test CLI list with duration and status filters."""
        run_cli(run_service, args=[
            "list",
            "--duration-min", "25.0",
            "--status", "completed",
        ])
        captured = capsys.readouterr()
        assert "run-3" in captured.out

    def test_list_all_filters_together(self, run_service, capsys):
        """Test CLI list with all filter types combined."""
        run_cli(run_service, args=[
            "list",
            "--branch", "main",
            "--duration-min", "15.0",
            "--duration-max", "25.0",
            "--created-after", "2026-05-03T09:00:00",
        ])
        captured = capsys.readouterr()
        assert "run-2" in captured.out


class TestCliAttemptListByRunId:
    """Test CLI attempt list filtering by run ID."""

    def test_attempt_list_filter_by_run_id(self, attempt_service, capsys):
        """Test CLI attempt list with run ID filter."""
        run_cli(None, attempt_service, args=["attempt", "list", "--run-id", "run-1"])
        captured = capsys.readouterr()
        assert "attempt-1" in captured.out

    def test_attempt_list_run_id_no_matches(self, attempt_service, capsys):
        """Test CLI attempt list run ID filter with no matches."""
        run_cli(None, attempt_service, args=["attempt", "list", "--run-id", "nonexistent"])
        captured = capsys.readouterr()
        assert "No attempts found" in captured.out


class TestCliAttemptListCompositeFilters:
    """Test CLI attempt list with multiple filters combined."""

    def test_attempt_list_run_id_and_duration(self, attempt_service, capsys):
        """Test CLI attempt list with run_id and duration filters."""
        run_cli(None, attempt_service, args=[
            "attempt", "list",
            "--run-id", "run-1",
            "--duration-min", "15.0",
        ])
        captured = capsys.readouterr()
        assert "No attempts found" in captured.out

    def test_attempt_list_duration_and_started(self, attempt_service, capsys):
        """Test CLI attempt list with duration and started filters."""
        run_cli(None, attempt_service, args=[
            "attempt", "list",
            "--duration-min", "15.0",
            "--started-after", "2026-05-03T09:00:00",
        ])
        captured = capsys.readouterr()
        assert "attempt-2" in captured.out
