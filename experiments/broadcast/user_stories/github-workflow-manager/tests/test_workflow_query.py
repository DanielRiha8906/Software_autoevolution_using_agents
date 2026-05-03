import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_query import WorkflowQuery, DurationRange, TimestampRange


def _make_run(
    run_id: str = "run-1",
    workflow_name: str = "CI",
    branch: str = "main",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    created_at: datetime = None,
    updated_at: datetime = None,
) -> WorkflowRun:
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    return WorkflowRun(
        id=run_id,
        workflow_name=workflow_name,
        branch=branch,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        updated_at=updated_at,
        run_number=1,
        commit_sha="abc123",
    )


class TestDurationRangeFilter:
    def test_filter_by_duration_min_only(self):
        """Test filtering with only minimum duration."""
        base_time = datetime.now(timezone.utc)
        runs = [
            _make_run("r1", created_at=base_time, updated_at=base_time + timedelta(seconds=10)),
            _make_run("r2", created_at=base_time, updated_at=base_time + timedelta(seconds=50)),
            _make_run("r3", created_at=base_time, updated_at=base_time + timedelta(seconds=100)),
        ]
        query = WorkflowQuery(runs)
        result = query.filter_by_duration(min_seconds=30)
        assert len(result) == 2
        assert result[0].id == "r2"
        assert result[1].id == "r3"

    def test_filter_by_duration_max_only(self):
        """Test filtering with only maximum duration."""
        base_time = datetime.now(timezone.utc)
        runs = [
            _make_run("r1", created_at=base_time, updated_at=base_time + timedelta(seconds=10)),
            _make_run("r2", created_at=base_time, updated_at=base_time + timedelta(seconds=50)),
            _make_run("r3", created_at=base_time, updated_at=base_time + timedelta(seconds=100)),
        ]
        query = WorkflowQuery(runs)
        result = query.filter_by_duration(max_seconds=60)
        assert len(result) == 2
        assert result[0].id == "r1"
        assert result[1].id == "r2"

    def test_filter_by_duration_min_and_max(self):
        """Test filtering with both minimum and maximum duration."""
        base_time = datetime.now(timezone.utc)
        runs = [
            _make_run("r1", created_at=base_time, updated_at=base_time + timedelta(seconds=10)),
            _make_run("r2", created_at=base_time, updated_at=base_time + timedelta(seconds=50)),
            _make_run("r3", created_at=base_time, updated_at=base_time + timedelta(seconds=100)),
        ]
        query = WorkflowQuery(runs)
        result = query.filter_by_duration(min_seconds=30, max_seconds=70)
        assert len(result) == 1
        assert result[0].id == "r2"

    def test_filter_by_duration_excludes_runs_without_updated_at(self):
        """Test that runs without updated_at are excluded."""
        base_time = datetime.now(timezone.utc)
        runs = [
            _make_run("r1", created_at=base_time, updated_at=base_time + timedelta(seconds=50)),
            _make_run("r2", created_at=base_time, updated_at=None),
        ]
        query = WorkflowQuery(runs)
        result = query.filter_by_duration(min_seconds=0)
        assert len(result) == 1
        assert result[0].id == "r1"

    def test_filter_by_duration_boundary_inclusive(self):
        """Test that boundaries are inclusive."""
        base_time = datetime.now(timezone.utc)
        runs = [
            _make_run("r1", created_at=base_time, updated_at=base_time + timedelta(seconds=10)),
            _make_run("r2", created_at=base_time, updated_at=base_time + timedelta(seconds=50)),
            _make_run("r3", created_at=base_time, updated_at=base_time + timedelta(seconds=100)),
        ]
        query = WorkflowQuery(runs)
        result = query.filter_by_duration(min_seconds=50, max_seconds=50)
        assert len(result) == 1
        assert result[0].id == "r2"

    def test_filter_by_duration_negative_min_raises(self):
        """Test that negative min_seconds raises ValueError."""
        runs = [_make_run()]
        query = WorkflowQuery(runs)
        with pytest.raises(ValueError, match="min_seconds must be non-negative"):
            query.filter_by_duration(min_seconds=-10)

    def test_filter_by_duration_negative_max_raises(self):
        """Test that negative max_seconds raises ValueError."""
        runs = [_make_run()]
        query = WorkflowQuery(runs)
        with pytest.raises(ValueError, match="max_seconds must be non-negative"):
            query.filter_by_duration(max_seconds=-10)

    def test_filter_by_duration_min_greater_than_max_raises(self):
        """Test that min_seconds > max_seconds raises ValueError."""
        runs = [_make_run()]
        query = WorkflowQuery(runs)
        with pytest.raises(ValueError, match="min_seconds .* cannot be greater than max_seconds"):
            query.filter_by_duration(min_seconds=100, max_seconds=50)

    def test_filter_by_duration_empty_result(self):
        """Test filtering with no matches."""
        base_time = datetime.now(timezone.utc)
        runs = [
            _make_run("r1", created_at=base_time, updated_at=base_time + timedelta(seconds=10)),
        ]
        query = WorkflowQuery(runs)
        result = query.filter_by_duration(min_seconds=100)
        assert len(result) == 0


class TestTimestampRangeFilter:
    def test_filter_by_timestamp_before(self):
        """Test filtering with only before timestamp."""
        base_time = datetime.now(timezone.utc)
        t1 = base_time
        t2 = base_time + timedelta(hours=1)
        t3 = base_time + timedelta(hours=2)
        runs = [
            _make_run("r1", created_at=t1),
            _make_run("r2", created_at=t2),
            _make_run("r3", created_at=t3),
        ]
        query = WorkflowQuery(runs)
        cutoff = t2 + timedelta(minutes=30)
        result = query.filter_by_timestamp(before=cutoff)
        assert len(result) == 2
        assert result[0].id == "r1"
        assert result[1].id == "r2"

    def test_filter_by_timestamp_after(self):
        """Test filtering with only after timestamp."""
        base_time = datetime.now(timezone.utc)
        t1 = base_time
        t2 = base_time + timedelta(hours=1)
        t3 = base_time + timedelta(hours=2)
        runs = [
            _make_run("r1", created_at=t1),
            _make_run("r2", created_at=t2),
            _make_run("r3", created_at=t3),
        ]
        query = WorkflowQuery(runs)
        cutoff = t2 - timedelta(minutes=30)
        result = query.filter_by_timestamp(after=cutoff)
        assert len(result) == 2
        assert result[0].id == "r2"
        assert result[1].id == "r3"

    def test_filter_by_timestamp_before_and_after(self):
        """Test filtering with both before and after timestamps."""
        base_time = datetime.now(timezone.utc)
        t1 = base_time
        t2 = base_time + timedelta(hours=1)
        t3 = base_time + timedelta(hours=2)
        runs = [
            _make_run("r1", created_at=t1),
            _make_run("r2", created_at=t2),
            _make_run("r3", created_at=t3),
        ]
        query = WorkflowQuery(runs)
        before_cutoff = t3 - timedelta(minutes=30)
        after_cutoff = t1 + timedelta(minutes=30)
        result = query.filter_by_timestamp(before=before_cutoff, after=after_cutoff)
        assert len(result) == 1
        assert result[0].id == "r2"

    def test_filter_by_timestamp_boundary_exclusive(self):
        """Test that boundaries are exclusive."""
        base_time = datetime.now(timezone.utc)
        t1 = base_time
        t2 = base_time + timedelta(hours=1)
        runs = [
            _make_run("r1", created_at=t1),
            _make_run("r2", created_at=t2),
        ]
        query = WorkflowQuery(runs)
        # Exact match should be excluded
        result = query.filter_by_timestamp(before=t1)
        assert len(result) == 0
        result = query.filter_by_timestamp(after=t2)
        assert len(result) == 0

    def test_filter_by_timestamp_before_after_raises(self):
        """Test that before <= after raises ValueError."""
        base_time = datetime.now(timezone.utc)
        t1 = base_time
        t2 = base_time + timedelta(hours=1)
        runs = [_make_run()]
        query = WorkflowQuery(runs)
        with pytest.raises(ValueError, match="before .* must be greater than after"):
            query.filter_by_timestamp(before=t1, after=t2)

    def test_filter_by_timestamp_empty_result(self):
        """Test filtering with no matches."""
        base_time = datetime.now(timezone.utc)
        runs = [_make_run(created_at=base_time)]
        query = WorkflowQuery(runs)
        future = base_time + timedelta(hours=1)
        with pytest.raises(ValueError):
            query.filter_by_timestamp(before=future, after=future)


class TestAttemptPresenceFilter:
    def test_filter_by_attempt_presence_has_attempts(self):
        """Test filtering for runs with attempts."""
        runs = [
            _make_run("r1"),
            _make_run("r2"),
            _make_run("r3"),
        ]
        attempt_service = MagicMock()
        attempt_service.get_attempts_for_run.side_effect = lambda run_id: {
            "r1": [{"id": 1}],  # r1 has 1 attempt
            "r2": [],           # r2 has 0 attempts
            "r3": [{"id": 2}],  # r3 has 1 attempt
        }.get(str(run_id), [])

        query = WorkflowQuery(runs, attempt_service)
        result = query.filter_by_attempt_presence(has_attempts=True)
        assert len(result) == 2
        assert result[0].id == "r1"
        assert result[1].id == "r3"

    def test_filter_by_attempt_presence_no_attempts(self):
        """Test filtering for runs without attempts."""
        runs = [
            _make_run("r1"),
            _make_run("r2"),
            _make_run("r3"),
        ]
        attempt_service = MagicMock()
        attempt_service.get_attempts_for_run.side_effect = lambda run_id: {
            "r1": [{"id": 1}],  # r1 has 1 attempt
            "r2": [],           # r2 has 0 attempts
            "r3": [],           # r3 has 0 attempts
        }.get(str(run_id), [])

        query = WorkflowQuery(runs, attempt_service)
        result = query.filter_by_attempt_presence(has_attempts=False)
        assert len(result) == 2
        assert result[0].id == "r2"
        assert result[1].id == "r3"

    def test_filter_by_attempt_presence_without_service_raises(self):
        """Test that filtering without attempt_service raises ValueError."""
        runs = [_make_run()]
        query = WorkflowQuery(runs)  # No attempt_service
        with pytest.raises(ValueError, match="attempt_service is required"):
            query.filter_by_attempt_presence(has_attempts=True)


class TestCombinedQuery:
    def test_query_duration_only(self):
        """Test combined query with only duration filter."""
        base_time = datetime.now(timezone.utc)
        runs = [
            _make_run("r1", created_at=base_time, updated_at=base_time + timedelta(seconds=10)),
            _make_run("r2", created_at=base_time, updated_at=base_time + timedelta(seconds=50)),
            _make_run("r3", created_at=base_time, updated_at=base_time + timedelta(seconds=100)),
        ]
        query = WorkflowQuery(runs)
        result = query.query(
            duration_range=DurationRange(min_seconds=30, max_seconds=70)
        )
        assert len(result) == 1
        assert result[0].id == "r2"

    def test_query_timestamp_only(self):
        """Test combined query with only timestamp filter."""
        base_time = datetime.now(timezone.utc)
        t1 = base_time
        t2 = base_time + timedelta(hours=1)
        t3 = base_time + timedelta(hours=2)
        runs = [
            _make_run("r1", created_at=t1),
            _make_run("r2", created_at=t2),
            _make_run("r3", created_at=t3),
        ]
        query = WorkflowQuery(runs)
        before_cutoff = t3 - timedelta(minutes=30)
        after_cutoff = t1 + timedelta(minutes=30)
        result = query.query(
            timestamp_range=TimestampRange(before=before_cutoff, after=after_cutoff)
        )
        assert len(result) == 1
        assert result[0].id == "r2"

    def test_query_attempt_presence_only(self):
        """Test combined query with only attempt presence filter."""
        runs = [
            _make_run("r1"),
            _make_run("r2"),
            _make_run("r3"),
        ]
        attempt_service = MagicMock()
        attempt_service.get_attempts_for_run.side_effect = lambda run_id: {
            "r1": [{"id": 1}],
            "r2": [],
            "r3": [{"id": 2}],
        }.get(str(run_id), [])

        query = WorkflowQuery(runs, attempt_service)
        result = query.query(has_attempts=True)
        assert len(result) == 2
        assert result[0].id == "r1"
        assert result[1].id == "r3"

    def test_query_all_filters_combined(self):
        """Test combined query with all filters."""
        base_time = datetime.now(timezone.utc)
        t1 = base_time
        t2 = base_time + timedelta(hours=1)
        t3 = base_time + timedelta(hours=2)
        runs = [
            _make_run("r1", created_at=t1, updated_at=t1 + timedelta(seconds=10)),
            _make_run("r2", created_at=t2, updated_at=t2 + timedelta(seconds=50)),
            _make_run("r3", created_at=t3, updated_at=t3 + timedelta(seconds=100)),
        ]
        attempt_service = MagicMock()
        attempt_service.get_attempts_for_run.side_effect = lambda run_id: {
            "r1": [{"id": 1}],
            "r2": [{"id": 2}],
            "r3": [],
        }.get(str(run_id), [])

        query = WorkflowQuery(runs, attempt_service)
        before_cutoff = t3 - timedelta(minutes=30)
        after_cutoff = t1 + timedelta(minutes=30)
        result = query.query(
            duration_range=DurationRange(min_seconds=30, max_seconds=70),
            timestamp_range=TimestampRange(before=before_cutoff, after=after_cutoff),
            has_attempts=True
        )
        # Only r2 matches: in time range, has duration 50, has attempts
        assert len(result) == 1
        assert result[0].id == "r2"

    def test_query_no_filters(self):
        """Test combined query with no filters returns all runs."""
        runs = [
            _make_run("r1"),
            _make_run("r2"),
            _make_run("r3"),
        ]
        query = WorkflowQuery(runs)
        result = query.query()
        assert len(result) == 3

    def test_query_conflicting_filters_no_results(self):
        """Test combined query where filters conflict."""
        base_time = datetime.now(timezone.utc)
        runs = [
            _make_run("r1", created_at=base_time, updated_at=base_time + timedelta(seconds=10)),
        ]
        query = WorkflowQuery(runs)
        result = query.query(
            duration_range=DurationRange(min_seconds=100, max_seconds=200)
        )
        assert len(result) == 0

    def test_query_creates_new_list(self):
        """Test that query returns a new list, not a reference to original."""
        runs = [_make_run("r1")]
        query = WorkflowQuery(runs)
        result = query.query()
        assert result is not runs
        assert result == runs


class TestDurationRangeDataclass:
    def test_duration_range_creation(self):
        """Test DurationRange dataclass creation."""
        dr = DurationRange(min_seconds=10, max_seconds=100)
        assert dr.min_seconds == 10
        assert dr.max_seconds == 100

    def test_duration_range_partial(self):
        """Test DurationRange with partial data."""
        dr = DurationRange(min_seconds=10)
        assert dr.min_seconds == 10
        assert dr.max_seconds is None


class TestTimestampRangeDataclass:
    def test_timestamp_range_creation(self):
        """Test TimestampRange dataclass creation."""
        t1 = datetime.now(timezone.utc)
        t2 = t1 + timedelta(hours=1)
        tr = TimestampRange(before=t2, after=t1)
        assert tr.before == t2
        assert tr.after == t1

    def test_timestamp_range_partial(self):
        """Test TimestampRange with partial data."""
        t1 = datetime.now(timezone.utc)
        tr = TimestampRange(before=t1)
        assert tr.before == t1
        assert tr.after is None
