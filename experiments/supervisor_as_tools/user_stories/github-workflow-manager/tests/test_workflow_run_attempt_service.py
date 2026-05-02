import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.attempt_run_status import RunAttemptStatus
from src.models.attempt_run_conclusion import RunAttemptConclusion
from src.services.workflow_run_attempt_service import WorkflowRunAttemptService


def _make_attempt(
    id: int = 1,
    run_id: int = 1,
    attempt_number: int = 1,
    status: RunAttemptStatus = RunAttemptStatus.COMPLETED,
    conclusion: RunAttemptConclusion = RunAttemptConclusion.SUCCESS,
    duration_seconds: float = None,
) -> WorkflowRunAttempt:
    return WorkflowRunAttempt(
        id=id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def service():
    storage = MagicMock()
    storage.load.return_value = []
    svc = WorkflowRunAttemptService(storage)
    return svc


def test_add_and_list(service):
    attempt = _make_attempt()
    service.add_workflow_run_attempt(attempt)
    assert service.list_attempts() == [attempt]


def test_add_duplicate_composite_key_raises(service):
    attempt = _make_attempt(id=1, run_id=1, attempt_number=1)
    service.add_workflow_run_attempt(attempt)
    with pytest.raises(ValueError):
        service.add_workflow_run_attempt(_make_attempt(id=2, run_id=1, attempt_number=1))


def test_get_attempt_by_run_and_number(service):
    attempt = _make_attempt(id=1, run_id=1, attempt_number=1)
    service.add_workflow_run_attempt(attempt)
    assert service.get_attempt(1, 1) is attempt
    assert service.get_attempt(1, 2) is None
    assert service.get_attempt(2, 1) is None


def test_list_attempts_by_run_id(service):
    a1 = _make_attempt(id=1, run_id=1, attempt_number=1)
    a2 = _make_attempt(id=2, run_id=1, attempt_number=2)
    a3 = _make_attempt(id=3, run_id=2, attempt_number=1)
    service.add_workflow_run_attempt(a1)
    service.add_workflow_run_attempt(a2)
    service.add_workflow_run_attempt(a3)
    assert service.list_attempts_by_run_id(1) == [a1, a2]
    assert service.list_attempts_by_run_id(2) == [a3]
    assert service.list_attempts_by_run_id(999) == []


def test_filter_by_status(service):
    a1 = _make_attempt(id=1, run_id=1, attempt_number=1, status=RunAttemptStatus.COMPLETED)
    a2 = _make_attempt(id=2, run_id=1, attempt_number=2, status=RunAttemptStatus.IN_PROGRESS)
    service.add_workflow_run_attempt(a1)
    service.add_workflow_run_attempt(a2)
    assert service.filter_by_status(RunAttemptStatus.COMPLETED) == [a1]
    assert service.filter_by_status(RunAttemptStatus.IN_PROGRESS) == [a2]
    assert service.filter_by_status(RunAttemptStatus.QUEUED) == []


def test_filter_by_conclusion(service):
    a1 = _make_attempt(id=1, run_id=1, attempt_number=1, conclusion=RunAttemptConclusion.SUCCESS)
    a2 = _make_attempt(id=2, run_id=1, attempt_number=2, conclusion=RunAttemptConclusion.FAILURE)
    service.add_workflow_run_attempt(a1)
    service.add_workflow_run_attempt(a2)
    assert service.filter_by_conclusion(RunAttemptConclusion.SUCCESS) == [a1]
    assert service.filter_by_conclusion(RunAttemptConclusion.FAILURE) == [a2]
    assert service.filter_by_conclusion(RunAttemptConclusion.CANCELLED) == []


def test_workflow_run_attempt_to_dict(service):
    attempt = _make_attempt(id=1, run_id=5, attempt_number=3, duration_seconds=12.5)
    attempt_dict = attempt.to_dict()
    assert attempt_dict["id"] == 1
    assert attempt_dict["run_id"] == 5
    assert attempt_dict["attempt_number"] == 3
    assert attempt_dict["status"] == "completed"
    assert attempt_dict["conclusion"] == "success"
    assert attempt_dict["duration_seconds"] == 12.5
    assert "created_at" in attempt_dict


def test_workflow_run_attempt_from_dict(service):
    data = {
        "id": 1,
        "run_id": 5,
        "attempt_number": 3,
        "status": "in_progress",
        "conclusion": "failure",
        "created_at": "2024-01-01T12:00:00+00:00",
        "duration_seconds": 25.5,
    }
    attempt = WorkflowRunAttempt.from_dict(data)
    assert attempt.id == 1
    assert attempt.run_id == 5
    assert attempt.attempt_number == 3
    assert attempt.status == RunAttemptStatus.IN_PROGRESS
    assert attempt.conclusion == RunAttemptConclusion.FAILURE
    assert attempt.duration_seconds == 25.5


def test_attempt_number_must_be_positive():
    with pytest.raises(ValueError, match="attempt_number must be positive integer >= 1"):
        _make_attempt(attempt_number=0)


def test_attempt_number_zero_raises():
    with pytest.raises(ValueError, match="attempt_number must be positive integer >= 1"):
        _make_attempt(attempt_number=-1)


def test_serialize_roundtrip(service):
    original = _make_attempt(id=7, run_id=3, attempt_number=2, duration_seconds=99.9)
    data = original.to_dict()
    restored = WorkflowRunAttempt.from_dict(data)
    assert restored.id == original.id
    assert restored.run_id == original.run_id
    assert restored.attempt_number == original.attempt_number
    assert restored.status == original.status
    assert restored.conclusion == original.conclusion
    assert restored.duration_seconds == original.duration_seconds
