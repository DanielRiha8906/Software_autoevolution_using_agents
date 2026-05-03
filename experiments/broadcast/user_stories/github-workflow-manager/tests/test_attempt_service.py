import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.attempt_service import AttemptService


def _make_attempt(
    attempt_id: int = 1,
    run_id: int = 100,
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
    created_at: datetime = None,
    duration_seconds: float = None,
) -> WorkflowRunAttempt:
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


@pytest.fixture
def service():
    storage = MagicMock()
    storage.load.return_value = []
    svc = AttemptService(storage)
    return svc


class TestAttemptServiceCreate:
    def test_create_attempt(self, service):
        attempt = _make_attempt()
        result = service.create_attempt(attempt)
        assert result is attempt
        assert attempt in service.list_all_attempts()

    def test_create_multiple_attempts_same_run_different_numbers(self, service):
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        service.create_attempt(attempt1)
        service.create_attempt(attempt2)
        assert len(service.list_all_attempts()) == 2

    def test_create_duplicate_attempt_raises(self, service):
        attempt = _make_attempt(run_id=100, attempt_number=1)
        service.create_attempt(attempt)
        with pytest.raises(ValueError, match="already exists"):
            service.create_attempt(attempt)

    def test_create_same_attempt_number_different_runs(self, service):
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=200, attempt_number=1)
        service.create_attempt(attempt1)
        service.create_attempt(attempt2)
        assert len(service.list_all_attempts()) == 2


class TestAttemptServiceRetrieve:
    def test_get_attempts_for_run_empty(self, service):
        attempts = service.get_attempts_for_run(999)
        assert attempts == []

    def test_get_attempts_for_run_single(self, service):
        attempt = _make_attempt(run_id=100, attempt_number=1)
        service.create_attempt(attempt)
        attempts = service.get_attempts_for_run(100)
        assert attempts == [attempt]

    def test_get_attempts_for_run_multiple_sorted(self, service):
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=3)
        attempt2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=1)
        attempt3 = _make_attempt(attempt_id=3, run_id=100, attempt_number=2)
        service.create_attempt(attempt1)
        service.create_attempt(attempt2)
        service.create_attempt(attempt3)
        attempts = service.get_attempts_for_run(100)
        assert len(attempts) == 3
        assert attempts[0].attempt_number == 1
        assert attempts[1].attempt_number == 2
        assert attempts[2].attempt_number == 3

    def test_get_attempts_for_run_filters_by_run_id(self, service):
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=200, attempt_number=1)
        service.create_attempt(attempt1)
        service.create_attempt(attempt2)
        attempts_100 = service.get_attempts_for_run(100)
        attempts_200 = service.get_attempts_for_run(200)
        assert attempts_100 == [attempt1]
        assert attempts_200 == [attempt2]

    def test_list_all_attempts_empty(self, service):
        assert service.list_all_attempts() == []

    def test_list_all_attempts(self, service):
        attempt1 = _make_attempt(attempt_id=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=200)
        service.create_attempt(attempt1)
        service.create_attempt(attempt2)
        all_attempts = service.list_all_attempts()
        assert len(all_attempts) == 2
        assert attempt1 in all_attempts
        assert attempt2 in all_attempts


class TestAttemptServicePersistence:
    def test_create_calls_persist(self, service):
        attempt = _make_attempt()
        service.create_attempt(attempt)
        service._storage.save.assert_called()

    def test_persistence_integration(self):
        storage = MagicMock()
        storage.load.return_value = []
        service = AttemptService(storage)
        attempt = _make_attempt()
        service.create_attempt(attempt)
        # Verify that the storage.save was called with attempts list
        service._storage.save.assert_called_once()
