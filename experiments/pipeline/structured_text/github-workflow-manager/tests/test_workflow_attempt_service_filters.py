"""Tests for WorkflowAttemptService filtering capabilities."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.models.workflow_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_attempt_service import WorkflowAttemptService


def _make_attempt(
    attempt_id: str = "attempt-1",
    run_id: str = "run-1",
    attempt_number: int = 1,
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    started_at: datetime = None,
    completed_at: datetime = None,
    duration_seconds: float = 0.0,
) -> WorkflowRunAttempt:
    if started_at is None:
        started_at = datetime(2026, 5, 3, 10, 0, 0)
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def service():
    storage = MagicMock()
    storage.load.return_value = []
    return WorkflowAttemptService(storage)


@pytest.fixture
def service_with_attempts():
    """Service pre-populated with test data."""
    storage = MagicMock()
    attempts = [
        _make_attempt("attempt-1", "run-1", 1, duration_seconds=10.0),
        _make_attempt("attempt-2", "run-1", 2, duration_seconds=20.0),
        _make_attempt("attempt-3", "run-2", 1, duration_seconds=30.0),
        _make_attempt("attempt-4", "run-2", 2, duration_seconds=15.0),
        _make_attempt("attempt-5", "run-3", 1, duration_seconds=25.0),
    ]
    storage.load.return_value = attempts
    return WorkflowAttemptService(storage)


class TestFilterByDurationRange:
    """Test filter_by_duration_range method."""

    def test_filter_no_bounds_returns_all_sorted(self, service_with_attempts):
        """Test with no bounds returns all attempts sorted by attempt_number."""
        result = service_with_attempts.filter_by_duration_range()
        assert len(result) == 5
        # Should be sorted by attempt_number, not duration
        attempt_numbers = [a.attempt_number for a in result]
        assert attempt_numbers == [1, 1, 1, 2, 2]

    def test_filter_min_only(self, service_with_attempts):
        """Test with minimum duration only."""
        result = service_with_attempts.filter_by_duration_range(min_seconds=20.0)
        assert len(result) == 3
        assert all(a.duration_seconds >= 20.0 for a in result)

    def test_filter_max_only(self, service_with_attempts):
        """Test with maximum duration only."""
        result = service_with_attempts.filter_by_duration_range(max_seconds=20.0)
        assert len(result) == 3
        assert all(a.duration_seconds <= 20.0 for a in result)

    def test_filter_both_bounds(self, service_with_attempts):
        """Test with both minimum and maximum."""
        result = service_with_attempts.filter_by_duration_range(min_seconds=15.0, max_seconds=25.0)
        assert len(result) == 3
        assert all(15.0 <= a.duration_seconds <= 25.0 for a in result)

    def test_filter_exact_boundaries_inclusive(self, service_with_attempts):
        """Test exact boundaries are inclusive."""
        result = service_with_attempts.filter_by_duration_range(min_seconds=10.0, max_seconds=10.0)
        assert len(result) == 1
        assert result[0].duration_seconds == 10.0

    def test_filter_no_matches_empty_result(self, service_with_attempts):
        """Test filter with no matches returns empty list."""
        result = service_with_attempts.filter_by_duration_range(min_seconds=100.0)
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

    def test_filter_zero_duration(self, service_with_attempts):
        """Test filtering with zero duration."""
        result = service_with_attempts.filter_by_duration_range(min_seconds=0.0, max_seconds=10.0)
        assert len(result) == 1
        assert result[0].duration_seconds == 10.0

    def test_filter_results_sorted_by_attempt_number(self, service_with_attempts):
        """Test results are sorted by attempt_number, not duration."""
        result = service_with_attempts.filter_by_duration_range()
        for i in range(len(result) - 1):
            assert result[i].attempt_number <= result[i + 1].attempt_number


class TestFilterByStartedAt:
    """Test filter_by_started_at method."""

    def test_filter_no_bounds_returns_all(self, service_with_attempts):
        """Test with no bounds returns all attempts."""
        result = service_with_attempts.filter_by_started_at()
        assert len(result) == 5

    def test_filter_after_only(self):
        """Test filtering with after timestamp only."""
        storage = MagicMock()
        cutoff = datetime(2026, 5, 3, 10, 0, 0)
        attempts = [
            _make_attempt("attempt-1", started_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_attempt("attempt-2", started_at=cutoff),
            _make_attempt("attempt-3", started_at=datetime(2026, 5, 5, 10, 0, 0)),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_by_started_at(after=cutoff)
        assert len(result) == 2
        assert all(a.started_at >= cutoff for a in result)

    def test_filter_before_only(self):
        """Test filtering with before timestamp only."""
        storage = MagicMock()
        cutoff = datetime(2026, 5, 3, 10, 0, 0)
        attempts = [
            _make_attempt("attempt-1", started_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_attempt("attempt-2", started_at=cutoff),
            _make_attempt("attempt-3", started_at=datetime(2026, 5, 5, 10, 0, 0)),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_by_started_at(before=cutoff)
        assert len(result) == 2
        assert all(a.started_at <= cutoff for a in result)

    def test_filter_range(self):
        """Test filtering with before and after."""
        storage = MagicMock()
        attempts = [
            _make_attempt("attempt-1", started_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_attempt("attempt-2", started_at=datetime(2026, 5, 3, 10, 0, 0)),
            _make_attempt("attempt-3", started_at=datetime(2026, 5, 5, 10, 0, 0)),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_by_started_at(
            after=datetime(2026, 5, 2, 0, 0, 0),
            before=datetime(2026, 5, 4, 0, 0, 0),
        )
        assert len(result) == 1
        assert result[0].id == "attempt-2"

    def test_filter_exact_boundaries_inclusive(self):
        """Test boundaries are inclusive."""
        storage = MagicMock()
        cutoff = datetime(2026, 5, 3, 10, 0, 0)
        attempts = [
            _make_attempt("attempt-1", started_at=cutoff),
            _make_attempt("attempt-2", started_at=cutoff + timedelta(seconds=1)),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_by_started_at(after=cutoff, before=cutoff)
        assert len(result) == 1
        assert result[0].id == "attempt-1"

    def test_filter_before_less_than_after_raises(self, service):
        """Test before < after raises ValueError."""
        before = datetime(2026, 5, 1, 10, 0, 0)
        after = datetime(2026, 5, 3, 10, 0, 0)
        with pytest.raises(ValueError, match="after.*must be <= before"):
            service.filter_by_started_at(before=before, after=after)

    def test_filter_results_sorted_by_attempt_number(self):
        """Test results are sorted by attempt_number."""
        storage = MagicMock()
        attempts = [
            _make_attempt("attempt-1", attempt_number=2, started_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_attempt("attempt-2", attempt_number=1, started_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_attempt("attempt-3", attempt_number=3, started_at=datetime(2026, 5, 1, 10, 0, 0)),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_by_started_at()
        assert [a.attempt_number for a in result] == [1, 2, 3]


class TestFilterByCompletedAt:
    """Test filter_by_completed_at method."""

    def test_filter_ignores_none_values(self):
        """Test attempts with completed_at=None are excluded."""
        storage = MagicMock()
        attempts = [
            _make_attempt("attempt-1", completed_at=datetime(2026, 5, 3, 10, 0, 0)),
            _make_attempt("attempt-2", completed_at=None),
            _make_attempt("attempt-3", completed_at=datetime(2026, 5, 3, 11, 0, 0)),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_by_completed_at()
        assert len(result) == 2
        assert all(a.completed_at is not None for a in result)

    def test_filter_after_only(self):
        """Test filtering with after timestamp."""
        storage = MagicMock()
        cutoff = datetime(2026, 5, 3, 10, 0, 0)
        attempts = [
            _make_attempt("attempt-1", completed_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_attempt("attempt-2", completed_at=cutoff),
            _make_attempt("attempt-3", completed_at=datetime(2026, 5, 5, 10, 0, 0)),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_by_completed_at(after=cutoff)
        assert len(result) == 2
        assert all(a.completed_at >= cutoff for a in result)

    def test_filter_before_only(self):
        """Test filtering with before timestamp."""
        storage = MagicMock()
        cutoff = datetime(2026, 5, 3, 10, 0, 0)
        attempts = [
            _make_attempt("attempt-1", completed_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_attempt("attempt-2", completed_at=cutoff),
            _make_attempt("attempt-3", completed_at=datetime(2026, 5, 5, 10, 0, 0)),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_by_completed_at(before=cutoff)
        assert len(result) == 2
        assert all(a.completed_at <= cutoff for a in result)

    def test_filter_range(self):
        """Test filtering with range."""
        storage = MagicMock()
        attempts = [
            _make_attempt("attempt-1", completed_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_attempt("attempt-2", completed_at=datetime(2026, 5, 3, 10, 0, 0)),
            _make_attempt("attempt-3", completed_at=datetime(2026, 5, 5, 10, 0, 0)),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_by_completed_at(
            after=datetime(2026, 5, 2, 0, 0, 0),
            before=datetime(2026, 5, 4, 0, 0, 0),
        )
        assert len(result) == 1
        assert result[0].id == "attempt-2"

    def test_filter_before_less_than_after_raises(self, service):
        """Test before < after raises ValueError."""
        before = datetime(2026, 5, 1, 10, 0, 0)
        after = datetime(2026, 5, 3, 10, 0, 0)
        with pytest.raises(ValueError, match="after.*must be <= before"):
            service.filter_by_completed_at(before=before, after=after)

    def test_filter_results_sorted_by_attempt_number(self):
        """Test results are sorted by attempt_number."""
        storage = MagicMock()
        attempts = [
            _make_attempt("attempt-1", attempt_number=2, completed_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_attempt("attempt-2", attempt_number=1, completed_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_attempt("attempt-3", attempt_number=3, completed_at=datetime(2026, 5, 1, 10, 0, 0)),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_by_completed_at()
        assert [a.attempt_number for a in result] == [1, 2, 3]


class TestCompositeFilterAttempts:
    """Test filter_attempts composite filter method."""

    def test_filter_no_criteria_returns_all(self, service_with_attempts):
        """Test with no criteria returns all attempts."""
        result = service_with_attempts.filter_attempts()
        assert len(result) == 5

    def test_filter_by_run_id_only(self, service_with_attempts):
        """Test filtering by run ID only."""
        result = service_with_attempts.filter_attempts(run_id="run-1")
        assert len(result) == 2
        assert all(a.run_id == "run-1" for a in result)

    def test_filter_by_status_only(self):
        """Test filtering by status only."""
        storage = MagicMock()
        attempts = [
            _make_attempt("attempt-1", status=WorkflowStatus.COMPLETED),
            _make_attempt("attempt-2", status=WorkflowStatus.IN_PROGRESS),
            _make_attempt("attempt-3", status=WorkflowStatus.COMPLETED),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_attempts(status=WorkflowStatus.COMPLETED)
        assert len(result) == 2
        assert all(a.status == WorkflowStatus.COMPLETED for a in result)

    def test_filter_run_id_and_duration(self, service_with_attempts):
        """Test combining run_id and duration filters."""
        result = service_with_attempts.filter_attempts(
            run_id="run-1",
            duration_min_seconds=15.0,
        )
        assert len(result) == 1
        assert result[0].id == "attempt-2"

    def test_filter_duration_and_started_at(self):
        """Test combining duration and started_at filters."""
        storage = MagicMock()
        attempts = [
            _make_attempt("attempt-1", started_at=datetime(2026, 5, 1, 10, 0, 0), duration_seconds=10.0),
            _make_attempt("attempt-2", started_at=datetime(2026, 5, 3, 10, 0, 0), duration_seconds=20.0),
            _make_attempt("attempt-3", started_at=datetime(2026, 5, 5, 10, 0, 0), duration_seconds=30.0),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_attempts(
            started_after=datetime(2026, 5, 2, 0, 0, 0),
            duration_min_seconds=15.0,
        )
        assert len(result) == 2
        assert all(a.started_at >= datetime(2026, 5, 2, 0, 0, 0) and a.duration_seconds >= 15.0 for a in result)

    def test_filter_all_criteria_together(self):
        """Test combining all filter criteria (AND logic)."""
        storage = MagicMock()
        attempts = [
            _make_attempt("attempt-1", "run-1", 1, duration_seconds=10.0, started_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_attempt("attempt-2", "run-1", 2, duration_seconds=20.0, started_at=datetime(2026, 5, 3, 10, 0, 0)),
            _make_attempt("attempt-3", "run-2", 1, duration_seconds=30.0, started_at=datetime(2026, 5, 5, 10, 0, 0)),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_attempts(
            run_id="run-1",
            duration_min_seconds=15.0,
            started_after=datetime(2026, 5, 2, 0, 0, 0),
        )
        assert len(result) == 1
        assert result[0].id == "attempt-2"

    def test_filter_none_criteria_skipped(self, service_with_attempts):
        """Test None criteria are skipped."""
        result = service_with_attempts.filter_attempts(
            run_id=None,
            status=None,
            duration_min_seconds=None,
        )
        assert len(result) == 5

    def test_filter_and_logic_no_false_positives(self):
        """Test AND logic prevents false positives."""
        storage = MagicMock()
        attempts = [
            _make_attempt("attempt-1", "run-1", duration_seconds=10.0),
            _make_attempt("attempt-2", "run-2", duration_seconds=20.0),
            _make_attempt("attempt-3", "run-1", duration_seconds=30.0),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        # Matches run_id OR duration_min, but not both
        result = service.filter_attempts(
            run_id="run-2",
            duration_min_seconds=25.0,
        )
        assert len(result) == 0

    def test_filter_results_sorted_by_attempt_number(self):
        """Test results are sorted by attempt_number."""
        storage = MagicMock()
        attempts = [
            _make_attempt("attempt-1", attempt_number=3),
            _make_attempt("attempt-2", attempt_number=1),
            _make_attempt("attempt-3", attempt_number=2),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_attempts()
        assert [a.attempt_number for a in result] == [1, 2, 3]

    def test_filter_with_completion_range(self):
        """Test filtering with completed_at range."""
        storage = MagicMock()
        attempts = [
            _make_attempt("attempt-1", completed_at=datetime(2026, 5, 1, 10, 0, 0)),
            _make_attempt("attempt-2", completed_at=datetime(2026, 5, 3, 10, 0, 0)),
            _make_attempt("attempt-3", completed_at=datetime(2026, 5, 5, 10, 0, 0)),
        ]
        storage.load.return_value = attempts
        service = WorkflowAttemptService(storage)

        result = service.filter_attempts(
            completed_after=datetime(2026, 5, 2, 0, 0, 0),
            completed_before=datetime(2026, 5, 4, 0, 0, 0),
        )
        assert len(result) == 1
        assert result[0].id == "attempt-2"

    def test_filter_invalid_parameters_propagate(self, service):
        """Test invalid parameters raise errors."""
        with pytest.raises(ValueError):
            service.filter_attempts(
                duration_min_seconds=30.0,
                duration_max_seconds=10.0,
            )
