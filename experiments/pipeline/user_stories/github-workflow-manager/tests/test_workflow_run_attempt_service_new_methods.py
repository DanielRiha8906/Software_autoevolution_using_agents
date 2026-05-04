"""Tests for new methods in WorkflowRunAttemptService: replace_attempt and delete_attempt."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.workflow_run_attempt_service import WorkflowRunAttemptService


def _make_attempt(
    attempt_id: int = 1,
    run_id: int = 1,
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
) -> WorkflowRunAttempt:
    """Create a test WorkflowRunAttempt."""
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def service():
    """Create a service with mocked storage."""
    storage = MagicMock()
    storage.load_attempts.return_value = []
    svc = WorkflowRunAttemptService(storage)
    return svc


class TestReplaceAttempt:
    """Tests for replace_attempt method."""

    def test_replace_attempt_add_new_attempt(self, service):
        """replace_attempt adds attempt if it doesn't exist."""
        attempt = _make_attempt(attempt_id=1)
        service.replace_attempt(attempt)
        attempts = service.list_attempts(sorted=False)
        assert len(attempts) == 1
        assert attempts[0].id == 1

    def test_replace_attempt_replace_existing_attempt(self, service):
        """replace_attempt replaces existing attempt with same id."""
        attempt1 = _make_attempt(attempt_id=1, status="completed", conclusion="success")
        service.add_attempt(attempt1)

        attempt2 = _make_attempt(attempt_id=1, status="completed", conclusion="failure")
        service.replace_attempt(attempt2)

        attempts = service.list_attempts(sorted=False)
        assert len(attempts) == 1
        assert attempts[0].conclusion == "failure"

    def test_replace_attempt_does_not_duplicate(self, service):
        """replace_attempt does not duplicate when replacing."""
        attempt1 = _make_attempt(attempt_id=1)
        service.add_attempt(attempt1)

        attempt2 = _make_attempt(attempt_id=1, run_id=2)
        service.replace_attempt(attempt2)

        attempts = service.list_attempts(sorted=False)
        assert len(attempts) == 1

    def test_replace_attempt_updates_internal_list(self, service):
        """replace_attempt updates the internal list."""
        attempt1 = _make_attempt(attempt_id=1, status="in_progress")
        service.add_attempt(attempt1)

        attempt2 = _make_attempt(attempt_id=1, status="completed")
        service.replace_attempt(attempt2)

        found = service.get_attempt(1)
        assert found is not None
        assert found.status == "completed"

    def test_replace_attempt_calls_persist(self, service):
        """replace_attempt persists changes to storage."""
        attempt = _make_attempt(attempt_id=1)
        service.replace_attempt(attempt)
        service._storage.save_attempts.assert_called()

    def test_replace_attempt_preserves_other_attempts(self, service):
        """replace_attempt does not affect other attempts."""
        attempt1 = _make_attempt(attempt_id=1, run_id=1, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=2, attempt_number=1)
        attempt3 = _make_attempt(attempt_id=3, run_id=3, attempt_number=1)

        service.add_attempt(attempt1)
        service.add_attempt(attempt2)
        service.add_attempt(attempt3)

        new_attempt2 = _make_attempt(attempt_id=2, run_id=2, attempt_number=1, conclusion="skipped")
        service.replace_attempt(new_attempt2)

        attempts = service.list_attempts(sorted=False)
        assert len(attempts) == 3
        # Find by id and check replacement worked
        replaced = next((a for a in attempts if a.id == 2), None)
        assert replaced is not None
        assert replaced.conclusion == "skipped"
        # Check others are unchanged
        assert any(a.id == 1 and a.conclusion == "success" for a in attempts)
        assert any(a.id == 3 and a.conclusion == "success" for a in attempts)

    def test_replace_attempt_on_empty_service(self, service):
        """replace_attempt works on empty service."""
        attempt = _make_attempt(attempt_id=1)
        assert len(service.list_attempts(sorted=False)) == 0
        service.replace_attempt(attempt)
        assert len(service.list_attempts(sorted=False)) == 1

    def test_replace_attempt_multiple_replacements(self, service):
        """replace_attempt can replace same attempt multiple times."""
        attempt1 = _make_attempt(attempt_id=1, conclusion="success")
        service.replace_attempt(attempt1)

        attempt2 = _make_attempt(attempt_id=1, conclusion="failure")
        service.replace_attempt(attempt2)

        attempt3 = _make_attempt(attempt_id=1, conclusion="skipped")
        service.replace_attempt(attempt3)

        attempts = service.list_attempts(sorted=False)
        assert len(attempts) == 1
        assert attempts[0].conclusion == "skipped"

    def test_replace_attempt_different_run_ids(self, service):
        """replace_attempt with different run_id."""
        attempt1 = _make_attempt(attempt_id=1, run_id=1)
        service.add_attempt(attempt1)

        # Attempt with same id but different run_id
        attempt2 = _make_attempt(attempt_id=1, run_id=2)
        service.replace_attempt(attempt2)

        found = service.get_attempt(1)
        assert found.run_id == 2


class TestDeleteAttempt:
    """Tests for delete_attempt method."""

    def test_delete_attempt_success(self, service):
        """delete_attempt returns True when attempt exists and is deleted."""
        attempt = _make_attempt(attempt_id=1)
        service.add_attempt(attempt)

        result = service.delete_attempt(1)
        assert result is True
        assert len(service.list_attempts(sorted=False)) == 0

    def test_delete_attempt_not_found(self, service):
        """delete_attempt returns False when attempt does not exist."""
        result = service.delete_attempt(999)
        assert result is False

    def test_delete_attempt_calls_persist_on_success(self, service):
        """delete_attempt calls persist when attempt is deleted."""
        attempt = _make_attempt(attempt_id=1)
        service.add_attempt(attempt)
        service._storage.reset_mock()

        service.delete_attempt(1)
        service._storage.save_attempts.assert_called()

    def test_delete_attempt_does_not_persist_on_failure(self, service):
        """delete_attempt does not call persist when attempt not found."""
        service._storage.reset_mock()
        service.delete_attempt(999)
        service._storage.save_attempts.assert_not_called()

    def test_delete_attempt_preserves_other_attempts(self, service):
        """delete_attempt only removes the target attempt."""
        attempt1 = _make_attempt(attempt_id=1, run_id=1, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=2, attempt_number=1)
        attempt3 = _make_attempt(attempt_id=3, run_id=3, attempt_number=1)

        service.add_attempt(attempt1)
        service.add_attempt(attempt2)
        service.add_attempt(attempt3)

        result = service.delete_attempt(2)

        assert result is True
        attempts = service.list_attempts(sorted=False)
        assert len(attempts) == 2
        assert any(a.id == 1 for a in attempts)
        assert any(a.id == 3 for a in attempts)
        assert not any(a.id == 2 for a in attempts)

    def test_delete_attempt_on_empty_service(self, service):
        """delete_attempt returns False on empty service."""
        result = service.delete_attempt(1)
        assert result is False
        assert len(service.list_attempts(sorted=False)) == 0

    def test_delete_attempt_multiple_times_same_id(self, service):
        """delete_attempt returns False on second deletion of same id."""
        attempt = _make_attempt(attempt_id=1)
        service.add_attempt(attempt)

        result1 = service.delete_attempt(1)
        assert result1 is True

        result2 = service.delete_attempt(1)
        assert result2 is False

    def test_delete_attempt_preserves_same_run_id(self, service):
        """delete_attempt only removes by attempt id, not run_id."""
        attempt1 = _make_attempt(attempt_id=1, run_id=1, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=1, attempt_number=2)
        attempt3 = _make_attempt(attempt_id=3, run_id=1, attempt_number=3)

        service.add_attempt(attempt1)
        service.add_attempt(attempt2)
        service.add_attempt(attempt3)

        # Delete attempt 2, but same run_id should have others
        result = service.delete_attempt(2)

        assert result is True
        attempts_for_run = service.get_attempts_for_run(1, sorted=False)
        assert len(attempts_for_run) == 2
        assert all(a.run_id == 1 for a in attempts_for_run)


class TestReplaceAndDeleteIntegration:
    """Integration tests for replace_attempt and delete_attempt together."""

    def test_replace_then_delete(self, service):
        """Can replace an attempt and then delete it."""
        attempt1 = _make_attempt(attempt_id=1)
        service.replace_attempt(attempt1)
        assert len(service.list_attempts(sorted=False)) == 1

        attempt2 = _make_attempt(attempt_id=1, conclusion="failure")
        service.replace_attempt(attempt2)
        assert service.get_attempt(1).conclusion == "failure"

        result = service.delete_attempt(1)
        assert result is True
        assert len(service.list_attempts(sorted=False)) == 0

    def test_delete_then_replace(self, service):
        """Can delete an attempt and then replace it."""
        attempt1 = _make_attempt(attempt_id=1)
        service.add_attempt(attempt1)
        service.delete_attempt(1)
        assert len(service.list_attempts(sorted=False)) == 0

        attempt2 = _make_attempt(attempt_id=1, conclusion="skipped")
        service.replace_attempt(attempt2)
        assert len(service.list_attempts(sorted=False)) == 1
        assert service.get_attempt(1).conclusion == "skipped"

    def test_replace_preserves_position(self, service):
        """replace_attempt appends attempt to end."""
        attempt1 = _make_attempt(attempt_id=1, run_id=1, attempt_number=1)
        attempt2 = _make_attempt(attempt_id=2, run_id=2, attempt_number=1)
        attempt3 = _make_attempt(attempt_id=3, run_id=3, attempt_number=1)

        service.add_attempt(attempt1)
        service.add_attempt(attempt2)
        service.add_attempt(attempt3)

        new_attempt2 = _make_attempt(attempt_id=2, run_id=2, attempt_number=1, conclusion="failed")
        service.replace_attempt(new_attempt2)

        attempts = service.list_attempts(sorted=False)
        # After replace, attempt 2 should be at the end
        assert attempts[-1].id == 2
        assert attempts[-1].conclusion == "failed"

    def test_concurrent_operations_consistency(self, service):
        """Multiple operations maintain consistency."""
        attempts = [_make_attempt(attempt_id=i, run_id=i, attempt_number=1) for i in range(1, 6)]
        for attempt in attempts:
            service.add_attempt(attempt)

        assert len(service.list_attempts(sorted=False)) == 5

        # Replace some
        service.replace_attempt(_make_attempt(attempt_id=1, run_id=1, attempt_number=1, conclusion="skipped"))
        service.replace_attempt(_make_attempt(attempt_id=3, run_id=3, attempt_number=1, conclusion="failed"))

        assert len(service.list_attempts(sorted=False)) == 5

        # Delete some
        assert service.delete_attempt(2) is True
        assert service.delete_attempt(4) is True

        assert len(service.list_attempts(sorted=False)) == 3

        # Add new
        service.add_attempt(_make_attempt(attempt_id=10, run_id=10, attempt_number=1))

        assert len(service.list_attempts(sorted=False)) == 4

    def test_same_run_multiple_attempts(self, service):
        """Multiple attempts for same run can be managed independently."""
        # Add 3 attempts for the same run
        for i in range(1, 4):
            service.add_attempt(_make_attempt(attempt_id=i, run_id=1, attempt_number=i))

        # Get all attempts for the run
        attempts = service.get_attempts_for_run(1)
        assert len(attempts) == 3

        # Replace one
        service.replace_attempt(_make_attempt(attempt_id=2, run_id=1, attempt_number=2, conclusion="failed"))
        found = service.get_attempt(2)
        assert found.conclusion == "failed"

        # Delete one
        assert service.delete_attempt(3) is True
        attempts = service.get_attempts_for_run(1)
        assert len(attempts) == 2
