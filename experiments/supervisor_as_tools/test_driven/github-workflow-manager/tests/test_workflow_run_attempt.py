import pytest
from datetime import datetime, timezone, timedelta

from src.models.workflow_run_attempt import WorkflowRunAttempt, CEST


class TestWorkflowRunAttemptInitialization:
    """Test initialization and validation of WorkflowRunAttempt."""

    def test_valid_creation(self):
        """Test creating a valid WorkflowRunAttempt instance."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="in_progress",
            conclusion="none",
            created_at=created_at,
            duration_seconds=0.0,
        )
        assert attempt.id == 1
        assert attempt.run_id == 100
        assert attempt.attempt_number == 1
        assert attempt.status == "in_progress"
        assert attempt.conclusion == "none"
        assert attempt.created_at == created_at
        assert attempt.duration_seconds == 0.0

    def test_duration_seconds_default_is_zero(self):
        """Test that duration_seconds defaults to 0.0 when not provided."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=created_at,
        )
        assert attempt.duration_seconds == 0.0

    def test_attempt_number_must_be_at_least_one(self):
        """Test that attempt_number >= 1 is enforced."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        with pytest.raises(ValueError, match="attempt_number must be >= 1"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number=0,
                status="completed",
                conclusion="success",
                created_at=created_at,
            )

    def test_attempt_number_negative_raises(self):
        """Test that negative attempt_number is rejected."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        with pytest.raises(ValueError, match="attempt_number must be >= 1"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number=-5,
                status="completed",
                conclusion="success",
                created_at=created_at,
            )

    def test_created_at_must_be_timezone_aware(self):
        """Test that naive datetime for created_at is rejected."""
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        with pytest.raises(ValueError, match="created_at must be timezone-aware, not naive"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number=1,
                status="completed",
                conclusion="success",
                created_at=naive_dt,
            )

    def test_created_at_must_be_cest_timezone(self):
        """Test that created_at must use CEST timezone specifically."""
        utc_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="created_at must be in CEST timezone"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number=1,
                status="completed",
                conclusion="success",
                created_at=utc_dt,
            )

    def test_created_at_with_different_timezone_raises(self):
        """Test that other timezones are rejected."""
        other_tz = timezone(timedelta(hours=5))
        dt_with_other_tz = datetime(2024, 1, 1, 12, 0, 0, tzinfo=other_tz)
        with pytest.raises(ValueError, match="created_at must be in CEST timezone"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number=1,
                status="completed",
                conclusion="success",
                created_at=dt_with_other_tz,
            )

    def test_duration_seconds_must_be_non_negative(self):
        """Test that negative duration_seconds is rejected."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number=1,
                status="completed",
                conclusion="success",
                created_at=created_at,
                duration_seconds=-0.5,
            )

    def test_duration_seconds_zero_is_valid(self):
        """Test that 0.0 duration_seconds is accepted."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=created_at,
            duration_seconds=0.0,
        )
        assert attempt.duration_seconds == 0.0

    def test_large_duration_seconds_is_valid(self):
        """Test that large duration_seconds values are accepted."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=created_at,
            duration_seconds=3600.5,
        )
        assert attempt.duration_seconds == 3600.5


class TestWorkflowRunAttemptToDict:
    """Test to_dict serialization method."""

    def test_to_dict_basic(self):
        """Test basic to_dict serialization."""
        created_at = datetime(2024, 1, 15, 14, 30, 45, tzinfo=CEST)
        attempt = WorkflowRunAttempt(
            id=42,
            run_id=200,
            attempt_number=3,
            status="completed",
            conclusion="success",
            created_at=created_at,
            duration_seconds=120.75,
        )
        result = attempt.to_dict()
        assert result == {
            "id": 42,
            "run_id": 200,
            "attempt_number": 3,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-15T14:30:45+02:00",
            "duration_seconds": 120.75,
        }

    def test_to_dict_with_zero_duration(self):
        """Test to_dict with zero duration."""
        created_at = datetime(2024, 1, 1, 0, 0, 0, tzinfo=CEST)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=1,
            attempt_number=1,
            status="in_progress",
            conclusion="none",
            created_at=created_at,
            duration_seconds=0.0,
        )
        result = attempt.to_dict()
        assert result["duration_seconds"] == 0.0

    def test_to_dict_iso_format(self):
        """Test that created_at is serialized to ISO format."""
        created_at = datetime(2024, 6, 15, 10, 45, 30, tzinfo=CEST)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=1,
            attempt_number=1,
            status="queued",
            conclusion="none",
            created_at=created_at,
        )
        result = attempt.to_dict()
        assert result["created_at"] == "2024-06-15T10:45:30+02:00"

    def test_to_dict_does_not_mutate_original(self):
        """Test that to_dict does not modify the original object."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        attempt = WorkflowRunAttempt(
            id=5,
            run_id=50,
            attempt_number=2,
            status="failed",
            conclusion="failure",
            created_at=created_at,
            duration_seconds=300.0,
        )
        original_created_at = attempt.created_at
        _ = attempt.to_dict()
        assert attempt.created_at == original_created_at
        assert attempt.duration_seconds == 300.0


class TestWorkflowRunAttemptFromDict:
    """Test from_dict deserialization method."""

    def test_from_dict_basic(self):
        """Test basic from_dict deserialization."""
        data = {
            "id": 10,
            "run_id": 150,
            "attempt_number": 2,
            "status": "completed",
            "conclusion": "failure",
            "created_at": "2024-02-20T16:45:30+02:00",
            "duration_seconds": 450.5,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.id == 10
        assert attempt.run_id == 150
        assert attempt.attempt_number == 2
        assert attempt.status == "completed"
        assert attempt.conclusion == "failure"
        assert attempt.duration_seconds == 450.5
        assert attempt.created_at.year == 2024
        assert attempt.created_at.month == 2
        assert attempt.created_at.day == 20

    def test_from_dict_without_duration_seconds(self):
        """Test from_dict when duration_seconds is not provided (defaults to 0.0)."""
        data = {
            "id": 7,
            "run_id": 70,
            "attempt_number": 1,
            "status": "in_progress",
            "conclusion": "none",
            "created_at": "2024-03-10T09:15:00+02:00",
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.duration_seconds == 0.0

    def test_from_dict_with_zero_duration(self):
        """Test from_dict explicitly with zero duration."""
        data = {
            "id": 8,
            "run_id": 80,
            "attempt_number": 1,
            "status": "queued",
            "conclusion": "none",
            "created_at": "2024-01-05T08:00:00+02:00",
            "duration_seconds": 0.0,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.duration_seconds == 0.0

    def test_from_dict_roundtrip(self):
        """Test that from_dict(to_dict()) is idempotent."""
        created_at = datetime(2024, 5, 12, 13, 22, 11, tzinfo=CEST)
        original = WorkflowRunAttempt(
            id=99,
            run_id=990,
            attempt_number=5,
            status="completed",
            conclusion="success",
            created_at=created_at,
            duration_seconds=987.65,
        )
        serialized = original.to_dict()
        deserialized = WorkflowRunAttempt.from_dict(serialized)

        assert deserialized.id == original.id
        assert deserialized.run_id == original.run_id
        assert deserialized.attempt_number == original.attempt_number
        assert deserialized.status == original.status
        assert deserialized.conclusion == original.conclusion
        assert deserialized.duration_seconds == original.duration_seconds
        assert deserialized.created_at == original.created_at

    def test_from_dict_validates_timezone(self):
        """Test that from_dict enforces CEST timezone validation."""
        data = {
            "id": 11,
            "run_id": 110,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T12:00:00+00:00",  # UTC instead of CEST
            "duration_seconds": 100.0,
        }
        with pytest.raises(ValueError, match="created_at must be in CEST timezone"):
            WorkflowRunAttempt.from_dict(data)

    def test_from_dict_validates_attempt_number(self):
        """Test that from_dict enforces attempt_number validation."""
        data = {
            "id": 12,
            "run_id": 120,
            "attempt_number": 0,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T12:00:00+02:00",
            "duration_seconds": 100.0,
        }
        with pytest.raises(ValueError, match="attempt_number must be >= 1"):
            WorkflowRunAttempt.from_dict(data)

    def test_from_dict_validates_duration_seconds(self):
        """Test that from_dict enforces duration_seconds validation."""
        data = {
            "id": 13,
            "run_id": 130,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T12:00:00+02:00",
            "duration_seconds": -10.0,
        }
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            WorkflowRunAttempt.from_dict(data)


class TestWorkflowRunAttemptEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_attempt_number_one_is_valid(self):
        """Test that attempt_number=1 is the minimum valid value."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=1,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=created_at,
        )
        assert attempt.attempt_number == 1

    def test_large_attempt_number(self):
        """Test that large attempt numbers are accepted."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=1,
            attempt_number=1000,
            status="completed",
            conclusion="success",
            created_at=created_at,
        )
        assert attempt.attempt_number == 1000

    def test_large_ids(self):
        """Test that large id and run_id values are accepted."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        attempt = WorkflowRunAttempt(
            id=999999999,
            run_id=888888888,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=created_at,
        )
        assert attempt.id == 999999999
        assert attempt.run_id == 888888888

    def test_various_status_values(self):
        """Test that various status strings are accepted."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        statuses = ["queued", "in_progress", "completed", "unknown"]
        for status in statuses:
            attempt = WorkflowRunAttempt(
                id=1,
                run_id=1,
                attempt_number=1,
                status=status,
                conclusion="none",
                created_at=created_at,
            )
            assert attempt.status == status

    def test_various_conclusion_values(self):
        """Test that various conclusion strings are accepted."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        conclusions = ["success", "failure", "neutral", "cancelled", "none"]
        for conclusion in conclusions:
            attempt = WorkflowRunAttempt(
                id=1,
                run_id=1,
                attempt_number=1,
                status="completed",
                conclusion=conclusion,
                created_at=created_at,
            )
            assert attempt.conclusion == conclusion

    def test_fractional_duration_seconds(self):
        """Test that fractional duration_seconds are preserved."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=CEST)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=1,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=created_at,
            duration_seconds=0.001,
        )
        assert attempt.duration_seconds == 0.001
