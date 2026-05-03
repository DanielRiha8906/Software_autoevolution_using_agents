import pytest
from datetime import datetime, timezone

from src.models.workflow_run_attempt import WorkflowRunAttempt


def _make_attempt(
    attempt_id=1,
    run_id=100,
    attempt_number=1,
    status="completed",
    conclusion=None,
    duration_seconds=0.0,
):
    """Helper function to create a WorkflowRunAttempt with minimal boilerplate."""
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        duration_seconds=duration_seconds,
    )


class TestValidation:
    """Tests for validation in __post_init__."""

    def test_valid_attempt_creation(self):
        """A valid attempt should be created without raising."""
        attempt = _make_attempt()
        assert attempt.id == 1
        assert attempt.run_id == 100
        assert attempt.attempt_number == 1

    def test_id_must_be_positive(self):
        """id must be > 0, raise ValueError if not."""
        with pytest.raises(ValueError, match="id must be greater than 0"):
            _make_attempt(attempt_id=0)

    def test_id_cannot_be_negative(self):
        """id cannot be negative."""
        with pytest.raises(ValueError, match="id must be greater than 0"):
            _make_attempt(attempt_id=-1)

    def test_run_id_must_be_positive(self):
        """run_id must be > 0, raise ValueError if not."""
        with pytest.raises(ValueError, match="run_id must be greater than 0"):
            _make_attempt(run_id=0)

    def test_run_id_cannot_be_negative(self):
        """run_id cannot be negative."""
        with pytest.raises(ValueError, match="run_id must be greater than 0"):
            _make_attempt(run_id=-1)

    def test_attempt_number_must_be_at_least_one(self):
        """attempt_number must be >= 1, raise ValueError if not."""
        with pytest.raises(ValueError, match="attempt_number must be >= 1"):
            _make_attempt(attempt_number=0)

    def test_attempt_number_cannot_be_negative(self):
        """attempt_number cannot be negative."""
        with pytest.raises(ValueError, match="attempt_number must be >= 1"):
            _make_attempt(attempt_number=-1)

    def test_duration_seconds_cannot_be_negative(self):
        """duration_seconds must be >= 0.0, raise ValueError if not."""
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            _make_attempt(duration_seconds=-0.1)

    def test_duration_seconds_can_be_zero(self):
        """duration_seconds can be exactly 0.0."""
        attempt = _make_attempt(duration_seconds=0.0)
        assert attempt.duration_seconds == 0.0

    def test_duration_seconds_can_be_positive(self):
        """duration_seconds can be positive."""
        attempt = _make_attempt(duration_seconds=120.5)
        assert attempt.duration_seconds == 120.5


class TestSerialization:
    """Tests for to_dict() method."""

    def test_to_dict_with_all_fields(self):
        """to_dict should include all fields."""
        created_at = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        attempt = WorkflowRunAttempt(
            id=5,
            run_id=200,
            attempt_number=2,
            status="completed",
            conclusion="success",
            created_at=created_at,
            duration_seconds=45.5,
        )
        result = attempt.to_dict()
        assert result["id"] == 5
        assert result["run_id"] == 200
        assert result["attempt_number"] == 2
        assert result["status"] == "completed"
        assert result["conclusion"] == "success"
        assert result["created_at"] == "2024-01-15T10:30:00+00:00"
        assert result["duration_seconds"] == 45.5

    def test_to_dict_with_none_conclusion(self):
        """to_dict should include None conclusion as-is."""
        attempt = _make_attempt(conclusion=None)
        result = attempt.to_dict()
        assert result["conclusion"] is None

    def test_to_dict_datetime_format(self):
        """to_dict should convert created_at to isoformat()."""
        created_at = datetime(2024, 5, 3, 14, 30, 45, tzinfo=timezone.utc)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=1,
            attempt_number=1,
            status="in_progress",
            conclusion=None,
            created_at=created_at,
        )
        result = attempt.to_dict()
        assert result["created_at"] == "2024-05-03T14:30:45+00:00"

    def test_to_dict_includes_duration_seconds(self):
        """to_dict should include duration_seconds."""
        attempt = _make_attempt(duration_seconds=123.456)
        result = attempt.to_dict()
        assert result["duration_seconds"] == 123.456


class TestDeserialization:
    """Tests for from_dict() classmethod."""

    def test_from_dict_with_all_fields(self):
        """from_dict should reconstruct all fields correctly."""
        data = {
            "id": 10,
            "run_id": 300,
            "attempt_number": 3,
            "status": "completed",
            "conclusion": "failure",
            "created_at": "2024-01-15T10:30:00+00:00",
            "duration_seconds": 67.8,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.id == 10
        assert attempt.run_id == 300
        assert attempt.attempt_number == 3
        assert attempt.status == "completed"
        assert attempt.conclusion == "failure"
        assert attempt.created_at == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert attempt.duration_seconds == 67.8

    def test_from_dict_missing_duration_seconds_defaults_to_zero(self):
        """from_dict should default duration_seconds to 0.0 if missing."""
        data = {
            "id": 1,
            "run_id": 1,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-15T10:30:00+00:00",
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.duration_seconds == 0.0

    def test_from_dict_with_none_conclusion(self):
        """from_dict should handle None conclusion."""
        data = {
            "id": 1,
            "run_id": 1,
            "attempt_number": 1,
            "status": "in_progress",
            "conclusion": None,
            "created_at": "2024-01-15T10:30:00+00:00",
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.conclusion is None

    def test_from_dict_parses_datetime(self):
        """from_dict should parse created_at with datetime.fromisoformat()."""
        data = {
            "id": 1,
            "run_id": 1,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-05-03T14:30:45+00:00",
            "duration_seconds": 0.0,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.created_at == datetime(2024, 5, 3, 14, 30, 45, tzinfo=timezone.utc)

    def test_from_dict_validates_on_construction(self):
        """from_dict should trigger validation via __post_init__."""
        data = {
            "id": -1,  # Invalid: must be > 0
            "run_id": 1,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": None,
            "created_at": "2024-01-15T10:30:00+00:00",
        }
        with pytest.raises(ValueError, match="id must be greater than 0"):
            WorkflowRunAttempt.from_dict(data)


class TestRoundtrip:
    """Tests for to_dict → from_dict roundtrip."""

    def test_roundtrip_preserves_all_data(self):
        """to_dict → from_dict should preserve all data."""
        original = _make_attempt(
            attempt_id=7,
            run_id=250,
            attempt_number=2,
            status="completed",
            conclusion="success",
            duration_seconds=88.2,
        )
        dict_form = original.to_dict()
        restored = WorkflowRunAttempt.from_dict(dict_form)
        assert restored.id == original.id
        assert restored.run_id == original.run_id
        assert restored.attempt_number == original.attempt_number
        assert restored.status == original.status
        assert restored.conclusion == original.conclusion
        assert restored.created_at == original.created_at
        assert restored.duration_seconds == original.duration_seconds

    def test_roundtrip_with_none_conclusion(self):
        """to_dict → from_dict should preserve None conclusion."""
        original = _make_attempt(conclusion=None)
        dict_form = original.to_dict()
        restored = WorkflowRunAttempt.from_dict(dict_form)
        assert restored.conclusion is None


class TestIsSuccessful:
    """Tests for is_successful() method."""

    def test_is_successful_completed_with_success(self):
        """An attempt with status='completed' and conclusion='success' should be successful."""
        attempt = _make_attempt(status="completed", conclusion="success")
        assert attempt.is_successful() is True

    def test_is_not_successful_completed_with_failure(self):
        """An attempt with status='completed' and conclusion='failure' should not be successful."""
        attempt = _make_attempt(status="completed", conclusion="failure")
        assert attempt.is_successful() is False

    def test_is_not_successful_completed_with_none_conclusion(self):
        """An attempt with status='completed' but no conclusion should not be successful."""
        attempt = _make_attempt(status="completed", conclusion=None)
        assert attempt.is_successful() is False

    def test_is_not_successful_in_progress_with_success_conclusion(self):
        """An attempt in progress cannot be successful (status != 'completed')."""
        attempt = _make_attempt(status="in_progress", conclusion="success")
        assert attempt.is_successful() is False

    def test_is_not_successful_queued_with_success_conclusion(self):
        """A queued attempt cannot be successful (status != 'completed')."""
        attempt = _make_attempt(status="queued", conclusion="success")
        assert attempt.is_successful() is False


class TestIsFailed:
    """Tests for is_failed() method."""

    def test_is_failed_completed_with_failure(self):
        """An attempt with status='completed' and conclusion='failure' should be failed."""
        attempt = _make_attempt(status="completed", conclusion="failure")
        assert attempt.is_failed() is True

    def test_is_not_failed_completed_with_success(self):
        """An attempt with status='completed' and conclusion='success' should not be failed."""
        attempt = _make_attempt(status="completed", conclusion="success")
        assert attempt.is_failed() is False

    def test_is_not_failed_completed_with_none_conclusion(self):
        """An attempt with status='completed' but no conclusion should not be failed."""
        attempt = _make_attempt(status="completed", conclusion=None)
        assert attempt.is_failed() is False

    def test_is_not_failed_in_progress_with_failure_conclusion(self):
        """An attempt in progress cannot be failed (status != 'completed')."""
        attempt = _make_attempt(status="in_progress", conclusion="failure")
        assert attempt.is_failed() is False

    def test_is_not_failed_queued_with_failure_conclusion(self):
        """A queued attempt cannot be failed (status != 'completed')."""
        attempt = _make_attempt(status="queued", conclusion="failure")
        assert attempt.is_failed() is False


class TestIsRunning:
    """Tests for is_running() method."""

    def test_is_running_in_progress(self):
        """An attempt with status != 'completed' should be running."""
        attempt = _make_attempt(status="in_progress")
        assert attempt.is_running() is True

    def test_is_running_queued(self):
        """A queued attempt should be running."""
        attempt = _make_attempt(status="queued")
        assert attempt.is_running() is True

    def test_is_running_waiting(self):
        """A waiting attempt should be running."""
        attempt = _make_attempt(status="waiting")
        assert attempt.is_running() is True

    def test_is_not_running_completed(self):
        """An attempt with status='completed' should not be running."""
        attempt = _make_attempt(status="completed")
        assert attempt.is_running() is False

    def test_is_not_running_completed_with_success(self):
        """A completed attempt with success conclusion should not be running."""
        attempt = _make_attempt(status="completed", conclusion="success")
        assert attempt.is_running() is False

    def test_is_not_running_completed_with_failure(self):
        """A completed attempt with failure conclusion should not be running."""
        attempt = _make_attempt(status="completed", conclusion="failure")
        assert attempt.is_running() is False


class TestMutualExclusivity:
    """Tests for mutual exclusivity of helper method results."""

    def test_successful_and_failed_mutually_exclusive(self):
        """An attempt cannot be both successful and failed."""
        success_attempt = _make_attempt(status="completed", conclusion="success")
        failed_attempt = _make_attempt(status="completed", conclusion="failure")
        assert success_attempt.is_successful() is True
        assert success_attempt.is_failed() is False
        assert failed_attempt.is_successful() is False
        assert failed_attempt.is_failed() is True

    def test_running_and_completed_mutually_exclusive(self):
        """An attempt cannot be both running and completed."""
        running_attempt = _make_attempt(status="in_progress")
        completed_attempt = _make_attempt(status="completed", conclusion="success")
        assert running_attempt.is_running() is True
        assert running_attempt.is_successful() is False
        assert running_attempt.is_failed() is False
        assert completed_attempt.is_running() is False

    def test_completed_with_no_conclusion_only_not_running(self):
        """A completed attempt with no conclusion is not running but not successful or failed."""
        attempt = _make_attempt(status="completed", conclusion=None)
        assert attempt.is_running() is False
        assert attempt.is_successful() is False
        assert attempt.is_failed() is False
