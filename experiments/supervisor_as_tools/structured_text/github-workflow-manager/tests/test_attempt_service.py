import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.attempt_service import AttemptService


def _make_attempt(
    attempt_id: int = 1,
    run_id: int = 42,
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


def test_create_attempt(service):
    attempt = service.create_attempt(
        run_id=42,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
        duration_seconds=5.0,
    )
    assert attempt.id == 1
    assert attempt.run_id == 42
    assert attempt.attempt_number == 1


def test_create_attempt_auto_increments_id(service):
    attempt1 = service.create_attempt(
        run_id=42,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )
    assert attempt1.id == 1

    attempt2 = service.create_attempt(
        run_id=42,
        attempt_number=2,
        status="completed",
        conclusion="failure",
        created_at=datetime.now(timezone.utc),
    )
    assert attempt2.id == 2


def test_create_attempt_duplicate_composite_key_raises(service):
    service.create_attempt(
        run_id=42,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )
    with pytest.raises(ValueError, match="already exists"):
        service.create_attempt(
            run_id=42,
            attempt_number=1,
            status="completed",
            conclusion="failure",
            created_at=datetime.now(timezone.utc),
        )


def test_list_attempts(service):
    attempt = service.create_attempt(
        run_id=42,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )
    assert service.list_attempts() == [attempt]


def test_get_attempts_by_run_id(service):
    a1 = service.create_attempt(
        run_id=42,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )
    a2 = service.create_attempt(
        run_id=42,
        attempt_number=2,
        status="completed",
        conclusion="failure",
        created_at=datetime.now(timezone.utc),
    )
    a3 = service.create_attempt(
        run_id=99,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )

    # Should return only attempts with run_id=42
    attempts_42 = service.get_attempts_by_run_id(42)
    assert len(attempts_42) == 2
    assert a1 in attempts_42
    assert a2 in attempts_42
    assert a3 not in attempts_42


def test_get_attempts_by_run_id_sorted_by_attempt_number(service):
    a2 = service.create_attempt(
        run_id=42,
        attempt_number=2,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )
    a1 = service.create_attempt(
        run_id=42,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )
    a3 = service.create_attempt(
        run_id=42,
        attempt_number=3,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )

    # Should be sorted by attempt_number ascending
    attempts = service.get_attempts_by_run_id(42)
    assert attempts[0].attempt_number == 1
    assert attempts[1].attempt_number == 2
    assert attempts[2].attempt_number == 3


def test_get_attempt_detail(service):
    attempt = service.create_attempt(
        run_id=42,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(timezone.utc),
    )
    assert service.get_attempt_detail(1) == attempt
    assert service.get_attempt_detail(99) is None
