"""Tests for WorkflowRunService filtering capabilities."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService


def _make_run(
    run_id: str = "run-1",
    branch: str = "main",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    created_at: datetime = None,
    updated_at: datetime = None,
    duration_seconds: float = 0.0,
) -> WorkflowRun:
    if created_at is None:
        created_at = datetime(2026, 5, 3, 10, 0, 0)
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch=branch,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        updated_at=updated_at,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def service():
    storage = MagicMock()
    storage.load.return_value = []
    return WorkflowRunService(storage)


@pytest.fixture
def service_with_runs():
    """Service pre-populated with test data."""
    storage = MagicMock()
    runs = [
        _make_run("run-1", "main", duration_seconds=10.0),
        _make_run("run-2", "main", duration_seconds=20.0),
        _make_run("run-3", "main", duration_seconds=30.0),
        _make_run("run-4", "develop", duration_seconds=15.0),
        _make_run("run-5", "develop", duration_seconds=25.0),
    ]
    storage.load.return_value = runs
    return WorkflowRunService(storage)


class TestFilterByDurationRange:
    """Test filter_by_duration_range method."""

    def test_filter_no_bounds_returns_all_sorted(self, service_with_runs):
        """Test with no bounds returns all runs sorted by duration."""
        result = service_with_runs.filter_by_duration_range()
        assert len(result) == 5
        durations = [r.duration_seconds for r in result]
        assert durations == [10.0, 15.0, 20.0, 25.0, 30.0]

    def test_filter_min_only(self, service_with_runs):
        """Test with minimum duration only."""
        result = service_with_runs.filter_by_duration_range(min_seconds=20.0)
        assert len(result) == 3
        assert all(r.duration_seconds >= 20.0 for r in result)

    def test_filter_max_only(self, service_with_runs):
        """Test with maximum duration only."""
        result = service_with_runs.filter_by_duration_range(max_seconds=20.0)
        assert len(result) == 3
        assert all(r.duration_seconds <= 20.0 for r in result)

    def test_filter_both_bounds(self, service_with_runs):
        """Test with both minimum and maximum."""
        result = service_with_runs.filter_by_duration_range(min_seconds=15.0, max_seconds=25.0)
        assert len(result) == 3
        assert all(15.0 <= r.duration_seconds <= 25.0 for r in result)

    def test_filter_exact_min_boundary(self, service_with_runs):
        """Test exact minimum boundary is inclusive."""
        result = service_with_runs.filter_by_duration_range(min_seconds=10.0)
        assert len(result) == 5
        assert result[0].duration_seconds == 10.0

    def test_filter_exact_max_boundary(self, service_with_runs):
        """Test exact maximum boundary is inclusive."""
        result = service_with_runs.filter_by_duration_range(max_seconds=30.0)
        assert len(result) == 5
        assert result[-1].duration_seconds == 30.0

    def test_filter_no_matches_empty_result(self, service_with_runs):
        """Test filter with no matches returns empty list."""
        result = service_with_runs.filter_by_duration_range(min_seconds=100.0)
        assert result == []

    def test_filter_negative_min_raises(self, service):
        """Test negative minimum raises ValueError."""
        with pytest.raises(ValueError, match="min_seconds must be non-negative"):
            service.filter_by_duration_range(min_seconds=-1.0)

    def test_filter_negative_max_raises(self, service):
        """Test negative maximum raises ValueError."""
        with pytest.raises(ValueError, match="max_seconds must be non-negative"):
            service.filter_by_duration_range(max_seconds=-1.0)

    def test_filter_min_greater_than_max_raises(self, service):
        """Test min > max raises ValueError."""
        with pytest.raises(ValueError, match="min_seconds.*must be <= max_seconds"):
            service.filter_by_duration_range(min_seconds=30.0, max_seconds=10.0)

    def test_filter_zero_duration(self, service_with_runs):
        """Test filtering with zero duration."""
        result = service_with_runs.filter_by_duration_range(min_seconds=0.0, max_seconds=10.0)
        assert len(result) == 1
        assert result[0].duration_seconds == 10.0

    def test_filter_results_sorted_ascending(self, service_with_runs):
        """Test results are sorted by duration ascending."""
        result = service_with_runs.filter_by_duration_range(min_seconds=10.0, max_seconds=30.0)
        for i in range(len(result) - 1):
            assert result[i].duration_seconds <= result[i + 1].duration_seconds


class TestFilterByCreatedAt:
    """Test filter_by_created_at method."""

    def test_filter_no_bounds_returns_all_sorted(self, service_with_runs):
        """Test with no bounds returns all runs sorted by created_at."""
        result = service_with_runs.filter_by_created_at()
        assert len(result) == 5

    def test_filter_after_only(self, service_with_runs):
        """Test filtering with after timestamp only."""
        cutoff = datetime(2026, 5, 3, 10, 0, 0)
        result = service_with_runs.filter_by_created_at(after=cutoff)
        assert len(result) == 5
        assert all(r.created_at >= cutoff for r in result)

    def test_filter_before_only(self, service_with_runs):
        """Test filtering with before timestamp only."""
        cutoff = datetime(2026, 5, 3, 10, 0, 0)
        result = service_with_runs.filter_by_created_at(before=cutoff)
        assert len(result) == 5
        assert all(r.created_at <= cutoff for r in result)

    def test_filter_range(self):
        """Test filtering with before and after."""
        storage = MagicMock()
        runs = [
            _make_run("run-1", created_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_run("run-2", created_at=datetime(2026, 5, 3, 10, 0, 0)),
            _make_run("run-3", created_at=datetime(2026, 5, 5, 10, 0, 0)),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        result = service.filter_by_created_at(
            after=datetime(2026, 5, 2, 0, 0, 0),
            before=datetime(2026, 5, 4, 0, 0, 0),
        )
        assert len(result) == 1
        assert result[0].id == "run-2"

    def test_filter_exact_boundaries_inclusive(self):
        """Test boundaries are inclusive."""
        storage = MagicMock()
        cutoff = datetime(2026, 5, 3, 10, 0, 0)
        runs = [
            _make_run("run-1", created_at=cutoff),
            _make_run("run-2", created_at=cutoff + timedelta(seconds=1)),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        result = service.filter_by_created_at(after=cutoff, before=cutoff)
        assert len(result) == 1
        assert result[0].id == "run-1"

    def test_filter_no_matches_returns_empty(self):
        """Test filter with no matches returns empty list."""
        storage = MagicMock()
        runs = [_make_run("run-1", created_at=datetime(2026, 5, 1, 10, 0, 0))]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        result = service.filter_by_created_at(
            after=datetime(2026, 5, 5, 0, 0, 0),
        )
        assert result == []

    def test_filter_before_less_than_after_raises(self, service):
        """Test before < after raises ValueError."""
        before = datetime(2026, 5, 1, 10, 0, 0)
        after = datetime(2026, 5, 3, 10, 0, 0)
        with pytest.raises(ValueError, match="after.*must be <= before"):
            service.filter_by_created_at(before=before, after=after)

    def test_filter_results_sorted_ascending(self):
        """Test results are sorted by created_at ascending."""
        storage = MagicMock()
        runs = [
            _make_run("run-1", created_at=datetime(2026, 5, 5, 10, 0, 0)),
            _make_run("run-2", created_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_run("run-3", created_at=datetime(2026, 5, 3, 10, 0, 0)),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        result = service.filter_by_created_at()
        for i in range(len(result) - 1):
            assert result[i].created_at <= result[i + 1].created_at


class TestFilterByUpdatedAt:
    """Test filter_by_updated_at method."""

    def test_filter_ignores_none_values(self):
        """Test runs with updated_at=None are excluded."""
        storage = MagicMock()
        runs = [
            _make_run("run-1", updated_at=datetime(2026, 5, 3, 10, 0, 0)),
            _make_run("run-2", updated_at=None),
            _make_run("run-3", updated_at=datetime(2026, 5, 3, 11, 0, 0)),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        result = service.filter_by_updated_at()
        assert len(result) == 2
        assert all(r.updated_at is not None for r in result)

    def test_filter_after_only(self):
        """Test filtering with after timestamp."""
        storage = MagicMock()
        cutoff = datetime(2026, 5, 3, 10, 0, 0)
        runs = [
            _make_run("run-1", updated_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_run("run-2", updated_at=cutoff),
            _make_run("run-3", updated_at=datetime(2026, 5, 5, 10, 0, 0)),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        result = service.filter_by_updated_at(after=cutoff)
        assert len(result) == 2
        assert all(r.updated_at >= cutoff for r in result)

    def test_filter_before_only(self):
        """Test filtering with before timestamp."""
        storage = MagicMock()
        cutoff = datetime(2026, 5, 3, 10, 0, 0)
        runs = [
            _make_run("run-1", updated_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_run("run-2", updated_at=cutoff),
            _make_run("run-3", updated_at=datetime(2026, 5, 5, 10, 0, 0)),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        result = service.filter_by_updated_at(before=cutoff)
        assert len(result) == 2
        assert all(r.updated_at <= cutoff for r in result)

    def test_filter_range(self):
        """Test filtering with range."""
        storage = MagicMock()
        runs = [
            _make_run("run-1", updated_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_run("run-2", updated_at=datetime(2026, 5, 3, 10, 0, 0)),
            _make_run("run-3", updated_at=datetime(2026, 5, 5, 10, 0, 0)),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        result = service.filter_by_updated_at(
            after=datetime(2026, 5, 2, 0, 0, 0),
            before=datetime(2026, 5, 4, 0, 0, 0),
        )
        assert len(result) == 1
        assert result[0].id == "run-2"

    def test_filter_before_less_than_after_raises(self, service):
        """Test before < after raises ValueError."""
        before = datetime(2026, 5, 1, 10, 0, 0)
        after = datetime(2026, 5, 3, 10, 0, 0)
        with pytest.raises(ValueError, match="after.*must be <= before"):
            service.filter_by_updated_at(before=before, after=after)

    def test_filter_results_sorted_ascending(self):
        """Test results are sorted by updated_at ascending."""
        storage = MagicMock()
        runs = [
            _make_run("run-1", updated_at=datetime(2026, 5, 5, 10, 0, 0)),
            _make_run("run-2", updated_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_run("run-3", updated_at=datetime(2026, 5, 3, 10, 0, 0)),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        result = service.filter_by_updated_at()
        for i in range(len(result) - 1):
            assert result[i].updated_at <= result[i + 1].updated_at


class TestFilterByHasAttempts:
    """Test filter_by_has_attempts method."""

    def test_filter_with_attempts_true(self):
        """Test filtering for runs with attempts."""
        storage = MagicMock()
        runs = [
            _make_run("run-1"),
            _make_run("run-2"),
            _make_run("run-3"),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        # Mock attempt service
        attempt_service = MagicMock()
        attempt_mock_1 = MagicMock()
        attempt_mock_1.run_id = "run-1"
        attempt_mock_2 = MagicMock()
        attempt_mock_2.run_id = "run-2"
        attempt_service.list_attempts.return_value = [attempt_mock_1, attempt_mock_2]

        result = service.filter_by_has_attempts(has_attempts=True, attempt_service=attempt_service)
        assert len(result) == 2
        assert result[0].id == "run-1"
        assert result[1].id == "run-2"

    def test_filter_without_attempts_true(self):
        """Test filtering for runs without attempts."""
        storage = MagicMock()
        runs = [
            _make_run("run-1"),
            _make_run("run-2"),
            _make_run("run-3"),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        # Mock attempt service
        attempt_service = MagicMock()
        attempt_mock_1 = MagicMock()
        attempt_mock_1.run_id = "run-1"
        attempt_service.list_attempts.return_value = [attempt_mock_1]

        result = service.filter_by_has_attempts(has_attempts=False, attempt_service=attempt_service)
        assert len(result) == 2
        assert result[0].id == "run-2"
        assert result[1].id == "run-3"

    def test_filter_no_attempts_at_all(self):
        """Test filtering when no attempts exist."""
        storage = MagicMock()
        runs = [_make_run("run-1"), _make_run("run-2")]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        # Mock attempt service with no attempts
        attempt_service = MagicMock()
        attempt_service.list_attempts.return_value = []

        result = service.filter_by_has_attempts(has_attempts=True, attempt_service=attempt_service)
        assert result == []

    def test_filter_with_attempts_false_no_attempts(self):
        """Test filtering without attempts when no attempts exist."""
        storage = MagicMock()
        runs = [_make_run("run-1"), _make_run("run-2")]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        # Mock attempt service with no attempts
        attempt_service = MagicMock()
        attempt_service.list_attempts.return_value = []

        result = service.filter_by_has_attempts(has_attempts=False, attempt_service=attempt_service)
        assert len(result) == 2

    def test_filter_none_service_raises(self, service):
        """Test None attempt_service raises ValueError."""
        with pytest.raises(ValueError, match="attempt_service cannot be None"):
            service.filter_by_has_attempts(has_attempts=True, attempt_service=None)

    def test_filter_preserves_original_order(self):
        """Test original order is preserved."""
        storage = MagicMock()
        runs = [
            _make_run("run-1"),
            _make_run("run-2"),
            _make_run("run-3"),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        # Mock attempt service
        attempt_service = MagicMock()
        attempt_mock = MagicMock()
        attempt_mock.run_id = "run-2"
        attempt_service.list_attempts.return_value = [attempt_mock]

        result = service.filter_by_has_attempts(has_attempts=True, attempt_service=attempt_service)
        assert result[0].id == "run-2"


class TestCompositeFilterRuns:
    """Test filter_runs composite filter method."""

    def test_filter_no_criteria_returns_all(self, service_with_runs):
        """Test with no criteria returns all runs."""
        result = service_with_runs.filter_runs()
        assert len(result) == 5

    def test_filter_duration_and_status(self, service_with_runs):
        """Test combining duration and status filters."""
        result = service_with_runs.filter_runs(
            duration_min_seconds=15.0,
            status=WorkflowStatus.COMPLETED,
        )
        assert len(result) == 4
        assert all(r.duration_seconds >= 15.0 and r.status == WorkflowStatus.COMPLETED for r in result)

    def test_filter_branch_and_duration(self, service_with_runs):
        """Test combining branch and duration filters."""
        result = service_with_runs.filter_runs(
            branch="main",
            duration_max_seconds=20.0,
        )
        assert len(result) == 2
        assert all(r.branch == "main" and r.duration_seconds <= 20.0 for r in result)

    def test_filter_created_and_duration(self):
        """Test combining timestamp and duration filters."""
        storage = MagicMock()
        runs = [
            _make_run("run-1", created_at=datetime(2026, 5, 1, 10, 0, 0), duration_seconds=10.0),
            _make_run("run-2", created_at=datetime(2026, 5, 3, 10, 0, 0), duration_seconds=20.0),
            _make_run("run-3", created_at=datetime(2026, 5, 5, 10, 0, 0), duration_seconds=30.0),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        result = service.filter_runs(
            created_after=datetime(2026, 5, 2, 0, 0, 0),
            duration_min_seconds=15.0,
        )
        assert len(result) == 2
        assert all(r.created_at >= datetime(2026, 5, 2, 0, 0, 0) and r.duration_seconds >= 15.0 for r in result)

    def test_filter_all_criteria_together(self):
        """Test combining all filter criteria (AND logic)."""
        storage = MagicMock()
        runs = [
            _make_run("run-1", "main", duration_seconds=10.0, created_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_run("run-2", "main", duration_seconds=20.0, created_at=datetime(2026, 5, 3, 10, 0, 0)),
            _make_run("run-3", "develop", duration_seconds=30.0, created_at=datetime(2026, 5, 5, 10, 0, 0)),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        result = service.filter_runs(
            branch="main",
            duration_min_seconds=15.0,
            duration_max_seconds=25.0,
            created_after=datetime(2026, 5, 2, 0, 0, 0),
        )
        assert len(result) == 1
        assert result[0].id == "run-2"

    def test_filter_with_attempts_inclusion(self):
        """Test including attempts filter."""
        storage = MagicMock()
        runs = [
            _make_run("run-1"),
            _make_run("run-2"),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        attempt_service = MagicMock()
        attempt_mock = MagicMock()
        attempt_mock.run_id = "run-1"
        attempt_service.list_attempts.return_value = [attempt_mock]

        result = service.filter_runs(
            with_attempts=True,
            attempt_service=attempt_service,
        )
        assert len(result) == 1
        assert result[0].id == "run-1"

    def test_filter_none_criteria_skipped(self, service_with_runs):
        """Test None criteria are skipped (not applied)."""
        result = service_with_runs.filter_runs(
            branch=None,
            status=None,
            duration_min_seconds=None,
        )
        assert len(result) == 5

    def test_filter_and_logic_no_false_positives(self):
        """Test AND logic prevents false positives."""
        storage = MagicMock()
        runs = [
            _make_run("run-1", "main", duration_seconds=10.0),
            _make_run("run-2", "develop", duration_seconds=20.0),
            _make_run("run-3", "main", duration_seconds=30.0),
        ]
        storage.load.return_value = runs
        service = WorkflowRunService(storage)

        # Matches branch OR duration_min, but not both
        result = service.filter_runs(
            branch="develop",
            duration_min_seconds=25.0,
        )
        assert len(result) == 0

    def test_filter_invalid_parameters_propagate(self, service):
        """Test invalid parameters raise errors."""
        with pytest.raises(ValueError):
            service.filter_runs(
                duration_min_seconds=30.0,
                duration_max_seconds=10.0,
            )
