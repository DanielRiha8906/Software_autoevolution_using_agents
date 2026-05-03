import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.attempt_service import AttemptService


def _make_attempt(
    attempt_id: int = 1,
    run_id: int = 1,
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
) -> WorkflowRunAttempt:
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        duration_seconds=5.0,
    )


@pytest.fixture
def service():
    storage = MagicMock()
    storage.load.return_value = []
    svc = AttemptService(storage)
    return svc


def test_add_and_list(service):
    attempt = _make_attempt()
    service.add_workflow_attempt(attempt)
    assert service.list_attempts() == [attempt]


def test_add_duplicate_raises(service):
    attempt = _make_attempt(run_id=1, attempt_number=1)
    service.add_workflow_attempt(attempt)
    with pytest.raises(ValueError, match="already exists"):
        service.add_workflow_attempt(attempt)


def test_get_attempts_by_run_id(service):
    a1 = _make_attempt(attempt_id=1, run_id=1, attempt_number=1)
    a2 = _make_attempt(attempt_id=2, run_id=1, attempt_number=2)
    a3 = _make_attempt(attempt_id=3, run_id=2, attempt_number=1)

    service.add_workflow_attempt(a1)
    service.add_workflow_attempt(a2)
    service.add_workflow_attempt(a3)

    run1_attempts = service.get_attempts_by_run_id(1)
    run2_attempts = service.get_attempts_by_run_id(2)

    assert run1_attempts == [a1, a2]
    assert run2_attempts == [a3]


def test_multiple_attempts_per_run_allowed(service):
    a1 = _make_attempt(attempt_id=1, run_id=1, attempt_number=1)
    a2 = _make_attempt(attempt_id=2, run_id=1, attempt_number=2)

    service.add_workflow_attempt(a1)
    service.add_workflow_attempt(a2)

    attempts = service.get_attempts_by_run_id(1)
    assert len(attempts) == 2


def test_different_runs_can_have_same_attempt_number(service):
    a1 = _make_attempt(attempt_id=1, run_id=1, attempt_number=1)
    a2 = _make_attempt(attempt_id=2, run_id=2, attempt_number=1)

    service.add_workflow_attempt(a1)
    service.add_workflow_attempt(a2)

    assert service.get_attempts_by_run_id(1) == [a1]
    assert service.get_attempts_by_run_id(2) == [a2]


def test_empty_run_id_returns_empty_list(service):
    a1 = _make_attempt(attempt_id=1, run_id=1, attempt_number=1)
    service.add_workflow_attempt(a1)

    attempts = service.get_attempts_by_run_id(999)
    assert attempts == []


def test_persist_called_on_add(service):
    attempt = _make_attempt()
    service.add_workflow_attempt(attempt)
    service._storage.save.assert_called_once()


def test_add_with_none_conclusion(service):
    attempt = _make_attempt(conclusion=None)
    service.add_workflow_attempt(attempt)
    assert service.list_attempts()[0].conclusion is None


def test_duplicate_check_respects_run_id(service):
    a1 = _make_attempt(attempt_id=1, run_id=1, attempt_number=1)
    a2 = _make_attempt(attempt_id=2, run_id=2, attempt_number=1)
    service.add_workflow_attempt(a1)
    service.add_workflow_attempt(a2)

    # Try to add duplicate of a1
    a1_dup = _make_attempt(attempt_id=3, run_id=1, attempt_number=1)
    with pytest.raises(ValueError, match="already exists"):
        service.add_workflow_attempt(a1_dup)
