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
    duration_seconds: float = 10.5,
) -> WorkflowRunAttempt:
    """Helper to create a WorkflowRunAttempt instance."""
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
    """Create a service with a mocked storage."""
    storage = MagicMock()
    storage.load.return_value = []
    svc = AttemptService(storage)
    return svc


class TestAttemptServiceCreation:
    """Tests for creating attempts via the service."""

    def test_create_attempt(self, service):
        """Test creating a single attempt."""
        attempt = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        result = service.create_attempt(attempt)
        assert result == attempt
        assert result.id == 1
        assert result.run_id == 100
        assert result.attempt_number == 1

    def test_create_multiple_attempts_same_run(self, service):
        """Test creating multiple attempts for the same run with different attempt numbers."""
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        service.create_attempt(attempt1)
        service.create_attempt(attempt2)
        attempts = service.get_attempts_for_run(100)
        assert len(attempts) == 2
        assert attempts[0] == attempt1
        assert attempts[1] == attempt2

    def test_create_attempts_different_runs(self, service):
        """Test creating attempts for different runs."""
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=200, attempt_number=1)
        service.create_attempt(attempt1)
        service.create_attempt(attempt2)
        assert service.get_attempts_for_run(100) == [attempt1]
        assert service.get_attempts_for_run(200) == [attempt2]


class TestAttemptServiceDuplicatePrevention:
    """Tests for preventing duplicate attempts."""

    def test_duplicate_attempt_same_run_and_number_raises(self, service):
        """Test that creating an attempt with duplicate (run_id, attempt_number) raises ValueError."""
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=1)
        service.create_attempt(attempt1)
        with pytest.raises(ValueError, match="already exists"):
            service.create_attempt(attempt2)

    def test_duplicate_run_id_different_attempt_number_allowed(self, service):
        """Test that same run_id with different attempt_number is allowed."""
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        service.create_attempt(attempt1)
        # Should not raise
        service.create_attempt(attempt2)
        assert len(service.get_attempts_for_run(100)) == 2

    def test_duplicate_attempt_number_different_run_allowed(self, service):
        """Test that same attempt_number with different run_id is allowed."""
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=200, attempt_number=1)
        service.create_attempt(attempt1)
        # Should not raise
        service.create_attempt(attempt2)
        assert service.get_attempts_for_run(100) == [attempt1]
        assert service.get_attempts_for_run(200) == [attempt2]


class TestAttemptServiceRetrieval:
    """Tests for retrieving attempts."""

    def test_get_attempts_for_run_empty(self, service):
        """Test getting attempts for a run with no attempts."""
        attempts = service.get_attempts_for_run(100)
        assert attempts == []

    def test_get_attempts_for_run_single(self, service):
        """Test getting attempts for a run with one attempt."""
        attempt = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        service.create_attempt(attempt)
        attempts = service.get_attempts_for_run(100)
        assert len(attempts) == 1
        assert attempts[0] == attempt

    def test_get_attempts_for_run_multiple(self, service):
        """Test getting attempts for a run with multiple attempts."""
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        attempt3 = _make_attempt(attempt_id=3, run_id=100, attempt_number=3)
        service.create_attempt(attempt1)
        service.create_attempt(attempt2)
        service.create_attempt(attempt3)
        attempts = service.get_attempts_for_run(100)
        assert len(attempts) == 3
        assert attempts == [attempt1, attempt2, attempt3]


class TestAttemptServiceSorting:
    """Tests for sorting attempts by attempt_number."""

    def test_get_attempts_sorted_by_attempt_number(self, service):
        """Test that attempts are returned sorted by attempt_number in ascending order."""
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        attempt3 = _make_attempt(attempt_id=3, run_id=100, attempt_number=3)
        # Create in non-sequential order
        service.create_attempt(attempt3)
        service.create_attempt(attempt1)
        service.create_attempt(attempt2)
        attempts = service.get_attempts_for_run(100)
        # Should be sorted by attempt_number
        assert attempts[0].attempt_number == 1
        assert attempts[1].attempt_number == 2
        assert attempts[2].attempt_number == 3

    def test_get_attempts_unsorted_insertion(self, service):
        """Test that insertion order doesn't affect the sort in returned list."""
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=5)
        attempt2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        attempt3 = _make_attempt(attempt_id=3, run_id=100, attempt_number=8)
        service.create_attempt(attempt1)
        service.create_attempt(attempt2)
        service.create_attempt(attempt3)
        attempts = service.get_attempts_for_run(100)
        assert attempts[0].attempt_number == 2
        assert attempts[1].attempt_number == 5
        assert attempts[2].attempt_number == 8

    def test_get_attempts_maintains_insertion_order_in_storage(self, service):
        """Test that storage is persisted correctly."""
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        service.create_attempt(attempt1)
        service.create_attempt(attempt2)
        # Verify internal storage has both
        assert len(service._attempts) == 2


class TestAttemptServiceStorageIntegration:
    """Tests for integration with storage layer."""

    def test_storage_save_called_on_create(self, service):
        """Test that storage.save is called when creating an attempt."""
        attempt = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        service.create_attempt(attempt)
        service._storage.save.assert_called_once()

    def test_storage_load_called_on_init(self):
        """Test that storage.load is called during initialization."""
        storage = MagicMock()
        storage.load.return_value = []
        service = AttemptService(storage)
        storage.load.assert_called_once()

    def test_service_loads_existing_attempts_on_init(self):
        """Test that service loads existing attempts from storage on init."""
        attempt1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)
        storage = MagicMock()
        storage.load.return_value = [attempt1, attempt2]
        service = AttemptService(storage)
        attempts = service.get_attempts_for_run(100)
        assert len(attempts) == 2
        assert attempts[0] == attempt1
        assert attempts[1] == attempt2


class TestAttemptServiceEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_get_attempts_for_nonexistent_run(self, service):
        """Test getting attempts for a run that doesn't exist."""
        attempts = service.get_attempts_for_run(999)
        assert attempts == []

    def test_create_attempt_with_none_conclusion(self, service):
        """Test creating an attempt with None conclusion."""
        attempt = _make_attempt(attempt_id=1, run_id=100, attempt_number=1, conclusion=None)
        result = service.create_attempt(attempt)
        assert result.conclusion is None

    def test_create_attempt_with_various_statuses(self, service):
        """Test creating attempts with various status values."""
        statuses = ["queued", "in_progress", "completed", "waiting"]
        for i, status in enumerate(statuses, 1):
            attempt = _make_attempt(attempt_id=i, run_id=100, attempt_number=i, status=status)
            result = service.create_attempt(attempt)
            assert result.status == status

    def test_create_attempt_with_large_values(self, service):
        """Test creating attempts with large ID and run_id values."""
        attempt = _make_attempt(attempt_id=9999999999, run_id=9999999999, attempt_number=100)
        result = service.create_attempt(attempt)
        assert result.id == 9999999999
        assert result.run_id == 9999999999

    def test_multiple_runs_with_attempts(self, service):
        """Test service with multiple runs, each having multiple attempts."""
        # Run 100 with 3 attempts
        for i in range(1, 4):
            attempt = _make_attempt(attempt_id=i, run_id=100, attempt_number=i)
            service.create_attempt(attempt)
        # Run 200 with 2 attempts
        for i in range(1, 3):
            attempt = _make_attempt(attempt_id=100 + i, run_id=200, attempt_number=i)
            service.create_attempt(attempt)
        # Verify separation
        run100_attempts = service.get_attempts_for_run(100)
        run200_attempts = service.get_attempts_for_run(200)
        assert len(run100_attempts) == 3
        assert len(run200_attempts) == 2
        assert all(a.run_id == 100 for a in run100_attempts)
        assert all(a.run_id == 200 for a in run200_attempts)

    def test_get_attempts_does_not_modify_internal_state(self, service):
        """Test that getting attempts doesn't modify the service state."""
        attempt = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        service.create_attempt(attempt)
        attempts1 = service.get_attempts_for_run(100)
        attempts2 = service.get_attempts_for_run(100)
        assert attempts1 == attempts2
        assert len(service._attempts) == 1


class TestAttemptServicePersistence:
    """Tests for persistence behavior."""

    def test_persist_called_on_create(self, service):
        """Test that _persist is called when creating an attempt."""
        attempt = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        service.create_attempt(attempt)
        # Verify storage.save was called (it's called in _persist)
        assert service._storage.save.called

    def test_attempt_remains_after_retrieval(self, service):
        """Test that attempts persist in memory after retrieval."""
        attempt = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        service.create_attempt(attempt)
        service.get_attempts_for_run(100)
        service.get_attempts_for_run(100)
        # Attempt should still be there
        assert len(service._attempts) == 1
