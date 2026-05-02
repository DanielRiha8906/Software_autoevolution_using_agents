import pytest
from datetime import datetime, timezone, timedelta

from src.models.workflow_run_attempt import WorkflowRunAttempt


def _make_attempt(
    attempt_id: int = 1,
    run_id: str = "run-1",
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
) -> WorkflowRunAttempt:
    """Helper function to create a WorkflowRunAttempt for testing."""
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
    )


def test_workflow_run_attempt_creation():
    """Test basic instantiation of WorkflowRunAttempt with all fields."""
    now = datetime.now(timezone.utc)
    attempt = WorkflowRunAttempt(
        id=1,
        run_id="run-1",
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=now,
    )
    assert attempt.id == 1
    assert attempt.run_id == "run-1"
    assert attempt.attempt_number == 1
    assert attempt.status == "completed"
    assert attempt.conclusion == "success"
    assert attempt.created_at == now


def test_workflow_run_attempt_with_conclusion():
    """Test WorkflowRunAttempt creation with conclusion value."""
    attempt = _make_attempt(conclusion="failure")
    assert attempt.conclusion == "failure"
    assert attempt.status == "completed"


def test_workflow_run_attempt_to_dict():
    """Test serialization of WorkflowRunAttempt to dict with datetime to ISO format."""
    now = datetime.now(timezone.utc)
    attempt = WorkflowRunAttempt(
        id=1,
        run_id="run-1",
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=now,
    )
    data = attempt.to_dict()
    assert data["id"] == 1
    assert data["run_id"] == "run-1"
    assert data["attempt_number"] == 1
    assert data["status"] == "completed"
    assert data["conclusion"] == "success"
    assert data["created_at"] == now.isoformat()
    assert isinstance(data["created_at"], str)


def test_workflow_run_attempt_to_dict_with_none_conclusion():
    """Test serialization of WorkflowRunAttempt to dict when conclusion is None."""
    now = datetime.now(timezone.utc)
    attempt = WorkflowRunAttempt(
        id=1,
        run_id="run-1",
        attempt_number=1,
        status="in_progress",
        conclusion=None,
        created_at=now,
    )
    data = attempt.to_dict()
    assert data["conclusion"] is None
    assert data["status"] == "in_progress"


def test_workflow_run_attempt_from_dict():
    """Test deserialization of WorkflowRunAttempt from dict."""
    now = datetime.now(timezone.utc)
    data = {
        "id": 1,
        "run_id": "run-1",
        "attempt_number": 1,
        "status": "completed",
        "conclusion": "success",
        "created_at": now.isoformat(),
    }
    attempt = WorkflowRunAttempt.from_dict(data)
    assert attempt.id == 1
    assert attempt.run_id == "run-1"
    assert attempt.attempt_number == 1
    assert attempt.status == "completed"
    assert attempt.conclusion == "success"
    assert attempt.created_at == now


def test_workflow_run_attempt_from_dict_with_none_conclusion():
    """Test deserialization of WorkflowRunAttempt from dict with None conclusion."""
    now = datetime.now(timezone.utc)
    data = {
        "id": 1,
        "run_id": "run-1",
        "attempt_number": 1,
        "status": "in_progress",
        "conclusion": None,
        "created_at": now.isoformat(),
    }
    attempt = WorkflowRunAttempt.from_dict(data)
    assert attempt.conclusion is None
    assert attempt.status == "in_progress"


def test_workflow_run_attempt_roundtrip_serialization():
    """Test full cycle serialization and deserialization of WorkflowRunAttempt."""
    now = datetime.now(timezone.utc)
    original = WorkflowRunAttempt(
        id=42,
        run_id="run-xyz",
        attempt_number=3,
        status="completed",
        conclusion="skipped",
        created_at=now,
    )
    data = original.to_dict()
    restored = WorkflowRunAttempt.from_dict(data)
    assert restored.id == original.id
    assert restored.run_id == original.run_id
    assert restored.attempt_number == original.attempt_number
    assert restored.status == original.status
    assert restored.conclusion == original.conclusion
    assert restored.created_at == original.created_at


def test_workflow_run_attempt_relationship_to_workflow_run():
    """Test that run_id properly links WorkflowRunAttempt to WorkflowRun."""
    attempt1 = WorkflowRunAttempt(
        id=1,
        run_id="run-1",
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )
    attempt2 = WorkflowRunAttempt(
        id=2,
        run_id="run-1",
        attempt_number=2,
        status="completed",
        conclusion="failure",
        created_at=datetime.now(timezone.utc),
    )
    assert attempt1.run_id == attempt2.run_id
    assert attempt1.attempt_number != attempt2.attempt_number


def test_workflow_run_attempt_list_for_run():
    """Test multiple attempts per run."""
    attempts = [
        WorkflowRunAttempt(
            id=i,
            run_id="run-1",
            attempt_number=i,
            status="completed" if i < 3 else "in_progress",
            conclusion="failure" if i < 3 else None,
            created_at=datetime.now(timezone.utc),
        )
        for i in range(1, 4)
    ]
    run_id = "run-1"
    run_attempts = [a for a in attempts if a.run_id == run_id]
    assert len(run_attempts) == 3
    assert all(a.run_id == run_id for a in run_attempts)
    assert run_attempts[0].attempt_number == 1
    assert run_attempts[2].attempt_number == 3


def test_workflow_run_attempt_datetime_timezone_preserved():
    """Test that CEST timezone is preserved through serialization roundtrip."""
    cest = timezone(timedelta(hours=2))
    now = datetime(2024, 5, 2, 14, 30, 45, tzinfo=cest)
    attempt = WorkflowRunAttempt(
        id=1,
        run_id="run-1",
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=now,
    )
    data = attempt.to_dict()
    restored = WorkflowRunAttempt.from_dict(data)
    assert restored.created_at == now
    assert restored.created_at.tzinfo == cest
    assert restored.created_at.isoformat() == now.isoformat()
