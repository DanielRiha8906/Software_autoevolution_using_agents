import pytest
from datetime import datetime, timezone, timedelta

from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.attempt_service import AttemptService


CEST = timezone(timedelta(hours=2))


def _attempt(**kwargs):
    defaults = dict(
        id=1,
        run_id=42,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(CEST),
    )
    defaults.update(kwargs)
    return WorkflowRunAttempt(**defaults)


@pytest.fixture
def service():
    return AttemptService()


def test_constructor_exists():
    service = AttemptService()
    assert service is not None


def test_create_stores_attempt(service):
    attempt = _attempt()
    service.create(attempt)
    # Verify we can retrieve it
    attempts = service.get_by_run_id(42)
    assert len(attempts) == 1
    assert attempts[0] == attempt


def test_create_raises_on_duplicate(service):
    attempt1 = _attempt(run_id=42, attempt_number=1)
    attempt2 = _attempt(run_id=42, attempt_number=1, id=2)

    service.create(attempt1)
    with pytest.raises(Exception):
        service.create(attempt2)


def test_get_by_run_id_returns_empty_list_when_not_found(service):
    attempts = service.get_by_run_id(999)
    assert attempts == []


def test_get_by_run_id_returns_sorted_by_attempt_number(service):
    attempt1 = _attempt(run_id=42, attempt_number=3)
    attempt2 = _attempt(run_id=42, attempt_number=1, id=2)
    attempt3 = _attempt(run_id=42, attempt_number=2, id=3)

    service.create(attempt1)
    service.create(attempt2)
    service.create(attempt3)

    attempts = service.get_by_run_id(42)
    assert len(attempts) == 3
    assert attempts[0].attempt_number == 1
    assert attempts[1].attempt_number == 2
    assert attempts[2].attempt_number == 3


def test_get_by_run_id_returns_only_matching_run_id(service):
    attempt1 = _attempt(run_id=42, attempt_number=1)
    attempt2 = _attempt(run_id=43, attempt_number=1, id=2)

    service.create(attempt1)
    service.create(attempt2)

    attempts_42 = service.get_by_run_id(42)
    attempts_43 = service.get_by_run_id(43)

    assert len(attempts_42) == 1
    assert attempts_42[0].run_id == 42
    assert len(attempts_43) == 1
    assert attempts_43[0].run_id == 43


def test_multiple_creates_with_different_run_ids(service):
    attempt1 = _attempt(run_id=42, attempt_number=1)
    attempt2 = _attempt(run_id=43, attempt_number=1, id=2)
    attempt3 = _attempt(run_id=42, attempt_number=2, id=3)

    service.create(attempt1)
    service.create(attempt2)
    service.create(attempt3)

    assert len(service.get_by_run_id(42)) == 2
    assert len(service.get_by_run_id(43)) == 1
