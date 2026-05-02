import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock
from tempfile import TemporaryDirectory

from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.attempt_service import AttemptService
from src.storage.workflow_json_storage import WorkflowJsonStorage


@pytest.fixture
def temp_storage():
    """Create a temporary storage for testing."""
    with TemporaryDirectory() as tmpdir:
        storage_file = Path(tmpdir) / "workflow_runs.json"
        storage = WorkflowJsonStorage(str(storage_file))
        yield storage


@pytest.fixture
def service(temp_storage):
    """Create an AttemptService with temporary storage."""
    return AttemptService(temp_storage)


def _make_attempt(
    attempt_id: int = 1,
    run_id: int = 1,
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
) -> WorkflowRunAttempt:
    """Helper to create a WorkflowRunAttempt."""
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        duration_seconds=60.0,
    )


class TestCreateAttempt:
    """Tests for creating new attempts."""

    def test_create_single_attempt(self, service):
        """Test creating a single attempt."""
        now = datetime.now(timezone.utc)
        attempt = service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="success",
            created_at=now,
        )

        assert attempt.id == 1
        assert attempt.run_id == 1
        assert attempt.attempt_number == 1
        assert attempt.status == "completed"
        assert attempt.conclusion == "success"
        assert attempt.created_at == now

    def test_create_multiple_attempts_same_run(self, service):
        """Test that attempt numbers increment correctly within a run."""
        now = datetime.now(timezone.utc)

        attempt1 = service.create_attempt(
            run_id=1,
            status="in_progress",
            conclusion=None,
            created_at=now,
        )
        attempt2 = service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="failure",
            created_at=now,
        )
        attempt3 = service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="success",
            created_at=now,
        )

        assert attempt1.attempt_number == 1
        assert attempt2.attempt_number == 2
        assert attempt3.attempt_number == 3

    def test_create_attempts_different_runs(self, service):
        """Test that attempt numbers reset for different runs."""
        now = datetime.now(timezone.utc)

        attempt1_run1 = service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="success",
            created_at=now,
        )
        attempt2_run1 = service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="failure",
            created_at=now,
        )
        attempt1_run2 = service.create_attempt(
            run_id=2,
            status="completed",
            conclusion="success",
            created_at=now,
        )

        assert attempt1_run1.attempt_number == 1
        assert attempt2_run1.attempt_number == 2
        assert attempt1_run2.attempt_number == 1

    def test_create_attempt_assigns_unique_ids(self, service):
        """Test that each created attempt gets a unique ID."""
        now = datetime.now(timezone.utc)

        attempt1 = service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="success",
            created_at=now,
        )
        attempt2 = service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="failure",
            created_at=now,
        )
        attempt3 = service.create_attempt(
            run_id=2,
            status="completed",
            conclusion="success",
            created_at=now,
        )

        assert attempt1.id == 1
        assert attempt2.id == 2
        assert attempt3.id == 3
        assert len({attempt1.id, attempt2.id, attempt3.id}) == 3

    def test_create_attempt_with_none_conclusion(self, service):
        """Test creating an attempt with None conclusion."""
        now = datetime.now(timezone.utc)
        attempt = service.create_attempt(
            run_id=1,
            status="in_progress",
            conclusion=None,
            created_at=now,
        )

        assert attempt.conclusion is None
        assert attempt.status == "in_progress"

    def test_create_attempt_invalid_run_id_zero(self, service):
        """Test that run_id of 0 raises ValueError."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="run_id must be positive"):
            service.create_attempt(
                run_id=0,
                status="completed",
                conclusion="success",
                created_at=now,
            )

    def test_create_attempt_invalid_run_id_negative(self, service):
        """Test that negative run_id raises ValueError."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="run_id must be positive"):
            service.create_attempt(
                run_id=-1,
                status="completed",
                conclusion="success",
                created_at=now,
            )

    def test_create_attempt_persists(self, temp_storage):
        """Test that created attempts are persisted to storage."""
        service = AttemptService(temp_storage)
        now = datetime.now(timezone.utc)

        service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="success",
            created_at=now,
        )

        # Create a new service instance to verify persistence
        service2 = AttemptService(temp_storage)
        attempts = service2.get_attempts_by_run_id(1)

        assert len(attempts) == 1
        assert attempts[0].run_id == 1


class TestGetAttemptsByRunId:
    """Tests for retrieving attempts by run_id."""

    def test_get_attempts_empty(self, service):
        """Test retrieving attempts when none exist."""
        attempts = service.get_attempts_by_run_id(1)
        assert attempts == []

    def test_get_single_attempt(self, service):
        """Test retrieving a single attempt."""
        now = datetime.now(timezone.utc)
        created = service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="success",
            created_at=now,
        )

        attempts = service.get_attempts_by_run_id(1)

        assert len(attempts) == 1
        assert attempts[0].id == created.id
        assert attempts[0].run_id == 1

    def test_get_multiple_attempts_sorted(self, service):
        """Test that retrieved attempts are sorted by attempt_number."""
        now = datetime.now(timezone.utc)

        service.create_attempt(
            run_id=1,
            status="in_progress",
            conclusion=None,
            created_at=now,
        )
        service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="failure",
            created_at=now,
        )
        service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="success",
            created_at=now,
        )

        attempts = service.get_attempts_by_run_id(1)

        assert len(attempts) == 3
        assert attempts[0].attempt_number == 1
        assert attempts[1].attempt_number == 2
        assert attempts[2].attempt_number == 3

    def test_get_attempts_filters_by_run_id(self, service):
        """Test that get_attempts_by_run_id only returns attempts for that run."""
        now = datetime.now(timezone.utc)

        service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="success",
            created_at=now,
        )
        service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="failure",
            created_at=now,
        )
        service.create_attempt(
            run_id=2,
            status="completed",
            conclusion="success",
            created_at=now,
        )
        service.create_attempt(
            run_id=2,
            status="completed",
            conclusion="failure",
            created_at=now,
        )

        attempts_run1 = service.get_attempts_by_run_id(1)
        attempts_run2 = service.get_attempts_by_run_id(2)

        assert len(attempts_run1) == 2
        assert all(a.run_id == 1 for a in attempts_run1)

        assert len(attempts_run2) == 2
        assert all(a.run_id == 2 for a in attempts_run2)

    def test_get_attempts_non_existent_run(self, service):
        """Test retrieving attempts for a run that doesn't exist."""
        now = datetime.now(timezone.utc)
        service.create_attempt(
            run_id=1,
            status="completed",
            conclusion="success",
            created_at=now,
        )

        attempts = service.get_attempts_by_run_id(999)
        assert attempts == []

    def test_get_attempts_preserves_order(self, service):
        """Test that attempts are consistently sorted."""
        now = datetime.now(timezone.utc)

        # Create in non-sequential order
        service.create_attempt(run_id=1, status="s1", conclusion="c1", created_at=now)
        service.create_attempt(run_id=1, status="s2", conclusion="c2", created_at=now)
        service.create_attempt(run_id=1, status="s3", conclusion="c3", created_at=now)

        # Retrieve multiple times
        attempts1 = service.get_attempts_by_run_id(1)
        attempts2 = service.get_attempts_by_run_id(1)

        assert [a.attempt_number for a in attempts1] == [1, 2, 3]
        assert [a.attempt_number for a in attempts2] == [1, 2, 3]


class TestDuplicateAttemptNumbers:
    """Tests for ensuring no duplicate attempt numbers per run."""

    def test_no_duplicate_attempt_numbers_same_run(self, service):
        """Test that attempt numbers are unique within a run."""
        now = datetime.now(timezone.utc)

        service.create_attempt(run_id=1, status="s1", conclusion="c1", created_at=now)
        service.create_attempt(run_id=1, status="s2", conclusion="c2", created_at=now)
        service.create_attempt(run_id=1, status="s3", conclusion="c3", created_at=now)

        attempts = service.get_attempts_by_run_id(1)
        attempt_numbers = [a.attempt_number for a in attempts]

        assert len(attempt_numbers) == len(set(attempt_numbers))
        assert attempt_numbers == [1, 2, 3]

    def test_duplicate_attempt_numbers_across_runs(self, service):
        """Test that the same attempt_number can exist in different runs."""
        now = datetime.now(timezone.utc)

        a1 = service.create_attempt(run_id=1, status="s", conclusion="c", created_at=now)
        a2 = service.create_attempt(run_id=2, status="s", conclusion="c", created_at=now)

        assert a1.attempt_number == 1
        assert a2.attempt_number == 1
        assert a1.id != a2.id


class TestIntegrationAndPersistence:
    """Integration tests for storage and retrieval."""

    def test_persistence_across_service_instances(self, temp_storage):
        """Test that attempts persist across service instances."""
        now = datetime.now(timezone.utc)

        # Create and add attempt with first service
        service1 = AttemptService(temp_storage)
        created = service1.create_attempt(
            run_id=1,
            status="completed",
            conclusion="success",
            created_at=now,
        )

        # Create new service and verify persistence
        service2 = AttemptService(temp_storage)
        attempts = service2.get_attempts_by_run_id(1)

        assert len(attempts) == 1
        assert attempts[0].id == created.id
        assert attempts[0].attempt_number == 1

    def test_continuation_with_new_service_instance(self, temp_storage):
        """Test that a new service instance can continue creating attempts."""
        now = datetime.now(timezone.utc)

        service1 = AttemptService(temp_storage)
        a1 = service1.create_attempt(run_id=1, status="s1", conclusion="c1", created_at=now)

        service2 = AttemptService(temp_storage)
        a2 = service2.create_attempt(run_id=1, status="s2", conclusion="c2", created_at=now)

        # Verify both are available
        attempts = service2.get_attempts_by_run_id(1)
        assert len(attempts) == 2
        assert attempts[0].attempt_number == 1
        assert attempts[1].attempt_number == 2
        assert a1.id != a2.id
        assert {a.id for a in attempts} == {a1.id, a2.id}

    def test_id_sequence_preserved_across_instances(self, temp_storage):
        """Test that ID sequence is preserved across service instances."""
        now = datetime.now(timezone.utc)

        service1 = AttemptService(temp_storage)
        a1 = service1.create_attempt(run_id=1, status="s", conclusion="c", created_at=now)
        assert a1.id == 1

        service2 = AttemptService(temp_storage)
        a2 = service2.create_attempt(run_id=1, status="s", conclusion="c", created_at=now)
        assert a2.id == 2

        service3 = AttemptService(temp_storage)
        a3 = service3.create_attempt(run_id=1, status="s", conclusion="c", created_at=now)
        assert a3.id == 3
