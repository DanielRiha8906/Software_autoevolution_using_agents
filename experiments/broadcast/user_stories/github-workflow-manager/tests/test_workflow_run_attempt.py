import pytest
from datetime import datetime, timezone, timedelta

from src.models.workflow_run_attempt import WorkflowRunAttempt


def _make_attempt(
    attempt_id: int = 1,
    run_id: int = 100,
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
    created_at: datetime = None,
    duration_seconds: float = 10.5,
) -> WorkflowRunAttempt:
    """Helper to create a WorkflowRunAttempt instance."""
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        duration_seconds=duration_seconds,
    )


class TestWorkflowRunAttemptCreation:
    """Tests for creating WorkflowRunAttempt instances."""

    def test_create_with_all_fields(self):
        """Test creating an attempt with all required fields."""
        created_at = datetime(2026, 5, 2, 10, 0, 0, tzinfo=timezone.utc)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=created_at,
            duration_seconds=15.5,
        )
        assert attempt.id == 1
        assert attempt.run_id == 100
        assert attempt.attempt_number == 1
        assert attempt.status == "completed"
        assert attempt.conclusion == "success"
        assert attempt.created_at == created_at
        assert attempt.duration_seconds == 15.5

    def test_create_with_optional_conclusion_none(self):
        """Test creating an attempt with conclusion=None."""
        attempt = _make_attempt(conclusion=None)
        assert attempt.conclusion is None

    def test_create_with_default_duration(self):
        """Test that duration_seconds defaults to 0.0."""
        created_at = datetime.now(timezone.utc)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="in_progress",
            conclusion=None,
            created_at=created_at,
        )
        assert attempt.duration_seconds == 0.0


class TestWorkflowRunAttemptValidation:
    """Tests for validation in __post_init__."""

    def test_attempt_number_must_be_positive(self):
        """Test that attempt_number must be >= 1."""
        with pytest.raises(ValueError, match="attempt_number must be a positive integer >= 1"):
            _make_attempt(attempt_number=0)

    def test_attempt_number_negative_raises(self):
        """Test that negative attempt_number raises ValueError."""
        with pytest.raises(ValueError, match="attempt_number must be a positive integer >= 1"):
            _make_attempt(attempt_number=-1)

    def test_attempt_number_one_is_valid(self):
        """Test that attempt_number=1 is valid."""
        attempt = _make_attempt(attempt_number=1)
        assert attempt.attempt_number == 1

    def test_attempt_number_large_value_is_valid(self):
        """Test that large attempt_number values are valid."""
        attempt = _make_attempt(attempt_number=100)
        assert attempt.attempt_number == 100

    def test_duration_seconds_cannot_be_negative(self):
        """Test that duration_seconds cannot be negative."""
        with pytest.raises(ValueError, match="duration_seconds cannot be negative"):
            _make_attempt(duration_seconds=-0.1)

    def test_duration_seconds_zero_is_valid(self):
        """Test that duration_seconds=0.0 is valid."""
        attempt = _make_attempt(duration_seconds=0.0)
        assert attempt.duration_seconds == 0.0

    def test_duration_seconds_large_value_is_valid(self):
        """Test that large duration_seconds values are valid."""
        attempt = _make_attempt(duration_seconds=3600.5)
        assert attempt.duration_seconds == 3600.5


class TestWorkflowRunAttemptAssociation:
    """Tests for parent WorkflowRun association."""

    def test_attempt_has_run_id(self):
        """Test that attempt stores its parent run_id."""
        attempt = _make_attempt(run_id=200)
        assert attempt.run_id == 200

    def test_multiple_attempts_same_run_id(self):
        """Test that multiple attempts can share the same run_id."""
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        assert attempt1.run_id == attempt2.run_id == 100
        assert attempt1.attempt_number != attempt2.attempt_number

    def test_uniqueness_tuple_run_id_attempt_number(self):
        """Test that (run_id, attempt_number) identifies a unique attempt."""
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        # Both have same run_id, different attempt_numbers
        assert (attempt1.run_id, attempt1.attempt_number) != (attempt2.run_id, attempt2.attempt_number)


class TestWorkflowRunAttemptSerialization:
    """Tests for JSON serialization and deserialization."""

    def test_to_dict_with_all_fields(self):
        """Test serializing an attempt to a dictionary."""
        created_at = datetime(2026, 5, 2, 10, 30, 45, tzinfo=timezone.utc)
        attempt = _make_attempt(
            attempt_id=5,
            run_id=200,
            attempt_number=2,
            status="completed",
            conclusion="failure",
            created_at=created_at,
            duration_seconds=42.7,
        )
        result = attempt.to_dict()
        assert result == {
            "id": 5,
            "run_id": 200,
            "attempt_number": 2,
            "status": "completed",
            "conclusion": "failure",
            "created_at": "2026-05-02T10:30:45+00:00",
            "duration_seconds": 42.7,
        }

    def test_to_dict_with_none_conclusion(self):
        """Test serializing an attempt with conclusion=None."""
        created_at = datetime(2026, 5, 2, 10, 0, 0, tzinfo=timezone.utc)
        attempt = _make_attempt(
            conclusion=None,
            created_at=created_at,
        )
        result = attempt.to_dict()
        assert result["conclusion"] is None

    def test_to_dict_preserves_all_fields(self):
        """Test that to_dict includes all fields."""
        attempt = _make_attempt()
        result = attempt.to_dict()
        assert "id" in result
        assert "run_id" in result
        assert "attempt_number" in result
        assert "status" in result
        assert "conclusion" in result
        assert "created_at" in result
        assert "duration_seconds" in result

    def test_from_dict_with_all_fields(self):
        """Test deserializing an attempt from a dictionary."""
        data = {
            "id": 7,
            "run_id": 300,
            "attempt_number": 3,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2026-05-02T14:45:30+00:00",
            "duration_seconds": 25.3,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.id == 7
        assert attempt.run_id == 300
        assert attempt.attempt_number == 3
        assert attempt.status == "completed"
        assert attempt.conclusion == "success"
        assert attempt.created_at == datetime.fromisoformat("2026-05-02T14:45:30+00:00")
        assert attempt.duration_seconds == 25.3

    def test_from_dict_with_none_conclusion(self):
        """Test deserializing an attempt with conclusion=None."""
        data = {
            "id": 8,
            "run_id": 400,
            "attempt_number": 1,
            "status": "in_progress",
            "conclusion": None,
            "created_at": "2026-05-02T12:00:00+00:00",
            "duration_seconds": 0.0,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.conclusion is None

    def test_from_dict_without_conclusion_key(self):
        """Test deserializing when conclusion key is missing."""
        data = {
            "id": 9,
            "run_id": 500,
            "attempt_number": 1,
            "status": "queued",
            "created_at": "2026-05-02T12:00:00+00:00",
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.conclusion is None

    def test_from_dict_without_duration_seconds_key(self):
        """Test deserializing when duration_seconds key is missing."""
        data = {
            "id": 10,
            "run_id": 600,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2026-05-02T12:00:00+00:00",
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.duration_seconds == 0.0

    def test_roundtrip_serialization(self):
        """Test that an attempt can be serialized and deserialized."""
        original = _make_attempt(
            attempt_id=11,
            run_id=700,
            attempt_number=4,
            status="completed",
            conclusion="cancelled",
            duration_seconds=18.2,
        )
        data = original.to_dict()
        restored = WorkflowRunAttempt.from_dict(data)
        assert restored.id == original.id
        assert restored.run_id == original.run_id
        assert restored.attempt_number == original.attempt_number
        assert restored.status == original.status
        assert restored.conclusion == original.conclusion
        assert restored.created_at == original.created_at
        assert restored.duration_seconds == original.duration_seconds


class TestWorkflowRunAttemptCEST:
    """Tests for CEST (UTC+2) timezone handling."""

    def test_created_at_with_utc_timezone(self):
        """Test that created_at can store UTC timezone."""
        created_at = datetime(2026, 5, 2, 12, 0, 0, tzinfo=timezone.utc)
        attempt = _make_attempt(created_at=created_at)
        assert attempt.created_at.tzinfo == timezone.utc

    def test_created_at_with_cest_offset(self):
        """Test that created_at can store CEST (UTC+2) timezone."""
        cest_tz = timezone(timedelta(hours=2))
        created_at = datetime(2026, 5, 2, 14, 0, 0, tzinfo=cest_tz)
        attempt = _make_attempt(created_at=created_at)
        assert attempt.created_at.tzinfo == cest_tz

    def test_created_at_serialization_preserves_timezone(self):
        """Test that serialization preserves timezone information."""
        cest_tz = timezone(timedelta(hours=2))
        created_at = datetime(2026, 5, 2, 14, 30, 0, tzinfo=cest_tz)
        attempt = _make_attempt(created_at=created_at)
        data = attempt.to_dict()
        # isoformat() should include +02:00 offset
        assert "+02:00" in data["created_at"]

    def test_created_at_deserialization_preserves_timezone(self):
        """Test that deserialization preserves timezone information."""
        data = {
            "id": 12,
            "run_id": 800,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2026-05-02T14:30:00+02:00",
            "duration_seconds": 10.0,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.created_at.utcoffset() == timedelta(hours=2)


class TestWorkflowRunAttemptAttributes:
    """Tests for attribute types and values."""

    def test_id_is_int(self):
        """Test that id is an integer."""
        attempt = _make_attempt(attempt_id=123)
        assert isinstance(attempt.id, int)
        assert attempt.id == 123

    def test_run_id_is_int(self):
        """Test that run_id is an integer."""
        attempt = _make_attempt(run_id=456)
        assert isinstance(attempt.run_id, int)
        assert attempt.run_id == 456

    def test_attempt_number_is_int(self):
        """Test that attempt_number is an integer."""
        attempt = _make_attempt(attempt_number=5)
        assert isinstance(attempt.attempt_number, int)
        assert attempt.attempt_number == 5

    def test_status_is_string(self):
        """Test that status is a string."""
        attempt = _make_attempt(status="in_progress")
        assert isinstance(attempt.status, str)
        assert attempt.status == "in_progress"

    def test_conclusion_is_optional_string(self):
        """Test that conclusion is either a string or None."""
        attempt_with_conclusion = _make_attempt(conclusion="success")
        assert attempt_with_conclusion.conclusion is not None
        assert isinstance(attempt_with_conclusion.conclusion, str)

        attempt_without_conclusion = _make_attempt(conclusion=None)
        assert attempt_without_conclusion.conclusion is None

    def test_created_at_is_datetime(self):
        """Test that created_at is a datetime instance."""
        created_at = datetime(2026, 5, 2, 10, 0, 0, tzinfo=timezone.utc)
        attempt = _make_attempt(created_at=created_at)
        assert isinstance(attempt.created_at, datetime)
        assert attempt.created_at == created_at

    def test_duration_seconds_is_float(self):
        """Test that duration_seconds is a float."""
        attempt = _make_attempt(duration_seconds=10.5)
        assert isinstance(attempt.duration_seconds, float)
        assert attempt.duration_seconds == 10.5


class TestWorkflowRunAttemptEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_large_id(self):
        """Test with very large id values."""
        attempt = _make_attempt(attempt_id=9999999999)
        assert attempt.id == 9999999999

    def test_very_large_run_id(self):
        """Test with very large run_id values."""
        attempt = _make_attempt(run_id=9999999999)
        assert attempt.run_id == 9999999999

    def test_very_large_attempt_number(self):
        """Test with very large attempt_number values."""
        attempt = _make_attempt(attempt_number=1000)
        assert attempt.attempt_number == 1000

    def test_very_large_duration_seconds(self):
        """Test with very large duration_seconds values (e.g., hours)."""
        attempt = _make_attempt(duration_seconds=86400.5)  # More than a day
        assert attempt.duration_seconds == 86400.5

    def test_status_with_various_values(self):
        """Test status field with various string values."""
        statuses = ["queued", "in_progress", "completed", "waiting", "custom_status"]
        for status_value in statuses:
            attempt = _make_attempt(status=status_value)
            assert attempt.status == status_value

    def test_conclusion_with_various_values(self):
        """Test conclusion field with various string values."""
        conclusions = ["success", "failure", "cancelled", "skipped", None]
        for conclusion_value in conclusions:
            attempt = _make_attempt(conclusion=conclusion_value)
            assert attempt.conclusion == conclusion_value

    def test_empty_string_status(self):
        """Test that status can be an empty string (though not recommended)."""
        attempt = _make_attempt(status="")
        assert attempt.status == ""

    def test_empty_string_conclusion(self):
        """Test that conclusion can be an empty string (though not recommended)."""
        attempt = _make_attempt(conclusion="")
        assert attempt.conclusion == ""

    def test_from_dict_with_extra_fields(self):
        """Test that from_dict ignores extra fields."""
        data = {
            "id": 13,
            "run_id": 900,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2026-05-02T12:00:00+00:00",
            "duration_seconds": 10.0,
            "extra_field": "should_be_ignored",
            "another_extra": 123,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.id == 13
        assert not hasattr(attempt, "extra_field")
        assert not hasattr(attempt, "another_extra")
