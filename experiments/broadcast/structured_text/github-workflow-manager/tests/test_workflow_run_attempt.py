import pytest
from datetime import datetime, timezone

from src.models.workflow_run_attempt import WorkflowRunAttempt


def _make_attempt(
    status: str = "completed",
    conclusion: str | None = "success",
) -> WorkflowRunAttempt:
    """Create a WorkflowRunAttempt with specified status and conclusion."""
    return WorkflowRunAttempt(
        id=1,
        run_id=100,
        attempt_number=1,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        duration_seconds=10.5,
    )


class TestWorkflowRunAttemptCreation:
    """Tests for WorkflowRunAttempt creation and validation."""

    def test_create_successful_attempt(self):
        """Test creating a successful completed attempt."""
        attempt = _make_attempt()
        assert attempt.id == 1
        assert attempt.run_id == 100
        assert attempt.attempt_number == 1
        assert attempt.status == "completed"
        assert attempt.conclusion == "success"
        assert attempt.duration_seconds == 10.5

    def test_create_failed_attempt(self):
        """Test creating a failed attempt."""
        attempt = _make_attempt(status="completed", conclusion="failure")
        assert attempt.status == "completed"
        assert attempt.conclusion == "failure"

    def test_create_attempt_with_no_conclusion(self):
        """Test creating an attempt with no conclusion."""
        attempt = _make_attempt(status="in_progress", conclusion=None)
        assert attempt.status == "in_progress"
        assert attempt.conclusion is None

    def test_duration_seconds_non_negative(self):
        """Test that duration_seconds must be non-negative."""
        with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
            WorkflowRunAttempt(
                id=1,
                run_id=100,
                attempt_number=1,
                status="completed",
                conclusion="success",
                created_at=datetime.now(timezone.utc),
                duration_seconds=-1.0,
            )

    def test_duration_seconds_default_zero(self):
        """Test that duration_seconds defaults to 0.0."""
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=datetime.now(timezone.utc),
        )
        assert attempt.duration_seconds == 0.0


class TestIsTerminal:
    """Tests for is_terminal() method."""

    def test_is_terminal_when_completed(self):
        attempt = _make_attempt(status="completed")
        assert attempt.is_terminal() is True

    def test_is_terminal_when_not_completed(self):
        for status in ["queued", "in_progress", "waiting", "pending"]:
            attempt = _make_attempt(status=status)
            assert attempt.is_terminal() is False


class TestIsRunning:
    """Tests for is_running() method."""

    def test_is_running_when_in_progress(self):
        attempt = _make_attempt(status="in_progress")
        assert attempt.is_running() is True

    def test_is_running_when_not_in_progress(self):
        for status in ["queued", "completed", "waiting", "pending"]:
            attempt = _make_attempt(status=status)
            assert attempt.is_running() is False


class TestTerminalAndRunningMutuallyExclusive:
    """Tests to verify is_terminal() and is_running() are mutually exclusive."""

    def test_terminal_and_running_never_both_true(self):
        """Verify that an attempt cannot be both terminal and running."""
        for status in ["queued", "in_progress", "completed", "waiting", "pending"]:
            attempt = _make_attempt(status=status)
            assert not (attempt.is_terminal() and attempt.is_running())


class TestIsSuccessful:
    """Tests for is_successful() method."""

    def test_is_successful_when_success(self):
        attempt = _make_attempt(conclusion="success")
        assert attempt.is_successful() is True

    def test_is_successful_when_not_success(self):
        for conclusion in ["failure", "cancelled", "skipped", "timed_out"]:
            attempt = _make_attempt(conclusion=conclusion)
            assert attempt.is_successful() is False

    def test_is_successful_with_no_conclusion(self):
        attempt = _make_attempt(conclusion=None)
        assert attempt.is_successful() is False


class TestIsFailed:
    """Tests for is_failed() method."""

    def test_is_failed_when_failure(self):
        attempt = _make_attempt(conclusion="failure")
        assert attempt.is_failed() is True

    def test_is_failed_when_not_failure(self):
        for conclusion in ["success", "cancelled", "skipped", "timed_out"]:
            attempt = _make_attempt(conclusion=conclusion)
            assert attempt.is_failed() is False

    def test_is_failed_with_no_conclusion(self):
        attempt = _make_attempt(conclusion=None)
        assert attempt.is_failed() is False


class TestIsCancelled:
    """Tests for is_cancelled() method."""

    def test_is_cancelled_when_cancelled(self):
        attempt = _make_attempt(conclusion="cancelled")
        assert attempt.is_cancelled() is True

    def test_is_cancelled_when_not_cancelled(self):
        for conclusion in ["success", "failure", "skipped", "timed_out"]:
            attempt = _make_attempt(conclusion=conclusion)
            assert attempt.is_cancelled() is False

    def test_is_cancelled_with_no_conclusion(self):
        attempt = _make_attempt(conclusion=None)
        assert attempt.is_cancelled() is False


class TestSerialization:
    """Tests for to_dict() and from_dict() serialization methods."""

    def test_to_dict_successful_attempt(self):
        """Test serializing a successful attempt to dict."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        attempt = WorkflowRunAttempt(
            id=1,
            run_id=100,
            attempt_number=1,
            status="completed",
            conclusion="success",
            created_at=created_at,
            duration_seconds=15.5,
        )
        data = attempt.to_dict()
        assert data["id"] == 1
        assert data["run_id"] == 100
        assert data["attempt_number"] == 1
        assert data["status"] == "completed"
        assert data["conclusion"] == "success"
        assert data["created_at"] == "2024-01-01T12:00:00+00:00"
        assert data["duration_seconds"] == 15.5

    def test_to_dict_with_no_conclusion(self):
        """Test serializing an attempt with no conclusion to dict."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        attempt = WorkflowRunAttempt(
            id=2,
            run_id=101,
            attempt_number=1,
            status="in_progress",
            conclusion=None,
            created_at=created_at,
        )
        data = attempt.to_dict()
        assert data["conclusion"] is None

    def test_from_dict_successful_attempt(self):
        """Test deserializing a successful attempt from dict."""
        data = {
            "id": 1,
            "run_id": 100,
            "attempt_number": 1,
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T12:00:00+00:00",
            "duration_seconds": 15.5,
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.id == 1
        assert attempt.run_id == 100
        assert attempt.attempt_number == 1
        assert attempt.status == "completed"
        assert attempt.conclusion == "success"
        assert attempt.created_at == datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert attempt.duration_seconds == 15.5

    def test_from_dict_with_no_conclusion(self):
        """Test deserializing an attempt with no conclusion from dict."""
        data = {
            "id": 2,
            "run_id": 101,
            "attempt_number": 1,
            "status": "in_progress",
            "created_at": "2024-01-01T12:00:00+00:00",
        }
        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.conclusion is None
        assert attempt.duration_seconds == 0.0

    def test_roundtrip_serialization(self):
        """Test that an attempt can be serialized and deserialized without loss."""
        original = WorkflowRunAttempt(
            id=42,
            run_id=200,
            attempt_number=3,
            status="completed",
            conclusion="failure",
            created_at=datetime(2024, 6, 15, 14, 30, 45, tzinfo=timezone.utc),
            duration_seconds=42.7,
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


class TestStateMethodsCombinations:
    """Tests for various combinations of state methods."""

    def test_completed_successful_attempt(self):
        """Test a successful completed attempt."""
        attempt = _make_attempt(status="completed", conclusion="success")
        assert attempt.is_terminal() is True
        assert attempt.is_running() is False
        assert attempt.is_successful() is True
        assert attempt.is_failed() is False
        assert attempt.is_cancelled() is False

    def test_completed_failed_attempt(self):
        """Test a failed completed attempt."""
        attempt = _make_attempt(status="completed", conclusion="failure")
        assert attempt.is_terminal() is True
        assert attempt.is_running() is False
        assert attempt.is_successful() is False
        assert attempt.is_failed() is True
        assert attempt.is_cancelled() is False

    def test_completed_cancelled_attempt(self):
        """Test a cancelled completed attempt."""
        attempt = _make_attempt(status="completed", conclusion="cancelled")
        assert attempt.is_terminal() is True
        assert attempt.is_running() is False
        assert attempt.is_successful() is False
        assert attempt.is_failed() is False
        assert attempt.is_cancelled() is True

    def test_in_progress_attempt(self):
        """Test an attempt currently in progress."""
        attempt = _make_attempt(status="in_progress", conclusion=None)
        assert attempt.is_terminal() is False
        assert attempt.is_running() is True
        assert attempt.is_successful() is False
        assert attempt.is_failed() is False
        assert attempt.is_cancelled() is False

    def test_queued_attempt(self):
        """Test a queued attempt."""
        attempt = _make_attempt(status="queued", conclusion=None)
        assert attempt.is_terminal() is False
        assert attempt.is_running() is False
        assert attempt.is_successful() is False
        assert attempt.is_failed() is False
        assert attempt.is_cancelled() is False
