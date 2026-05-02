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
    duration_seconds: float = 0.0,
) -> WorkflowRunAttempt:
    """Helper to create a test WorkflowRunAttempt."""
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def service():
    """Create a service with mocked storage."""
    storage = MagicMock()
    storage.load.return_value = []
    return AttemptService(storage)


@pytest.fixture
def service_with_data():
    """Create a service with pre-loaded data."""
    storage = MagicMock()
    attempts = [
        _make_attempt(attempt_id=1, run_id=100, attempt_number=1),
        _make_attempt(attempt_id=2, run_id=100, attempt_number=2),
        _make_attempt(attempt_id=3, run_id=101, attempt_number=1),
    ]
    storage.load.return_value = attempts
    return AttemptService(storage)


class TestAttemptServiceAddition:
    """Test adding attempts to the service."""

    def test_add_and_list(self, service):
        """Test adding an attempt and listing."""
        attempt = _make_attempt()
        service.add_attempt(attempt)

        assert service.list_attempts() == [attempt]

    def test_add_multiple_attempts(self, service):
        """Test adding multiple attempts."""
        a1 = _make_attempt(attempt_id=1, attempt_number=1)
        a2 = _make_attempt(attempt_id=2, attempt_number=2)
        a3 = _make_attempt(attempt_id=3, attempt_number=3)

        service.add_attempt(a1)
        service.add_attempt(a2)
        service.add_attempt(a3)

        attempts = service.list_attempts()
        assert len(attempts) == 3
        assert attempts[0].id == 1
        assert attempts[1].id == 2
        assert attempts[2].id == 3

    def test_add_persists_to_storage(self, service):
        """Test that adding an attempt calls persist."""
        attempt = _make_attempt()
        service.add_attempt(attempt)

        service._storage.save.assert_called_once()

    def test_add_returns_attempt(self, service):
        """Test that add_attempt returns the added attempt."""
        attempt = _make_attempt()
        result = service.add_attempt(attempt)

        assert result is attempt


class TestAttemptServiceUniqueness:
    """Test uniqueness constraint enforcement."""

    def test_duplicate_run_id_attempt_number_raises(self, service):
        """Test that duplicate (run_id, attempt_number) pair raises ValueError."""
        a1 = _make_attempt(run_id=100, attempt_number=1)
        a2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=1)

        service.add_attempt(a1)

        with pytest.raises(ValueError) as exc_info:
            service.add_attempt(a2)

        assert "already exists" in str(exc_info.value)
        assert "100" in str(exc_info.value)  # run_id
        assert "1" in str(exc_info.value)  # attempt_number

    def test_same_run_different_attempt_allowed(self, service):
        """Test that same run_id with different attempt_number is allowed."""
        a1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        a2 = _make_attempt(attempt_id=2, run_id=100, attempt_number=2)

        service.add_attempt(a1)
        service.add_attempt(a2)  # Should not raise

        assert len(service.list_attempts()) == 2

    def test_same_attempt_number_different_run_allowed(self, service):
        """Test that same attempt_number in different runs is allowed."""
        a1 = _make_attempt(attempt_id=1, run_id=100, attempt_number=1)
        a2 = _make_attempt(attempt_id=2, run_id=101, attempt_number=1)

        service.add_attempt(a1)
        service.add_attempt(a2)  # Should not raise

        assert len(service.list_attempts()) == 2

    def test_many_attempts_same_run(self, service):
        """Test adding many attempts to the same run."""
        for i in range(1, 11):
            attempt = _make_attempt(
                attempt_id=i,
                run_id=100,
                attempt_number=i,
            )
            service.add_attempt(attempt)

        assert len(service.list_attempts()) == 10

    def test_uniqueness_error_message_format(self, service):
        """Test error message contains run_id and attempt_number."""
        a1 = _make_attempt(run_id=42, attempt_number=3)
        a2 = _make_attempt(attempt_id=2, run_id=42, attempt_number=3)

        service.add_attempt(a1)

        with pytest.raises(ValueError) as exc_info:
            service.add_attempt(a2)

        error_msg = str(exc_info.value)
        assert "3" in error_msg
        assert "42" in error_msg


class TestAttemptServiceRetrieval:
    """Test retrieval operations."""

    def test_list_attempts(self, service_with_data):
        """Test listing all attempts."""
        attempts = service_with_data.list_attempts()

        assert len(attempts) == 3
        assert attempts[0].id == 1
        assert attempts[1].id == 2
        assert attempts[2].id == 3

    def test_list_returns_copy(self, service_with_data):
        """Test that list_attempts returns a copy, not the original."""
        list1 = service_with_data.list_attempts()
        list2 = service_with_data.list_attempts()

        assert list1 == list2
        assert list1 is not list2

    def test_get_attempt_by_id_found(self, service_with_data):
        """Test retrieving an attempt by ID."""
        attempt = service_with_data.get_attempt_by_id(2)

        assert attempt is not None
        assert attempt.id == 2
        assert attempt.run_id == 100

    def test_get_attempt_by_id_not_found(self, service_with_data):
        """Test retrieving non-existent attempt returns None."""
        attempt = service_with_data.get_attempt_by_id(999)

        assert attempt is None

    def test_get_attempt_by_id_first(self, service_with_data):
        """Test retrieving first attempt."""
        attempt = service_with_data.get_attempt_by_id(1)

        assert attempt.attempt_number == 1

    def test_get_attempt_by_id_last(self, service_with_data):
        """Test retrieving last attempt."""
        attempt = service_with_data.get_attempt_by_id(3)

        assert attempt.run_id == 101


class TestAttemptServiceFilterByRun:
    """Test filtering by run_id."""

    def test_filter_by_run_single_result(self, service_with_data):
        """Test filtering for run with multiple attempts."""
        attempts = service_with_data.filter_by_run(100)

        assert len(attempts) == 2
        assert all(a.run_id == 100 for a in attempts)
        assert [a.attempt_number for a in attempts] == [1, 2]

    def test_filter_by_run_single_attempt(self, service_with_data):
        """Test filtering for run with single attempt."""
        attempts = service_with_data.filter_by_run(101)

        assert len(attempts) == 1
        assert attempts[0].id == 3

    def test_filter_by_run_no_match(self, service_with_data):
        """Test filtering for non-existent run."""
        attempts = service_with_data.filter_by_run(999)

        assert attempts == []

    def test_filter_by_run_returns_copy(self, service_with_data):
        """Test that filter results are a list, not reference."""
        attempts = service_with_data.filter_by_run(100)

        assert isinstance(attempts, list)
        assert len(attempts) == 2

    def test_filter_by_run_many_attempts(self, service):
        """Test filtering with many attempts in a run."""
        for i in range(1, 21):
            attempt = _make_attempt(
                attempt_id=i,
                run_id=100,
                attempt_number=i,
            )
            service.add_attempt(attempt)

        attempts = service.filter_by_run(100)
        assert len(attempts) == 20

    def test_filter_by_run_multiple_runs(self, service):
        """Test filtering with multiple runs."""
        for run_id in range(100, 110):
            for attempt_num in range(1, 4):
                attempt = _make_attempt(
                    attempt_id=run_id * 10 + attempt_num,
                    run_id=run_id,
                    attempt_number=attempt_num,
                )
                service.add_attempt(attempt)

        attempts = service.filter_by_run(105)
        assert len(attempts) == 3
        assert all(a.run_id == 105 for a in attempts)


class TestAttemptServiceFilterByStatus:
    """Test filtering by status."""

    def test_filter_by_status_single_result(self, service):
        """Test filtering by status returns matching attempts."""
        a1 = _make_attempt(attempt_id=1, attempt_number=1, status="completed")
        a2 = _make_attempt(attempt_id=2, attempt_number=2, status="in_progress")
        a3 = _make_attempt(attempt_id=3, attempt_number=3, status="completed")

        service.add_attempt(a1)
        service.add_attempt(a2)
        service.add_attempt(a3)

        attempts = service.filter_by_status("completed")
        assert len(attempts) == 2
        assert all(a.status == "completed" for a in attempts)

    def test_filter_by_status_no_match(self, service):
        """Test filtering for non-existent status."""
        a1 = _make_attempt(status="completed")
        service.add_attempt(a1)

        attempts = service.filter_by_status("in_progress")
        assert attempts == []

    def test_filter_by_status_all_match(self, service):
        """Test filtering when all attempts match."""
        for i in range(1, 6):
            attempt = _make_attempt(attempt_id=i, attempt_number=i, status="completed")
            service.add_attempt(attempt)

        attempts = service.filter_by_status("completed")
        assert len(attempts) == 5

    def test_filter_by_status_various_statuses(self, service):
        """Test filtering with various status values."""
        statuses = ["queued", "in_progress", "completed", "failed", "cancelled"]
        for i, status in enumerate(statuses, 1):
            attempt = _make_attempt(attempt_id=i, attempt_number=i, status=status)
            service.add_attempt(attempt)

        for status in statuses:
            attempts = service.filter_by_status(status)
            assert len(attempts) == 1
            assert attempts[0].status == status

    def test_filter_by_status_case_sensitive(self, service):
        """Test that status filtering is case-sensitive."""
        a1 = _make_attempt(status="completed")
        service.add_attempt(a1)

        attempts = service.filter_by_status("Completed")
        assert attempts == []  # Case-sensitive, no match

    def test_filter_by_status_with_spaces(self, service):
        """Test filtering with status containing spaces."""
        a1 = _make_attempt(status="in progress")
        service.add_attempt(a1)

        attempts = service.filter_by_status("in progress")
        assert len(attempts) == 1


class TestAttemptServicePersistence:
    """Test persistence behavior."""

    def test_persist_called_on_add(self, service):
        """Test that _persist is called when adding."""
        attempt = _make_attempt()
        service.add_attempt(attempt)

        service._storage.save.assert_called()

    def test_persist_saves_all_attempts(self, service):
        """Test that persist saves all attempts."""
        a1 = _make_attempt(attempt_id=1, attempt_number=1)
        a2 = _make_attempt(attempt_id=2, attempt_number=2)

        service.add_attempt(a1)
        service.add_attempt(a2)

        # Check last call to save had both attempts
        last_call = service._storage.save.call_args
        saved_attempts = last_call[0][0]
        assert len(saved_attempts) == 2

    def test_init_loads_from_storage(self):
        """Test that initialization loads from storage."""
        attempts = [
            _make_attempt(attempt_id=1),
            _make_attempt(attempt_id=2),
        ]
        storage = MagicMock()
        storage.load.return_value = attempts

        service = AttemptService(storage)
        assert len(service.list_attempts()) == 2
        assert service.list_attempts()[0].id == 1


class TestAttemptServiceIntegration:
    """Integration tests combining multiple operations."""

    def test_add_multiple_then_filter(self, service):
        """Test adding multiple attempts and filtering."""
        # Add attempts for two runs
        for run_id in [100, 101]:
            for attempt_num in range(1, 4):
                attempt = _make_attempt(
                    attempt_id=run_id * 10 + attempt_num,
                    run_id=run_id,
                    attempt_number=attempt_num,
                    status="completed" if attempt_num % 2 == 0 else "in_progress",
                )
                service.add_attempt(attempt)

        # Filter by run
        run_100 = service.filter_by_run(100)
        assert len(run_100) == 3

        # Filter by status
        completed = service.filter_by_status("completed")
        assert len(completed) == 2  # One from each run

    def test_comprehensive_workflow(self, service):
        """Test a comprehensive workflow."""
        # Add several attempts
        for i in range(1, 6):
            attempt = _make_attempt(
                attempt_id=i,
                run_id=100,
                attempt_number=i,
            )
            service.add_attempt(attempt)

        # Verify count
        assert len(service.list_attempts()) == 5

        # Retrieve specific attempt
        attempt = service.get_attempt_by_id(3)
        assert attempt.attempt_number == 3

        # Filter by run
        attempts = service.filter_by_run(100)
        assert len(attempts) == 5

        # Attempt to add duplicate (should fail)
        duplicate = _make_attempt(
            attempt_id=10,
            run_id=100,
            attempt_number=3,
        )
        with pytest.raises(ValueError):
            service.add_attempt(duplicate)

    def test_empty_service(self, service):
        """Test operations on empty service."""
        assert service.list_attempts() == []
        assert service.get_attempt_by_id(1) is None
        assert service.filter_by_run(100) == []
        assert service.filter_by_status("completed") == []
