import pytest
from datetime import datetime, timezone, timedelta

from src.models.workflow_run_attempt import WorkflowRunAttempt


def _sample_attempt(
    id: int = 1,
    run_id: int = 100,
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
    created_at: datetime = None,
    duration_seconds: float = 0.0,
) -> WorkflowRunAttempt:
    """Helper function to create a sample WorkflowRunAttempt for testing."""
    if created_at is None:
        created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

    return WorkflowRunAttempt(
        id=id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        duration_seconds=duration_seconds,
    )


class TestWorkflowRunAttemptInstantiation:
    """Tests for basic instantiation of WorkflowRunAttempt."""

    def test_instantiate_with_all_fields(self):
        """Test creating an attempt with all required and optional fields."""
        attempt = _sample_attempt()
        assert attempt.id == 1
        assert attempt.run_id == 100
        assert attempt.attempt_number == 1
        assert attempt.status == "completed"
        assert attempt.conclusion == "success"
        assert attempt.created_at == datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert attempt.duration_seconds == 0.0

    def test_instantiate_with_custom_values(self):
        """Test creating an attempt with custom field values."""
        attempt = _sample_attempt(
            id=42,
            run_id=200,
            attempt_number=3,
            status="in_progress",
            conclusion="failure",
            duration_seconds=123.45,
        )
        assert attempt.id == 42
        assert attempt.run_id == 200
        assert attempt.attempt_number == 3
        assert attempt.status == "in_progress"
        assert attempt.conclusion == "failure"
        assert attempt.duration_seconds == 123.45

    def test_instantiate_with_none_conclusion(self):
        """Test creating an attempt with None conclusion."""
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="in_progress",
            conclusion=None,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            duration_seconds=0.0,
        )
        assert attempt.conclusion is None

    def test_instantiate_with_default_duration(self):
        """Test that duration_seconds defaults to 0.0."""
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert attempt.duration_seconds == 0.0


class TestWorkflowRunAttemptValidation:
    """Tests for __post_init__() validation."""

    def test_valid_attempt_number_one(self):
        """Test that attempt_number = 1 is valid (minimum)."""
        attempt = _sample_attempt(attempt_number=1)
        assert attempt.attempt_number == 1

    def test_valid_attempt_number_large(self):
        """Test that large attempt numbers are valid."""
        attempt = _sample_attempt(attempt_number=1000000)
        assert attempt.attempt_number == 1000000

    def test_invalid_attempt_number_zero(self):
        """Test that attempt_number = 0 raises ValueError."""
        with pytest.raises(ValueError, match="attempt_number must be a positive integer"):
            _sample_attempt(attempt_number=0)

    def test_invalid_attempt_number_negative(self):
        """Test that negative attempt_number raises ValueError."""
        with pytest.raises(ValueError, match="attempt_number must be a positive integer"):
            _sample_attempt(attempt_number=-1)

    def test_valid_duration_zero(self):
        """Test that duration_seconds = 0.0 is valid (minimum)."""
        attempt = _sample_attempt(duration_seconds=0.0)
        assert attempt.duration_seconds == 0.0

    def test_valid_duration_positive(self):
        """Test that positive duration_seconds is valid."""
        attempt = _sample_attempt(duration_seconds=123.45)
        assert attempt.duration_seconds == 123.45

    def test_valid_duration_large(self):
        """Test that large duration_seconds (e.g., 1 week) is valid."""
        one_week_seconds = 604800.0
        attempt = _sample_attempt(duration_seconds=one_week_seconds)
        assert attempt.duration_seconds == one_week_seconds

    def test_invalid_duration_negative(self):
        """Test that negative duration_seconds raises ValueError."""
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            _sample_attempt(duration_seconds=-1.0)

    def test_invalid_duration_slightly_negative(self):
        """Test that even slightly negative duration raises ValueError."""
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            _sample_attempt(duration_seconds=-0.001)


class TestWorkflowRunAttemptSerialization:
    """Tests for to_dict() method."""

    def test_to_dict_returns_dict(self):
        """Test that to_dict() returns a dictionary."""
        attempt = _sample_attempt()
        result = attempt.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_includes_all_fields(self):
        """Test that to_dict() includes all required fields."""
        attempt = _sample_attempt()
        result = attempt.to_dict()
        assert "id" in result
        assert "run_id" in result
        assert "attempt_number" in result
        assert "status" in result
        assert "conclusion" in result
        assert "created_at" in result
        assert "duration_seconds" in result

    def test_to_dict_preserves_simple_values(self):
        """Test that to_dict() preserves integer and string values."""
        attempt = _sample_attempt(
            id=42,
            run_id=200,
            attempt_number=3,
            status="in_progress",
            conclusion="failure",
        )
        result = attempt.to_dict()
        assert result["id"] == 42
        assert result["run_id"] == 200
        assert result["attempt_number"] == 3
        assert result["status"] == "in_progress"
        assert result["conclusion"] == "failure"

    def test_to_dict_converts_datetime_to_iso_string(self):
        """Test that to_dict() converts datetime to ISO 8601 string."""
        dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        attempt = _sample_attempt(created_at=dt)
        result = attempt.to_dict()
        assert isinstance(result["created_at"], str)
        assert result["created_at"] == "2024-01-15T12:30:45+00:00"

    def test_to_dict_preserves_duration_seconds(self):
        """Test that to_dict() preserves duration_seconds."""
        attempt = _sample_attempt(duration_seconds=123.45)
        result = attempt.to_dict()
        assert result["duration_seconds"] == 123.45

    def test_to_dict_with_none_conclusion(self):
        """Test that to_dict() preserves None conclusion."""
        attempt = _sample_attempt(conclusion=None)
        result = attempt.to_dict()
        assert result["conclusion"] is None

    def test_to_dict_is_json_serializable(self):
        """Test that to_dict() output is JSON-serializable (contains no objects)."""
        import json
        attempt = _sample_attempt()
        result = attempt.to_dict()
        # Should not raise
        json_str = json.dumps(result)
        assert isinstance(json_str, str)


class TestWorkflowRunAttemptDeserialization:
    """Tests for from_dict() class method."""

    def test_from_dict_basic(self):
        """Test basic deserialization from dict."""
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00+00:00",
            "duration_seconds": 0.0,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.id == 1
        assert attempt.run_id == 100
        assert attempt.attempt_number == 1
        assert attempt.status == "completed"
        assert attempt.conclusion == "success"
        assert attempt.duration_seconds == 0.0

    def test_from_dict_reconstructs_datetime(self):
        """Test that from_dict() correctly reconstructs datetime from ISO string."""
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-15T12:30:45+00:00",
            "duration_seconds": 0.0,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        expected_dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        assert attempt.created_at == expected_dt

    def test_from_dict_with_none_conclusion(self):
        """Test from_dict() with None conclusion."""
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "in_progress",
            "conclusion": None,
            "created_at": "2024-01-01T00:00:00+00:00",
            "duration_seconds": 0.0,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.conclusion is None

    def test_from_dict_missing_duration_defaults_to_zero(self):
        """Test that from_dict() defaults duration_seconds to 0.0 if missing."""
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00+00:00",
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.duration_seconds == 0.0

    def test_from_dict_with_custom_values(self):
        """Test from_dict() with custom field values."""
        data = {
            "id": 42,
            "run_id": 200,
            "attempt_number": 3,
            "status": "in_progress",
            "conclusion": "failure",
            "created_at": "2024-01-15T12:30:45+00:00",
            "duration_seconds": 123.45,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.id == 42
        assert attempt.run_id == 200
        assert attempt.attempt_number == 3
        assert attempt.status == "in_progress"
        assert attempt.conclusion == "failure"
        assert attempt.duration_seconds == 123.45

    def test_from_dict_validates_attempt_number(self):
        """Test that from_dict() still validates attempt_number >= 1."""
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 0,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00+00:00",
            "duration_seconds": 0.0,
        }
        with pytest.raises(ValueError, match="attempt_number must be a positive integer"):
            WorkflowRunAttempt.from_dict(data)

    def test_from_dict_validates_duration_seconds(self):
        """Test that from_dict() still validates duration_seconds >= 0."""
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00+00:00",
            "duration_seconds": -1.0,
        }
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            WorkflowRunAttempt.from_dict(data)


class TestWorkflowRunAttemptRoundTrip:
    """Tests for serialization and deserialization round-trips."""

    def test_roundtrip_basic(self):
        """Test round-trip: object -> dict -> object preserves all fields."""
        original = _sample_attempt()
        dict_repr = original.to_dict()
        restored = WorkflowRunAttempt.from_dict(dict_repr)

        assert restored.id == original.id
        assert restored.run_id == original.run_id
        assert restored.attempt_number == original.attempt_number
        assert restored.status == original.status
        assert restored.conclusion == original.conclusion
        assert restored.created_at == original.created_at
        assert restored.duration_seconds == original.duration_seconds

    def test_roundtrip_with_none_conclusion(self):
        """Test round-trip preserves None conclusion."""
        original = _sample_attempt(conclusion=None)
        dict_repr = original.to_dict()
        restored = WorkflowRunAttempt.from_dict(dict_repr)
        assert restored.conclusion is None

    def test_roundtrip_with_nonzero_duration(self):
        """Test round-trip preserves non-zero duration."""
        original = _sample_attempt(duration_seconds=123.45)
        dict_repr = original.to_dict()
        restored = WorkflowRunAttempt.from_dict(dict_repr)
        assert restored.duration_seconds == 123.45

    def test_roundtrip_with_custom_datetime(self):
        """Test round-trip preserves datetime with timezone."""
        custom_dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        original = _sample_attempt(created_at=custom_dt)
        dict_repr = original.to_dict()
        restored = WorkflowRunAttempt.from_dict(dict_repr)
        assert restored.created_at == custom_dt

    def test_roundtrip_with_timezone_offset(self):
        """Test round-trip with non-UTC timezone offset."""
        # UTC+2 offset (CEST-like)
        tz_offset = timezone(timedelta(hours=2))
        dt_with_offset = datetime(2024, 6, 15, 14, 30, 0, tzinfo=tz_offset)
        original = _sample_attempt(created_at=dt_with_offset)
        dict_repr = original.to_dict()
        restored = WorkflowRunAttempt.from_dict(dict_repr)
        # datetime.fromisoformat() should preserve the offset
        assert restored.created_at == dt_with_offset

    def test_roundtrip_multiple_attempts(self):
        """Test round-trip for multiple attempts (simulating sequence)."""
        attempts = [
            _sample_attempt(attempt_number=i, duration_seconds=float(i * 10))
            for i in range(1, 4)
        ]

        dict_reprs = [a.to_dict() for a in attempts]
        restored = [WorkflowRunAttempt.from_dict(d) for d in dict_reprs]

        for original, rest in zip(attempts, restored):
            assert rest.attempt_number == original.attempt_number
            assert rest.duration_seconds == original.duration_seconds


class TestWorkflowRunAttemptEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_attempt_number_boundary_one(self):
        """Test attempt_number = 1 (minimum valid)."""
        attempt = _sample_attempt(attempt_number=1)
        assert attempt.attempt_number == 1

    def test_attempt_number_large_value(self):
        """Test attempt_number with very large value."""
        large_number = 999999999
        attempt = _sample_attempt(attempt_number=large_number)
        assert attempt.attempt_number == large_number

    def test_duration_zero(self):
        """Test duration_seconds = 0.0 (minimum valid)."""
        attempt = _sample_attempt(duration_seconds=0.0)
        assert attempt.duration_seconds == 0.0

    def test_duration_fractional(self):
        """Test duration_seconds with fractional value."""
        attempt = _sample_attempt(duration_seconds=0.123)
        assert attempt.duration_seconds == 0.123

    def test_duration_very_large(self):
        """Test duration_seconds with very large value (e.g., 1 month)."""
        one_month = 2592000.0  # ~30 days in seconds
        attempt = _sample_attempt(duration_seconds=one_month)
        assert attempt.duration_seconds == one_month

    def test_unicode_in_status(self):
        """Test that status can contain unicode characters."""
        attempt = _sample_attempt(status="完成")
        assert attempt.status == "完成"

    def test_unicode_in_conclusion(self):
        """Test that conclusion can contain unicode characters."""
        attempt = _sample_attempt(conclusion="成功")
        assert attempt.conclusion == "成功"

    def test_empty_string_status(self):
        """Test that empty string status is accepted (no validation on content)."""
        attempt = _sample_attempt(status="")
        assert attempt.status == ""

    def test_empty_string_conclusion(self):
        """Test that empty string conclusion is accepted (no validation on content)."""
        attempt = _sample_attempt(conclusion="")
        assert attempt.conclusion == ""

    def test_large_id_values(self):
        """Test with very large id and run_id values."""
        large_id = 2**31 - 1
        attempt = _sample_attempt(id=large_id, run_id=large_id)
        assert attempt.id == large_id
        assert attempt.run_id == large_id
