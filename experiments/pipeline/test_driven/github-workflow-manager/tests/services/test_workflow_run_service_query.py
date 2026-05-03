import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.models.workflow_run_attempt import WorkflowRunAttempt, CEST
from src.services.workflow_run_service import WorkflowRunService
from src.services.attempt_service import AttemptService


def _make_run(
    run_id: str = "1",
    branch: str = "main",
    duration_seconds: float = 100.0,
    created_at: datetime = None,
    run_number: int = None,
) -> WorkflowRun:
    """Helper to create a WorkflowRun with sensible defaults."""
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    if run_number is None:
        try:
            run_number = int(run_id)
        except ValueError:
            run_number = 1
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch=branch,
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=created_at,
        updated_at=None,
        run_number=run_number,
        commit_sha="abc123",
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def svc():
    """Create a WorkflowRunService with two sample runs and attempts added to one."""
    storage = MagicMock()
    # Create two runs: one with 50 seconds, one with 150 seconds
    run1 = _make_run(
        run_id="1",
        duration_seconds=50.0,
        created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    run2 = _make_run(
        run_id="2",
        duration_seconds=150.0,
        created_at=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
    )
    storage.load.return_value = [run1, run2]
    svc = WorkflowRunService(storage)

    # Create attempt service and add an attempt to run2 only
    attempt_service = AttemptService()
    attempt = WorkflowRunAttempt(
        id=1,
        run_id=2,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime(2024, 1, 2, 10, 5, 0, tzinfo=CEST),
    )
    attempt_service.create(attempt)

    # Store the attempt_service for test access
    svc._attempt_service = attempt_service

    return svc


class TestFilterByDurationRange:
    """Test filtering by min_duration and max_duration."""

    def test_filter_by_duration_range(self, svc):
        """Test filtering by duration range with both min and max."""
        attempt_service = svc._attempt_service

        # Filter for runs between 60 and 160 seconds (should get run2 with 150 seconds)
        result = svc.query(min_duration=60.0, max_duration=160.0, attempt_service=attempt_service)
        assert len(result) == 1
        assert result[0].id == "2"


class TestFilterByCreatedBefore:
    """Test filtering by created_before."""

    def test_filter_by_created_before(self, svc):
        """Test filtering by created_before date."""
        attempt_service = svc._attempt_service

        # Filter for runs created before 2024-01-02 (should get only run1)
        cutoff = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        result = svc.query(created_before=cutoff, attempt_service=attempt_service)
        assert len(result) == 1
        assert result[0].id == "1"


class TestFilterByCreatedAfter:
    """Test filtering by created_after."""

    def test_filter_by_created_after(self, svc):
        """Test filtering by created_after date."""
        attempt_service = svc._attempt_service

        # Filter for runs created after 2024-01-01 15:00:00 (should get only run2 at 10:00:00 is not > 15:00:00)
        # Actually, run1 is at 10:00:00, which is not > 15:00:00, so only run2 at next day qualifies
        cutoff = datetime(2024, 1, 1, 15, 0, 0, tzinfo=timezone.utc)
        result = svc.query(created_after=cutoff, attempt_service=attempt_service)
        assert len(result) == 1
        assert result[0].id == "2"


class TestFilterRunsWithAttempts:
    """Test filtering runs that have attempts."""

    def test_filter_runs_with_attempts(self, svc):
        """Test filtering for runs with at least one attempt."""
        attempt_service = svc._attempt_service

        # Only run2 has attempts
        result = svc.query(has_attempts=True, attempt_service=attempt_service)
        assert len(result) == 1
        assert result[0].id == "2"


class TestFilterRunsWithoutAttempts:
    """Test filtering runs without attempts."""

    def test_filter_runs_without_attempts(self, svc):
        """Test filtering for runs with zero attempts."""
        attempt_service = svc._attempt_service

        # Only run1 has no attempts
        result = svc.query(has_attempts=False, attempt_service=attempt_service)
        assert len(result) == 1
        assert result[0].id == "1"


class TestCombinedFilters:
    """Test combining multiple filter conditions."""

    def test_combined_filters(self, svc):
        """Test combining duration range and attempts filters."""
        attempt_service = svc._attempt_service

        # Filter for runs with 100-200 seconds duration AND with attempts
        # Only run2 matches (150 seconds and has 1 attempt)
        result = svc.query(
            min_duration=100.0,
            max_duration=200.0,
            has_attempts=True,
            attempt_service=attempt_service
        )
        assert len(result) == 1
        assert result[0].id == "2"


class TestQueryReturnsListType:
    """Test that query() returns a list type."""

    def test_query_returns_list(self, svc):
        """Test that query() returns a list."""
        attempt_service = svc._attempt_service
        result = svc.query(attempt_service=attempt_service)
        assert isinstance(result, list)


class TestNoMatchReturnsEmptyList:
    """Test that no matches return an empty list."""

    def test_no_match_returns_empty_list(self, svc):
        """Test that query returns empty list when no runs match filters."""
        attempt_service = svc._attempt_service

        # Filter for runs with 500+ seconds (none exist)
        result = svc.query(min_duration=500.0, attempt_service=attempt_service)
        assert result == []
        assert isinstance(result, list)


# Additional edge case tests

class TestValidationErrors:
    """Test validation error conditions."""

    def test_requires_attempt_service_for_has_attempts(self, svc):
        """Test that ValueError is raised if has_attempts is set but attempt_service is None."""
        with pytest.raises(ValueError, match="attempt_service required"):
            svc.query(has_attempts=True, attempt_service=None)

    def test_created_after_must_be_before_created_before(self, svc):
        """Test that ValueError is raised if created_after >= created_before."""
        attempt_service = svc._attempt_service
        after = datetime(2024, 1, 2, tzinfo=timezone.utc)
        before = datetime(2024, 1, 1, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="created_after must be strictly before"):
            svc.query(created_after=after, created_before=before, attempt_service=attempt_service)

    def test_created_after_equal_to_created_before_raises(self, svc):
        """Test that ValueError is raised if created_after == created_before."""
        attempt_service = svc._attempt_service
        same_time = datetime(2024, 1, 2, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="created_after must be strictly before"):
            svc.query(created_after=same_time, created_before=same_time, attempt_service=attempt_service)

    def test_min_duration_greater_than_max_raises(self, svc):
        """Test that ValueError is raised if min_duration > max_duration."""
        attempt_service = svc._attempt_service

        with pytest.raises(ValueError, match="min_duration must not be greater than max_duration"):
            svc.query(min_duration=200.0, max_duration=100.0, attempt_service=attempt_service)

    def test_created_after_must_be_timezone_aware(self, svc):
        """Test that TypeError is raised if created_after is not timezone-aware."""
        attempt_service = svc._attempt_service
        naive_dt = datetime(2024, 1, 1, 10, 0, 0)  # No tzinfo

        with pytest.raises(TypeError, match="created_after must be timezone-aware"):
            svc.query(created_after=naive_dt, attempt_service=attempt_service)

    def test_created_before_must_be_timezone_aware(self, svc):
        """Test that TypeError is raised if created_before is not timezone-aware."""
        attempt_service = svc._attempt_service
        naive_dt = datetime(2024, 1, 1, 10, 0, 0)  # No tzinfo

        with pytest.raises(TypeError, match="created_before must be timezone-aware"):
            svc.query(created_before=naive_dt, attempt_service=attempt_service)


class TestDurationFilterBoundaries:
    """Test boundary conditions for duration filtering."""

    def test_min_duration_inclusive(self, svc):
        """Test that min_duration is inclusive (>=)."""
        attempt_service = svc._attempt_service

        # run1 has exactly 50.0 seconds, so it should be included with min=50.0
        result = svc.query(min_duration=50.0, attempt_service=attempt_service)
        assert len(result) == 2  # Both runs meet the criteria
        run_ids = [r.id for r in result]
        assert "1" in run_ids

    def test_max_duration_inclusive(self, svc):
        """Test that max_duration is inclusive (<=)."""
        attempt_service = svc._attempt_service

        # run2 has exactly 150.0 seconds, so it should be included with max=150.0
        result = svc.query(max_duration=150.0, attempt_service=attempt_service)
        assert len(result) == 2  # Both runs meet the criteria
        run_ids = [r.id for r in result]
        assert "2" in run_ids


class TestCreatedAtFilterBoundaries:
    """Test boundary conditions for created_at filtering."""

    def test_created_after_exclusive(self, svc):
        """Test that created_after is exclusive (>)."""
        attempt_service = svc._attempt_service

        # run1 is created at exactly 2024-01-01 10:00:00, so it should NOT be included
        cutoff = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        result = svc.query(created_after=cutoff, attempt_service=attempt_service)
        assert len(result) == 1
        assert result[0].id == "2"

    def test_created_before_exclusive(self, svc):
        """Test that created_before is exclusive (<)."""
        attempt_service = svc._attempt_service

        # run2 is created at exactly 2024-01-02 10:00:00, so it should NOT be included
        cutoff = datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
        result = svc.query(created_before=cutoff, attempt_service=attempt_service)
        assert len(result) == 1
        assert result[0].id == "1"


class TestAttemptsFilterHandling:
    """Test the attempts filtering logic."""

    def test_run_with_multiple_attempts(self, svc):
        """Test that a run with multiple attempts is correctly identified."""
        attempt_service = svc._attempt_service

        # Add another attempt to run2
        attempt2 = WorkflowRunAttempt(
            id=2,
            run_id=2,
            attempt_number=2,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 2, 11, 0, 0, tzinfo=CEST),
        )
        attempt_service.create(attempt2)

        # Should still find run2 with has_attempts=True
        result = svc.query(has_attempts=True, attempt_service=attempt_service)
        assert len(result) == 1
        assert result[0].id == "2"

    def test_invalid_run_id_for_attempt_lookup(self, svc):
        """Test handling of runs where id cannot be converted to int."""
        storage = MagicMock()
        # Create a run with non-numeric string ID
        non_numeric_run = _make_run(run_id="abc-123")
        storage.load.return_value = [non_numeric_run]

        svc_with_invalid = WorkflowRunService(storage)
        attempt_service = AttemptService()

        # Should skip the run gracefully
        result = svc_with_invalid.query(has_attempts=True, attempt_service=attempt_service)
        assert result == []


class TestNoFiltersApplied:
    """Test behavior when no filters are provided."""

    def test_no_filters_returns_all_runs(self, svc):
        """Test that query with no filters returns all runs."""
        attempt_service = svc._attempt_service
        result = svc.query(attempt_service=attempt_service)
        assert len(result) == 2
        run_ids = sorted([r.id for r in result])
        assert run_ids == ["1", "2"]

    def test_none_filters_are_no_op(self, svc):
        """Test that explicitly passing None for filters doesn't filter."""
        attempt_service = svc._attempt_service
        result = svc.query(
            min_duration=None,
            max_duration=None,
            created_after=None,
            created_before=None,
            has_attempts=None,
            attempt_service=attempt_service
        )
        assert len(result) == 2


class TestMultipleRunsWithVariedDurations:
    """Test with multiple runs of varied durations."""

    def test_three_runs_duration_filter(self):
        """Test filtering three runs with different durations."""
        storage = MagicMock()

        # Create three runs with different durations
        r1 = _make_run(run_id="1", duration_seconds=50.0)
        r2 = _make_run(run_id="2", duration_seconds=100.0)
        r3 = _make_run(run_id="3", duration_seconds=150.0)

        storage.load.return_value = [r1, r2, r3]
        svc = WorkflowRunService(storage)
        attempt_service = AttemptService()

        # Filter for 80-120 seconds
        result = svc.query(min_duration=80.0, max_duration=120.0, attempt_service=attempt_service)
        assert len(result) == 1
        assert result[0].id == "2"


class TestTimezoneHandling:
    """Test proper handling of timezone-aware datetimes."""

    def test_different_timezone_aware_datetimes(self):
        """Test that timezone-aware datetimes work correctly."""
        storage = MagicMock()

        # Create runs in different timezones
        utc_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        cest_dt = datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone(timedelta(hours=2)))

        r1 = _make_run(run_id="1", created_at=utc_dt)
        r2 = _make_run(run_id="2", created_at=cest_dt)

        storage.load.return_value = [r1, r2]
        svc = WorkflowRunService(storage)
        attempt_service = AttemptService()

        # Filter with UTC timezone
        cutoff = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        result = svc.query(created_after=cutoff, attempt_service=attempt_service)

        # CEST 14:00 is UTC 12:00, which is before 13:00 UTC, so should not be included
        assert len(result) == 0
