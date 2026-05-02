import pytest
from datetime import datetime, timezone, timedelta

from src.models.workflow_run_attempt import WorkflowRunAttempt


def _sample_attempt() -> WorkflowRunAttempt:
    """Create a sample attempt for testing."""
    return WorkflowRunAttempt(
        id=1,
        run_id=100,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        duration_seconds=42.5,
    )


class TestWorkflowRunAttemptInstantiation:
    """Test basic instantiation of WorkflowRunAttempt."""

    def test_create_attempt_with_all_fields(self):
        attempt = _sample_attempt()
        assert attempt.id == 1
        assert attempt.run_id == 100
        assert attempt.attempt_number == 1
        assert attempt.status == "completed"
        assert attempt.conclusion == "success"
        assert attempt.duration_seconds == 42.5

    def test_create_attempt_without_conclusion(self):
        attempt = WorkflowRunAttempt(
            id=2,
            run_id=100,
            attempt_number=1,
            status="in_progress",
            conclusion=None,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert attempt.conclusion is None
        assert attempt.duration_seconds is None

    def test_create_attempt_without_duration(self):
        attempt = WorkflowRunAttempt(
            id=3,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert attempt.duration_seconds is None


class TestWorkflowRunAttemptValidation:
    """Test validation rules for WorkflowRunAttempt."""

    def test_attempt_number_must_be_positive(self):
        """Validation rule 1: attempt_number >= 1."""
        with pytest.raises(ValueError, match="attempt_number must be >= 1"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number=0,
                status="completed",
                conclusion="success",
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            )

    def test_attempt_number_negative_raises_error(self):
        """Validation rule 1: attempt_number < 0 raises ValueError."""
        with pytest.raises(ValueError, match="attempt_number must be >= 1"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number=-5,
                status="completed",
                conclusion="success",
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            )

    def test_attempt_number_one_is_valid(self):
        """Validation rule: attempt_number == 1 is valid."""
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert attempt.attempt_number == 1

    def test_attempt_number_large_value_is_valid(self):
        """Validation rule: attempt_number can be arbitrarily large."""
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=9999,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert attempt.attempt_number == 9999

    def test_status_can_be_any_string(self):
        """Status is a string with no validation on specific values."""
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="custom_status",
            conclusion=None,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert attempt.status == "custom_status"

    def test_conclusion_can_be_any_string_or_none(self):
        """Conclusion is optional string with no validation on values."""
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="custom_conclusion",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert attempt.conclusion == "custom_conclusion"


class TestWorkflowRunAttemptSerialization:
    """Test to_dict() serialization."""

    def test_to_dict_with_all_fields(self):
        attempt = _sample_attempt()
        data = attempt.to_dict()

        assert data["id"] == 1
        assert data["run_id"] == 100
        assert data["attempt_number"] == 1
        assert data["status"] == "completed"
        assert data["conclusion"] == "success"
        assert data["duration_seconds"] == 42.5
        assert isinstance(data["created_at"], str)

    def test_to_dict_created_at_is_iso_format(self):
        attempt = _sample_attempt()
        data = attempt.to_dict()
        # Verify ISO format (can be parsed back)
        assert datetime.fromisoformat(data["created_at"]) == attempt.created_at

    def test_to_dict_with_none_conclusion(self):
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="in_progress",
            conclusion=None,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            duration_seconds=None,
        )
        data = attempt.to_dict()

        assert data["conclusion"] is None
        assert data["duration_seconds"] is None

    def test_to_dict_returns_dict_type(self):
        attempt = _sample_attempt()
        data = attempt.to_dict()
        assert isinstance(data, dict)


class TestWorkflowRunAttemptDeserialization:
    """Test from_dict() deserialization."""

    def test_from_dict_with_all_fields(self):
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T12:00:00+00:00",
            "duration_seconds": 42.5,
        }
        attempt = WorkflowRunAttempt.from_dict(data)

        assert attempt.id == 1
        assert attempt.run_id == 100
        assert attempt.attempt_number == 1
        assert attempt.status == "completed"
        assert attempt.conclusion == "success"
        assert attempt.duration_seconds == 42.5

    def test_from_dict_parses_iso_datetime(self):
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T12:00:00+00:00",
            "duration_seconds": 42.5,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.created_at == datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def test_from_dict_with_missing_conclusion_defaults_to_none(self):
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "in_progress",
            "created_at": "2024-01-01T12:00:00+00:00",
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.conclusion is None

    def test_from_dict_with_missing_duration_defaults_to_none(self):
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T12:00:00+00:00",
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.duration_seconds is None

    def test_from_dict_with_explicit_none_conclusion(self):
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "in_progress",
            "conclusion": None,
            "created_at": "2024-01-01T12:00:00+00:00",
            "duration_seconds": None,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.conclusion is None
        assert attempt.duration_seconds is None


class TestWorkflowRunAttemptRoundtrip:
    """Test serialization roundtrip (to_dict -> from_dict)."""

    def test_roundtrip_with_all_fields(self):
        original = _sample_attempt()
        data = original.to_dict()
        restored = WorkflowRunAttempt.from_dict(data)

        assert restored.id == original.id
        assert restored.run_id == original.run_id
        assert restored.attempt_number == original.attempt_number
        assert restored.status == original.status
        assert restored.conclusion == original.conclusion
        assert restored.duration_seconds == original.duration_seconds
        assert restored.created_at == original.created_at

    def test_roundtrip_with_none_values(self):
        original = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="in_progress",
            conclusion=None,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            duration_seconds=None,
        )
        data = original.to_dict()
        restored = WorkflowRunAttempt.from_dict(data)

        assert restored.conclusion is None
        assert restored.duration_seconds is None

    def test_roundtrip_preserves_datetime_precision(self):
        created = datetime(2024, 1, 1, 12, 30, 45, 123456, tzinfo=timezone.utc)
        original = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=created,
            duration_seconds=42.5,
        )
        data = original.to_dict()
        restored = WorkflowRunAttempt.from_dict(data)

        assert restored.created_at == original.created_at


class TestWorkflowRunAttemptTimezones:
    """Test datetime handling with different timezones."""

    def test_roundtrip_with_utc_timezone(self):
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=dt,
        )
        data = attempt.to_dict()
        restored = WorkflowRunAttempt.from_dict(data)

        assert restored.created_at.tzinfo is not None
        assert restored.created_at == dt

    def test_roundtrip_with_offset_timezone(self):
        # UTC+2 (CEST-like timezone)
        cest_tz = timezone(timedelta(hours=2))
        dt = datetime(2024, 1, 1, 14, 0, 0, tzinfo=cest_tz)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=dt,
        )
        data = attempt.to_dict()
        restored = WorkflowRunAttempt.from_dict(data)

        assert restored.created_at == dt

    def test_iso_format_preserves_timezone_offset(self):
        cest_tz = timezone(timedelta(hours=2))
        dt = datetime(2024, 1, 1, 14, 0, 0, tzinfo=cest_tz)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=dt,
        )
        data = attempt.to_dict()
        assert "+02:00" in data["created_at"]


class TestWorkflowRunAttemptEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_attempt_with_zero_duration(self):
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            duration_seconds=0.0,
        )
        assert attempt.duration_seconds == 0.0

    def test_attempt_with_negative_duration(self):
        # Note: No validation on duration_seconds, unlike WorkflowRun
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            duration_seconds=-1.0,
        )
        assert attempt.duration_seconds == -1.0

    def test_attempt_with_very_large_id(self):
        attempt = WorkflowRunAttempt(
            id=999999999,
            run_id=999999999,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert attempt.id == 999999999
        assert attempt.run_id == 999999999

    def test_attempt_with_empty_string_status(self):
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="",
            conclusion=None,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert attempt.status == ""

    def test_attempt_with_empty_string_conclusion(self):
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert attempt.conclusion == ""

    def test_from_dict_with_extra_keys_ignores_them(self):
        """Extra keys in dict should be ignored."""
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T12:00:00+00:00",
            "duration_seconds": 42.5,
            "extra_field": "should be ignored",
            "another_extra": 999,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.id == 1
        assert not hasattr(attempt, "extra_field")
