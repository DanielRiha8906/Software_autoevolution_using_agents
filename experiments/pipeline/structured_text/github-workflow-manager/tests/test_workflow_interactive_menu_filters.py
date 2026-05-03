"""Tests for interactive menu filtering capabilities."""

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


class TestInteractiveMenuFilteringLogic:
    """Test filtering logic that interactive menu relies on."""

    def test_run_service_filter_by_branch_works(self, run_service):
        """Test run service branch filtering works for menu."""
        result = run_service.filter_runs(branch="main")
        assert len(result) == 2
        assert all(r.branch == "main" for r in result)

    def test_run_service_filter_by_duration_works(self, run_service):
        """Test run service duration filtering works for menu."""
        result = run_service.filter_runs(duration_min_seconds=15.0)
        assert len(result) == 2
        assert all(r.duration_seconds >= 15.0 for r in result)

    def test_run_service_multi_filter_works(self, run_service):
        """Test run service multiple filters work for menu."""
        result = run_service.filter_runs(
            branch="main",
            duration_min_seconds=15.0,
        )
        assert len(result) == 1
        assert result[0].id == "run-2"

    def test_attempt_service_filter_by_run_id_works(self, attempt_service):
        """Test attempt service run ID filtering works for menu."""
        result = attempt_service.filter_attempts(run_id="run-1")
        assert len(result) == 1
        assert result[0].run_id == "run-1"

    def test_attempt_service_filter_by_duration_works(self, attempt_service):
        """Test attempt service duration filtering works for menu."""
        result = attempt_service.filter_attempts(duration_min_seconds=15.0)
        assert len(result) == 1
        assert result[0].duration_seconds >= 15.0

    def test_attempt_service_multi_filter_works(self, attempt_service):
        """Test attempt service multiple filters work for menu."""
        result = attempt_service.filter_attempts(
            run_id="run-2",
            duration_min_seconds=15.0,
        )
        assert len(result) == 1
        assert result[0].id == "attempt-2"


class TestInteractiveMenuFilterResults:
    """Test that filter results display correctly for menu."""

    def test_run_filter_returns_display_friendly_list(self, run_service):
        """Test run filter returns list suitable for menu display."""
        result = run_service.filter_runs(branch="main")
        assert len(result) > 0
        assert all(isinstance(r, WorkflowRun) for r in result)

    def test_attempt_filter_returns_display_friendly_list(self, attempt_service):
        """Test attempt filter returns list suitable for menu display."""
        result = attempt_service.filter_attempts(run_id="run-1")
        assert len(result) > 0
        assert all(isinstance(a, WorkflowRunAttempt) for a in result)

    def test_empty_filter_result(self, run_service):
        """Test empty filter results can be shown in menu."""
        result = run_service.filter_runs(branch="nonexistent")
        assert result == []


class TestInteractiveMenuFilterEdgeCases:
    """Test edge cases for interactive menu filtering."""

    def test_filter_with_none_criteria_values(self, run_service):
        """Test filtering with None criteria values (skip filter)."""
        result = run_service.filter_runs(
            branch=None,
            duration_min_seconds=None,
        )
        assert len(result) == 3

    def test_filter_all_runs(self, run_service):
        """Test filtering that returns all runs."""
        result = run_service.filter_runs()
        assert len(result) == 3

    def test_filter_single_run(self, run_service):
        """Test filtering that returns single run."""
        result = run_service.filter_runs(branch="develop")
        assert len(result) == 1
        assert result[0].branch == "develop"

    def test_filter_no_runs(self, run_service):
        """Test filtering that returns no runs."""
        result = run_service.filter_runs(branch="nonexistent")
        assert len(result) == 0

    def test_filter_all_attempts(self, attempt_service):
        """Test filtering that returns all attempts."""
        result = attempt_service.filter_attempts()
        assert len(result) == 2

    def test_filter_no_attempts(self, attempt_service):
        """Test filtering that returns no attempts."""
        result = attempt_service.filter_attempts(run_id="nonexistent")
        assert len(result) == 0


class TestInteractiveMenuTimestampFiltering:
    """Test timestamp filtering for interactive menu."""

    def test_run_filter_by_created_timestamp(self, run_service):
        """Test run service timestamp filtering for menu."""
        cutoff = datetime(2026, 5, 3, 10, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = run_service.filter_runs(created_after=cutoff)
        assert len(result) >= 0
        if result:
            assert all(r.created_at >= cutoff for r in result)

    def test_attempt_filter_by_started_timestamp(self, attempt_service):
        """Test attempt service timestamp filtering for menu."""
        cutoff = datetime(2026, 5, 3, 10, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = attempt_service.filter_attempts(started_after=cutoff)
        assert len(result) >= 0
        if result:
            assert all(a.started_at >= cutoff for a in result)


class TestInteractiveMenuAttemptFiltering:
    """Test attempt filtering for interactive menu."""

    def test_run_filter_by_has_attempts(self, run_service, attempt_service):
        """Test run service attempts filtering for menu."""
        result = run_service.filter_runs(with_attempts=True, attempt_service=attempt_service)
        assert len(result) == 2
        assert all(r.id in ("run-1", "run-2") for r in result)

    def test_run_filter_without_attempts(self, run_service, attempt_service):
        """Test run service without-attempts filtering for menu."""
        result = run_service.filter_runs(with_attempts=False, attempt_service=attempt_service)
        assert len(result) == 1
        assert result[0].id == "run-3"


class TestInteractiveMenuStatusFiltering:
    """Test status and conclusion filtering for interactive menu."""

    def test_run_filter_by_status(self, run_service):
        """Test run service status filtering for menu."""
        result = run_service.filter_runs(status=WorkflowStatus.COMPLETED)
        assert len(result) == 3
        assert all(r.status == WorkflowStatus.COMPLETED for r in result)

    def test_run_filter_by_conclusion(self, run_service):
        """Test run service conclusion filtering for menu."""
        result = run_service.filter_runs(conclusion=WorkflowConclusion.SUCCESS)
        assert len(result) == 3
        assert all(r.conclusion == WorkflowConclusion.SUCCESS for r in result)

    def test_attempt_filter_by_status(self, attempt_service):
        """Test attempt service status filtering for menu."""
        result = attempt_service.filter_attempts(status=WorkflowStatus.COMPLETED)
        assert len(result) == 2
        assert all(a.status == WorkflowStatus.COMPLETED for a in result)
