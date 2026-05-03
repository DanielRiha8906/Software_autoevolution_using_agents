"""
Comprehensive tests for the filtering interface in WorkflowRunService,
including CLI and interactive menu datetime parsing.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from src.models.workflow_run import WorkflowRun
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.services.workflow_run_attempt_service import WorkflowRunAttemptService
from src.cli.workflow_cli import _parse_datetime as cli_parse_datetime
from src.cli.interactive_menu import _parse_datetime as menu_parse_datetime


# ============================================================================
# FIXTURES
# ============================================================================

def _make_run(
    run_id: str = "run-1",
    branch: str = "main",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    created_at: datetime = None,
    duration_seconds: float = 0.0,
) -> WorkflowRun:
    """Create a test WorkflowRun with sensible defaults."""
    if created_at is None:
        created_at = datetime(2025, 5, 3, tzinfo=timezone.utc)
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch=branch,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def service():
    """Create a WorkflowRunService with empty storage."""
    storage = MagicMock()
    storage.load.return_value = []
    svc = WorkflowRunService(storage)
    return svc


@pytest.fixture
def attempt_service():
    """Create a WorkflowRunAttemptService with empty storage."""
    storage = MagicMock()
    storage.load_attempts.return_value = []
    svc = WorkflowRunAttemptService(storage)
    return svc


# ============================================================================
# TEST: filter_by_created_after
# ============================================================================

class TestFilterByCreatedAfter:
    """Test filter_by_created_after method."""

    def test_single_run_after_threshold(self, service):
        """Single run created after threshold should be included."""
        threshold = datetime(2025, 5, 1, tzinfo=timezone.utc)
        run = _make_run(created_at=datetime(2025, 5, 3, tzinfo=timezone.utc))
        service.add_workflow_run(run)

        result = service.filter_by_created_after(threshold)
        assert result == [run]

    def test_single_run_before_threshold(self, service):
        """Single run created before threshold should be excluded."""
        threshold = datetime(2025, 5, 10, tzinfo=timezone.utc)
        run = _make_run(created_at=datetime(2025, 5, 3, tzinfo=timezone.utc))
        service.add_workflow_run(run)

        result = service.filter_by_created_after(threshold)
        assert result == []

    def test_run_at_exact_threshold(self, service):
        """Run created at exact threshold should be included (>= logic)."""
        threshold = datetime(2025, 5, 3, 12, 0, 0, tzinfo=timezone.utc)
        run = _make_run(created_at=datetime(2025, 5, 3, 12, 0, 0, tzinfo=timezone.utc))
        service.add_workflow_run(run)

        result = service.filter_by_created_after(threshold)
        assert result == [run]

    def test_multiple_runs_mixed(self, service):
        """Multiple runs with some before, some after threshold."""
        threshold = datetime(2025, 5, 5, tzinfo=timezone.utc)
        r1 = _make_run("r1", created_at=datetime(2025, 5, 3, tzinfo=timezone.utc))
        r2 = _make_run("r2", created_at=datetime(2025, 5, 5, tzinfo=timezone.utc))
        r3 = _make_run("r3", created_at=datetime(2025, 5, 7, tzinfo=timezone.utc))

        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        result = service.filter_by_created_after(threshold)
        assert sorted([r.id for r in result]) == sorted(["r2", "r3"])

    def test_no_runs_match(self, service):
        """No runs match filter returns empty list."""
        threshold = datetime(2025, 5, 10, tzinfo=timezone.utc)
        run = _make_run(created_at=datetime(2025, 5, 3, tzinfo=timezone.utc))
        service.add_workflow_run(run)

        result = service.filter_by_created_after(threshold)
        assert result == []

    def test_empty_service(self, service):
        """Empty service returns empty list."""
        threshold = datetime(2025, 5, 1, tzinfo=timezone.utc)
        result = service.filter_by_created_after(threshold)
        assert result == []


# ============================================================================
# TEST: filter_by_created_before
# ============================================================================

class TestFilterByCreatedBefore:
    """Test filter_by_created_before method."""

    def test_single_run_before_threshold(self, service):
        """Single run created before threshold should be included."""
        threshold = datetime(2025, 5, 10, tzinfo=timezone.utc)
        run = _make_run(created_at=datetime(2025, 5, 3, tzinfo=timezone.utc))
        service.add_workflow_run(run)

        result = service.filter_by_created_before(threshold)
        assert result == [run]

    def test_single_run_after_threshold(self, service):
        """Single run created after threshold should be excluded."""
        threshold = datetime(2025, 5, 1, tzinfo=timezone.utc)
        run = _make_run(created_at=datetime(2025, 5, 3, tzinfo=timezone.utc))
        service.add_workflow_run(run)

        result = service.filter_by_created_before(threshold)
        assert result == []

    def test_run_at_exact_threshold(self, service):
        """Run created at exact threshold should be included (<= logic)."""
        threshold = datetime(2025, 5, 3, 12, 0, 0, tzinfo=timezone.utc)
        run = _make_run(created_at=datetime(2025, 5, 3, 12, 0, 0, tzinfo=timezone.utc))
        service.add_workflow_run(run)

        result = service.filter_by_created_before(threshold)
        assert result == [run]

    def test_multiple_runs_mixed(self, service):
        """Multiple runs with some before, some after threshold."""
        threshold = datetime(2025, 5, 5, tzinfo=timezone.utc)
        r1 = _make_run("r1", created_at=datetime(2025, 5, 3, tzinfo=timezone.utc))
        r2 = _make_run("r2", created_at=datetime(2025, 5, 5, tzinfo=timezone.utc))
        r3 = _make_run("r3", created_at=datetime(2025, 5, 7, tzinfo=timezone.utc))

        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        result = service.filter_by_created_before(threshold)
        assert sorted([r.id for r in result]) == sorted(["r1", "r2"])

    def test_no_runs_match(self, service):
        """No runs match filter returns empty list."""
        threshold = datetime(2025, 5, 1, tzinfo=timezone.utc)
        run = _make_run(created_at=datetime(2025, 5, 3, tzinfo=timezone.utc))
        service.add_workflow_run(run)

        result = service.filter_by_created_before(threshold)
        assert result == []

    def test_empty_service(self, service):
        """Empty service returns empty list."""
        threshold = datetime(2025, 5, 10, tzinfo=timezone.utc)
        result = service.filter_by_created_before(threshold)
        assert result == []


# ============================================================================
# TEST: filter_by_duration_min
# ============================================================================

class TestFilterByDurationMin:
    """Test filter_by_duration_min method."""

    @pytest.mark.parametrize("min_seconds,duration_seconds,should_match", [
        (100.0, 100.0, True),   # Exact match
        (100.0, 150.0, True),   # Exceeds minimum
        (100.0, 50.0, False),   # Below minimum
        (0.0, 0.0, True),       # Zero minimum, zero duration
        (0.0, 100.0, True),     # Zero minimum, positive duration
        (0.5, 0.5, True),       # Float exact match
        (0.5, 0.75, True),      # Float exceeds
        (0.5, 0.25, False),     # Float below
    ])
    def test_single_run_duration_variants(self, service, min_seconds, duration_seconds, should_match):
        """Test various duration comparisons."""
        run = _make_run(duration_seconds=duration_seconds)
        service.add_workflow_run(run)

        result = service.filter_by_duration_min(min_seconds)
        if should_match:
            assert result == [run]
        else:
            assert result == []

    def test_multiple_runs_mixed(self, service):
        """Multiple runs with varying durations."""
        r1 = _make_run("r1", duration_seconds=50.0)
        r2 = _make_run("r2", duration_seconds=100.0)
        r3 = _make_run("r3", duration_seconds=150.0)

        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        result = service.filter_by_duration_min(100.0)
        assert sorted([r.id for r in result]) == sorted(["r2", "r3"])

    def test_empty_service(self, service):
        """Empty service returns empty list."""
        result = service.filter_by_duration_min(100.0)
        assert result == []


# ============================================================================
# TEST: filter_by_duration_max
# ============================================================================

class TestFilterByDurationMax:
    """Test filter_by_duration_max method."""

    @pytest.mark.parametrize("max_seconds,duration_seconds,should_match", [
        (100.0, 100.0, True),   # Exact match
        (100.0, 50.0, True),    # Below maximum
        (100.0, 150.0, False),  # Exceeds maximum
        (0.0, 0.0, True),       # Zero maximum, zero duration
        (0.0, 100.0, False),    # Zero maximum, positive duration
        (0.5, 0.5, True),       # Float exact match
        (0.5, 0.25, True),      # Float below
        (0.5, 0.75, False),     # Float exceeds
    ])
    def test_single_run_duration_variants(self, service, max_seconds, duration_seconds, should_match):
        """Test various duration comparisons."""
        run = _make_run(duration_seconds=duration_seconds)
        service.add_workflow_run(run)

        result = service.filter_by_duration_max(max_seconds)
        if should_match:
            assert result == [run]
        else:
            assert result == []

    def test_multiple_runs_mixed(self, service):
        """Multiple runs with varying durations."""
        r1 = _make_run("r1", duration_seconds=50.0)
        r2 = _make_run("r2", duration_seconds=100.0)
        r3 = _make_run("r3", duration_seconds=150.0)

        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        result = service.filter_by_duration_max(100.0)
        assert sorted([r.id for r in result]) == sorted(["r1", "r2"])

    def test_empty_service(self, service):
        """Empty service returns empty list."""
        result = service.filter_by_duration_max(100.0)
        assert result == []


# ============================================================================
# TEST: filter_by_attempt_presence
# ============================================================================

class TestFilterByAttemptPresence:
    """Test filter_by_attempt_presence method."""

    def test_has_attempts_true_with_numeric_run_id(self, service, attempt_service):
        """Run with numeric ID and matching attempt should be included."""
        run = _make_run("123")  # Numeric string ID
        service.add_workflow_run(run)

        attempt = WorkflowRunAttempt(
            id=1,
            run_id=123,
            attempt_number=1,
            status="in-progress",
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            duration_seconds=0.0,
        )
        attempt_service.add_attempt(attempt)

        result = service.filter_by_attempt_presence(attempt_service, has_attempts=True)
        assert result == [run]

    def test_has_attempts_true_no_matching_attempt(self, service, attempt_service):
        """Run with numeric ID but no matching attempt should be excluded."""
        run = _make_run("123")
        service.add_workflow_run(run)

        # Add attempt for different run
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=456,
            attempt_number=1,
            status="in-progress",
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            duration_seconds=0.0,
        )
        attempt_service.add_attempt(attempt)

        result = service.filter_by_attempt_presence(attempt_service, has_attempts=True)
        assert result == []

    def test_has_attempts_false_no_attempt(self, service, attempt_service):
        """Run with no matching attempt should be included when has_attempts=False."""
        run = _make_run("123")
        service.add_workflow_run(run)

        # Add attempt for different run
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=456,
            attempt_number=1,
            status="in-progress",
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            duration_seconds=0.0,
        )
        attempt_service.add_attempt(attempt)

        result = service.filter_by_attempt_presence(attempt_service, has_attempts=False)
        assert result == [run]

    def test_has_attempts_false_with_attempt(self, service, attempt_service):
        """Run with matching attempt should be excluded when has_attempts=False."""
        run = _make_run("123")
        service.add_workflow_run(run)

        attempt = WorkflowRunAttempt(
            id=1,
            run_id=123,
            attempt_number=1,
            status="in-progress",
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            duration_seconds=0.0,
        )
        attempt_service.add_attempt(attempt)

        result = service.filter_by_attempt_presence(attempt_service, has_attempts=False)
        assert result == []

    def test_uuid_string_id_treated_as_no_attempts(self, service, attempt_service):
        """Run with UUID string ID should be treated as having no attempts."""
        run = _make_run("550e8400-e29b-41d4-a716-446655440000")  # UUID string
        service.add_workflow_run(run)

        attempt = WorkflowRunAttempt(
            id=1,
            run_id=123,
            attempt_number=1,
            status="in-progress",
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            duration_seconds=0.0,
        )
        attempt_service.add_attempt(attempt)

        # UUID cannot be converted to int, so it's treated as no attempts
        result = service.filter_by_attempt_presence(attempt_service, has_attempts=False)
        assert result == [run]

        result = service.filter_by_attempt_presence(attempt_service, has_attempts=True)
        assert result == []

    def test_non_numeric_string_id_treated_as_no_attempts(self, service, attempt_service):
        """Run with non-numeric string ID should be treated as having no attempts."""
        run = _make_run("run-abc")
        service.add_workflow_run(run)

        attempt = WorkflowRunAttempt(
            id=1,
            run_id=123,
            attempt_number=1,
            status="in-progress",
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            duration_seconds=0.0,
        )
        attempt_service.add_attempt(attempt)

        result = service.filter_by_attempt_presence(attempt_service, has_attempts=False)
        assert result == [run]

    def test_multiple_runs_mixed(self, service, attempt_service):
        """Multiple runs with some having attempts, some not."""
        r1 = _make_run("123")  # Has attempt
        r2 = _make_run("456")  # No attempt
        r3 = _make_run("789")  # No attempt

        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        attempt = WorkflowRunAttempt(
            id=1,
            run_id=123,
            attempt_number=1,
            status="in-progress",
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            duration_seconds=0.0,
        )
        attempt_service.add_attempt(attempt)

        result = service.filter_by_attempt_presence(attempt_service, has_attempts=True)
        assert result == [r1]

        result = service.filter_by_attempt_presence(attempt_service, has_attempts=False)
        assert sorted([r.id for r in result]) == sorted(["456", "789"])

    def test_empty_service(self, service, attempt_service):
        """Empty service returns empty list."""
        result = service.filter_by_attempt_presence(attempt_service, has_attempts=True)
        assert result == []

        result = service.filter_by_attempt_presence(attempt_service, has_attempts=False)
        assert result == []


# ============================================================================
# TEST: query method (composite filtering)
# ============================================================================

class TestQuery:
    """Test the composite query method with multiple filters."""

    def test_query_with_no_filters(self, service):
        """Query with no filters returns all runs."""
        r1 = _make_run("r1")
        r2 = _make_run("r2")
        service.add_workflow_run(r1)
        service.add_workflow_run(r2)

        result = service.query()
        assert sorted([r.id for r in result]) == sorted(["r1", "r2"])

    def test_query_created_after_and_before(self, service):
        """Query with both created_after and created_before (AND logic)."""
        r1 = _make_run("r1", created_at=datetime(2025, 5, 3, tzinfo=timezone.utc))
        r2 = _make_run("r2", created_at=datetime(2025, 5, 5, tzinfo=timezone.utc))
        r3 = _make_run("r3", created_at=datetime(2025, 5, 10, tzinfo=timezone.utc))

        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        result = service.query(
            created_after=datetime(2025, 5, 3, tzinfo=timezone.utc),
            created_before=datetime(2025, 5, 7, tzinfo=timezone.utc),
        )
        assert sorted([r.id for r in result]) == sorted(["r1", "r2"])

    def test_query_duration_min_and_max(self, service):
        """Query with both duration_min and duration_max (AND logic)."""
        r1 = _make_run("r1", duration_seconds=50.0)
        r2 = _make_run("r2", duration_seconds=100.0)
        r3 = _make_run("r3", duration_seconds=150.0)

        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        result = service.query(duration_min=75.0, duration_max=125.0)
        assert result == [r2]

    def test_query_branch_and_status(self, service):
        """Query with branch and status filters (AND logic)."""
        r1 = _make_run("r1", branch="main", status=WorkflowStatus.COMPLETED)
        r2 = _make_run("r2", branch="main", status=WorkflowStatus.IN_PROGRESS)
        r3 = _make_run("r3", branch="dev", status=WorkflowStatus.COMPLETED)

        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        result = service.query(branch="main", status=WorkflowStatus.COMPLETED)
        assert result == [r1]

    def test_query_all_filters_combined(self, service, attempt_service):
        """Query with all possible filters (AND logic)."""
        r1 = _make_run(
            "123",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime(2025, 5, 5, tzinfo=timezone.utc),
            duration_seconds=100.0,
        )
        r2 = _make_run(
            "456",
            branch="dev",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime(2025, 5, 5, tzinfo=timezone.utc),
            duration_seconds=100.0,
        )

        service.add_workflow_run(r1)
        service.add_workflow_run(r2)

        attempt = WorkflowRunAttempt(
            id=1,
            run_id=123,
            attempt_number=1,
            status="in-progress",
            conclusion=None,
            created_at=datetime.now(timezone.utc),
            duration_seconds=0.0,
        )
        attempt_service.add_attempt(attempt)

        result = service.query(
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_after=datetime(2025, 5, 1, tzinfo=timezone.utc),
            created_before=datetime(2025, 5, 10, tzinfo=timezone.utc),
            duration_min=50.0,
            duration_max=150.0,
            has_attempts=True,
            attempt_service=attempt_service,
        )
        assert result == [r1]

    def test_query_has_attempts_requires_service(self, service):
        """Query with has_attempts filter but no attempt_service raises ValueError."""
        r1 = _make_run("r1")
        service.add_workflow_run(r1)

        with pytest.raises(ValueError, match="attempt_service must be provided"):
            service.query(has_attempts=True, attempt_service=None)

    def test_query_has_attempts_with_none_filter(self, service, attempt_service):
        """Query with has_attempts=None does not require attempt_service."""
        r1 = _make_run("r1")
        service.add_workflow_run(r1)

        # Should not raise
        result = service.query(has_attempts=None, attempt_service=None)
        assert result == [r1]

    def test_query_no_filters_match(self, service):
        """Query that matches nothing returns empty list."""
        r1 = _make_run("r1", branch="main")
        service.add_workflow_run(r1)

        result = service.query(branch="nonexistent")
        assert result == []

    def test_query_filters_are_anded_not_ored(self, service):
        """Filters should AND together, not OR."""
        r1 = _make_run("r1", branch="main", status=WorkflowStatus.COMPLETED)
        r2 = _make_run("r2", branch="main", status=WorkflowStatus.IN_PROGRESS)
        r3 = _make_run("r3", branch="dev", status=WorkflowStatus.COMPLETED)

        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        # If ORed, we'd get r1, r2, r3. If ANDed, only r1.
        result = service.query(branch="main", status=WorkflowStatus.COMPLETED)
        assert result == [r1]


# ============================================================================
# TEST: _parse_datetime in workflow_cli.py
# ============================================================================

class TestCliParseDateTime:
    """Test _parse_datetime in workflow_cli.py."""

    def test_iso_format_with_timezone(self):
        """Parse ISO format with timezone."""
        result = cli_parse_datetime("2025-05-03T10:30:00+00:00")
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 3
        assert result.hour == 10
        assert result.minute == 30
        assert result.tzinfo is not None

    def test_iso_format_without_timezone(self):
        """Parse ISO format without timezone; should add UTC."""
        result = cli_parse_datetime("2025-05-03T10:30:00")
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 3
        assert result.hour == 10
        assert result.minute == 30
        assert result.tzinfo == timezone.utc

    def test_yyyy_mm_dd_format(self):
        """Parse YYYY-MM-DD format."""
        result = cli_parse_datetime("2025-05-03")
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 3
        assert result.hour == 0
        assert result.minute == 0
        assert result.tzinfo == timezone.utc

    def test_invalid_format_raises(self):
        """Invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="Could not parse date"):
            cli_parse_datetime("invalid-date")

    def test_invalid_date_values_raises(self):
        """Invalid date values raise ValueError."""
        with pytest.raises(ValueError, match="Could not parse date"):
            cli_parse_datetime("2025-13-45")

    def test_iso_with_seconds_fraction(self):
        """Parse ISO format with fractional seconds."""
        result = cli_parse_datetime("2025-05-03T10:30:00.123456")
        assert result.microsecond == 123456

    def test_empty_string_raises(self):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="Could not parse date"):
            cli_parse_datetime("")

    def test_partial_iso_date_only(self):
        """Partial ISO with only date (no time) should work."""
        result = cli_parse_datetime("2025-05-03")
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 3


# ============================================================================
# TEST: _parse_datetime in interactive_menu.py
# ============================================================================

class TestMenuParseDateTime:
    """Test _parse_datetime in interactive_menu.py."""

    def test_iso_format_with_timezone(self):
        """Parse ISO format with timezone."""
        result = menu_parse_datetime("2025-05-03T10:30:00+00:00")
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 3
        assert result.hour == 10
        assert result.minute == 30
        assert result.tzinfo is not None

    def test_iso_format_without_timezone(self):
        """Parse ISO format without timezone; should add UTC."""
        result = menu_parse_datetime("2025-05-03T10:30:00")
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 3
        assert result.hour == 10
        assert result.minute == 30
        assert result.tzinfo == timezone.utc

    def test_yyyy_mm_dd_format(self):
        """Parse YYYY-MM-DD format."""
        result = menu_parse_datetime("2025-05-03")
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 3
        assert result.hour == 0
        assert result.minute == 0
        assert result.tzinfo == timezone.utc

    def test_invalid_format_raises(self):
        """Invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="Could not parse date"):
            menu_parse_datetime("invalid-date")

    def test_invalid_date_values_raises(self):
        """Invalid date values raise ValueError."""
        with pytest.raises(ValueError, match="Could not parse date"):
            menu_parse_datetime("2025-13-45")

    def test_iso_with_seconds_fraction(self):
        """Parse ISO format with fractional seconds."""
        result = menu_parse_datetime("2025-05-03T10:30:00.123456")
        assert result.microsecond == 123456

    def test_empty_string_raises(self):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="Could not parse date"):
            menu_parse_datetime("")

    def test_partial_iso_date_only(self):
        """Partial ISO with only date (no time) should work."""
        result = menu_parse_datetime("2025-05-03")
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 3


# ============================================================================
# TEST: Edge cases and boundary conditions
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions across all filters."""

    def test_duration_boundary_zero(self, service):
        """Duration at zero boundary."""
        r1 = _make_run("r1", duration_seconds=0.0)
        service.add_workflow_run(r1)

        # Should include at 0
        assert service.filter_by_duration_min(0.0) == [r1]
        assert service.filter_by_duration_max(0.0) == [r1]

        # Should exclude above 0
        assert service.filter_by_duration_min(0.1) == []
        assert service.filter_by_duration_max(-0.1) == []

    def test_very_large_duration(self, service):
        """Very large duration values."""
        r1 = _make_run("r1", duration_seconds=1_000_000.0)
        service.add_workflow_run(r1)

        assert service.filter_by_duration_min(999_999.0) == [r1]
        assert service.filter_by_duration_max(1_000_001.0) == [r1]

    def test_very_small_float_duration(self, service):
        """Very small float durations."""
        r1 = _make_run("r1", duration_seconds=0.0001)
        service.add_workflow_run(r1)

        assert service.filter_by_duration_min(0.0001) == [r1]
        assert service.filter_by_duration_max(0.0001) == [r1]

    def test_many_runs_same_created_at(self, service):
        """Multiple runs with same created_at timestamp."""
        timestamp = datetime(2025, 5, 5, 12, 0, 0, tzinfo=timezone.utc)
        r1 = _make_run("r1", created_at=timestamp)
        r2 = _make_run("r2", created_at=timestamp)
        r3 = _make_run("r3", created_at=timestamp)

        service.add_workflow_run(r1)
        service.add_workflow_run(r2)
        service.add_workflow_run(r3)

        result = service.filter_by_created_after(timestamp)
        assert sorted([r.id for r in result]) == sorted(["r1", "r2", "r3"])

    def test_microsecond_precision_boundary(self, service):
        """Boundary at microsecond precision."""
        base = datetime(2025, 5, 5, 12, 0, 0, tzinfo=timezone.utc)
        r1 = _make_run("r1", created_at=base)
        r2 = _make_run("r2", created_at=base.replace(microsecond=1))

        service.add_workflow_run(r1)
        service.add_workflow_run(r2)

        # Should include both (>= logic)
        result = service.filter_by_created_after(base)
        assert sorted([r.id for r in result]) == sorted(["r1", "r2"])

    def test_negative_duration_in_creation_raises(self):
        """Creating a run with negative duration raises ValueError."""
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            _make_run(duration_seconds=-1.0)
