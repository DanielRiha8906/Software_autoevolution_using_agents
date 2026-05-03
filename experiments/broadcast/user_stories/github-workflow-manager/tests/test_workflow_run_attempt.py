import pytest
from datetime import datetime, timezone

from src.models.workflow_run_attempt import WorkflowRunAttempt


def _make_attempt(
    attempt_id: int = 1,
    run_id: int = 100,
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
    created_at: datetime = None,
    duration_seconds: float = None,
) -> WorkflowRunAttempt:
    """Helper to create a WorkflowRunAttempt with reasonable defaults."""
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
    """Test basic creation and attribute validation."""

    def test_create_with_all_attributes(self):
        """Test creating a WorkflowRunAttempt with all attributes."""
        created_at = datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="in_progress",
            conclusion=None,
            created_at=created_at,
            duration_seconds=None,
        )
        assert attempt.id == 1
        assert attempt.run_id == 100
        assert attempt.attempt_number == 1
        assert attempt.status == "in_progress"
        assert attempt.conclusion is None
        assert attempt.created_at == created_at
        assert attempt.duration_seconds is None

    def test_create_with_conclusion(self):
        """Test creating an attempt with a conclusion."""
        attempt = _make_attempt(conclusion="success")
        assert attempt.conclusion == "success"

    def test_create_with_duration(self):
        """Test creating an attempt with duration_seconds."""
        attempt = _make_attempt(duration_seconds=45.5)
        assert attempt.duration_seconds == 45.5

    def test_create_with_zero_duration(self):
        """Test creating an attempt with zero duration (allowed)."""
        attempt = _make_attempt(duration_seconds=0.0)
        assert attempt.duration_seconds == 0.0

    def test_create_with_optional_conclusion_none(self):
        """Test creating an attempt with None conclusion."""
        attempt = _make_attempt(conclusion=None)
        assert attempt.conclusion is None


class TestWorkflowRunAttemptValidation:
    """Test validation rules in __post_init__."""

    def test_attempt_number_must_be_positive(self):
        """Test that attempt_number must be >= 1."""
        with pytest.raises(ValueError, match="attempt_number must be positive"):
            _make_attempt(attempt_number=0)

    def test_attempt_number_negative_raises(self):
        """Test that negative attempt_number raises ValueError."""
        with pytest.raises(ValueError, match="attempt_number must be positive"):
            _make_attempt(attempt_number=-1)

    def test_attempt_number_one_is_valid(self):
        """Test that attempt_number=1 is valid (minimum)."""
        attempt = _make_attempt(attempt_number=1)
        assert attempt.attempt_number == 1

    def test_attempt_number_multiple_is_valid(self):
        """Test that attempt_number > 1 is valid."""
        attempt = _make_attempt(attempt_number=5)
        assert attempt.attempt_number == 5

    def test_duration_seconds_negative_raises(self):
        """Test that negative duration_seconds raises ValueError."""
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            _make_attempt(duration_seconds=-1.0)

    def test_duration_seconds_very_negative_raises(self):
        """Test that very negative duration_seconds raises ValueError."""
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            _make_attempt(duration_seconds=-100.5)

    def test_multiple_validation_errors(self):
        """Test that attempt_number validation is checked before duration_seconds."""
        # attempt_number validation should catch first
        with pytest.raises(ValueError, match="attempt_number must be positive"):
            _make_attempt(attempt_number=0, duration_seconds=-1.0)


class TestWorkflowRunAttemptTimezone:
    """Test created_at timezone handling."""

    def test_created_at_with_utc_timezone(self):
        """Test that created_at can be timezone-aware UTC."""
        utc_time = datetime(2026, 5, 3, 14, 30, 0, tzinfo=timezone.utc)
        attempt = _make_attempt(created_at=utc_time)
        assert attempt.created_at == utc_time
        assert attempt.created_at.tzinfo is not None

    def test_created_at_is_timezone_aware(self):
        """Test that created_at is preserved as timezone-aware."""
        utc_time = datetime.now(timezone.utc)
        attempt = _make_attempt(created_at=utc_time)
        assert attempt.created_at.tzinfo is not None
        assert attempt.created_at == utc_time

    def test_created_at_isoformat_preserves_timezone(self):
        """Test that isoformat() preserves timezone info."""
        utc_time = datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc)
        attempt = _make_attempt(created_at=utc_time)
        iso_str = attempt.created_at.isoformat()
        assert "+" in iso_str or iso_str.endswith("Z") or "00:00" in iso_str


class TestWorkflowRunAttemptSerialization:
    """Test serialization (to_dict) and deserialization (from_dict)."""

    def test_to_dict_all_fields(self):
        """Test to_dict with all fields populated."""
        created_at = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=2,
            status="completed",
            conclusion="success",
            created_at=created_at,
            duration_seconds=120.5,
        )
        data = attempt.to_dict()

        assert data["id"] == 1
        assert data["run_id"] == 100
        assert data["attempt_number"] == 2
        assert data["status"] == "completed"
        assert data["conclusion"] == "success"
        assert data["created_at"] == created_at.isoformat()
        assert data["duration_seconds"] == 120.5

    def test_to_dict_with_none_conclusion(self):
        """Test to_dict with None conclusion."""
        attempt = _make_attempt(conclusion=None, duration_seconds=None)
        data = attempt.to_dict()

        assert data["conclusion"] is None
        assert data["duration_seconds"] is None

    def test_from_dict_all_fields(self):
        """Test from_dict with all fields."""
        created_at = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 2,
            "status": "completed",
            "conclusion": "success",
            "created_at": created_at.isoformat(),
            "duration_seconds": 120.5,
        }
        attempt = WorkflowRunAttempt.from_dict(data)

        assert attempt.id == 1
        assert attempt.run_id == 100
        assert attempt.attempt_number == 2
        assert attempt.status == "completed"
        assert attempt.conclusion == "success"
        assert attempt.created_at == created_at
        assert attempt.duration_seconds == 120.5

    def test_from_dict_with_none_conclusion(self):
        """Test from_dict with None conclusion."""
        created_at = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "in_progress",
            "created_at": created_at.isoformat(),
        }
        attempt = WorkflowRunAttempt.from_dict(data)

        assert attempt.conclusion is None
        assert attempt.duration_seconds is None

    def test_roundtrip_serialization(self):
        """Test that to_dict -> from_dict preserves all data."""
        original = _make_attempt(
            attempt_id=5,
            run_id=200,
            attempt_number=3,
            status="completed",
            conclusion="failure",
            duration_seconds=90.0,
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

    def test_from_dict_validates_on_creation(self):
        """Test that from_dict triggers validation in __post_init__."""
        created_at = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 0,  # Invalid: must be >= 1
            "status": "completed",
            "conclusion": "success",
            "created_at": created_at.isoformat(),
        }
        with pytest.raises(ValueError, match="attempt_number must be positive"):
            WorkflowRunAttempt.from_dict(data)


class TestWorkflowRunAttemptUniqueness:
    """Test unique constraint validation for (run_id, attempt_number) pair.

    Note: The model enforces attempt_number >= 1 validation, but the uniqueness
    constraint is typically enforced at the service or database layer, not in
    the model itself. These tests verify the model structure supports uniqueness.
    """

    def test_same_run_different_attempt_numbers(self):
        """Test creating attempts with same run_id but different attempt_numbers."""
        attempt1 = _make_attempt(run_id=100, attempt_number=1)
        attempt2 = _make_attempt(run_id=100, attempt_number=2)

        assert attempt1.run_id == attempt2.run_id
        assert attempt1.attempt_number != attempt2.attempt_number

    def test_different_runs_same_attempt_number(self):
        """Test creating attempts with different run_id but same attempt_number."""
        attempt1 = _make_attempt(run_id=100, attempt_number=1)
        attempt2 = _make_attempt(run_id=200, attempt_number=1)

        assert attempt1.run_id != attempt2.run_id
        assert attempt1.attempt_number == attempt2.attempt_number

    def test_model_structure_supports_composite_key(self):
        """Test that the model has both run_id and attempt_number for composite key."""
        attempt = _make_attempt(run_id=100, attempt_number=3)
        assert hasattr(attempt, "run_id")
        assert hasattr(attempt, "attempt_number")


class TestWorkflowRunAttemptEdgeCases:
    """Test edge cases and special scenarios."""

    def test_large_attempt_number(self):
        """Test with a large attempt_number."""
        attempt = _make_attempt(attempt_number=1000)
        assert attempt.attempt_number == 1000

    def test_large_duration_seconds(self):
        """Test with a large duration_seconds value."""
        attempt = _make_attempt(duration_seconds=86400.5)  # More than a day
        assert attempt.duration_seconds == 86400.5

    def test_very_small_float_duration(self):
        """Test with a very small positive float duration."""
        attempt = _make_attempt(duration_seconds=0.001)
        assert attempt.duration_seconds == 0.001

    def test_status_values(self):
        """Test different status values."""
        for status in ["queued", "in_progress", "completed", "waiting"]:
            attempt = _make_attempt(status=status)
            assert attempt.status == status

    def test_conclusion_values(self):
        """Test different conclusion values."""
        for conclusion in ["success", "failure", "cancelled", "skipped"]:
            attempt = _make_attempt(conclusion=conclusion)
            assert attempt.conclusion == conclusion

    def test_empty_string_status(self):
        """Test that empty string status is allowed (model does not validate it)."""
        attempt = _make_attempt(status="")
        assert attempt.status == ""

    def test_empty_string_conclusion(self):
        """Test that empty string conclusion is allowed."""
        attempt = _make_attempt(conclusion="")
        assert attempt.conclusion == ""
