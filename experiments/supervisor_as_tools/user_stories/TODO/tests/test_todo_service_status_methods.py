import pytest
from datetime import datetime, timezone, timedelta
from src.models.task_status import TaskStatus
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    """Create a TodoService with temporary storage."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TodoService(storage)


class TestMarkInProgress:
    """Test mark_in_progress service method."""

    def test_mark_in_progress_persists(self, service):
        task = service.add_task("Test task")
        assert task.status == TaskStatus.PENDING

        updated = service.mark_in_progress(task.id)
        assert updated.status == TaskStatus.IN_PROGRESS

        # Verify persistence by retrieving from service
        retrieved = service.get_task(task.id)
        assert retrieved.status == TaskStatus.IN_PROGRESS


class TestMarkDone:
    """Test mark_done service method."""

    def test_mark_done_persists(self, service):
        task = service.add_task("Test task")
        assert task.status == TaskStatus.PENDING

        updated = service.mark_done(task.id)
        assert updated.status == TaskStatus.DONE

        # Verify persistence by retrieving from service
        retrieved = service.get_task(task.id)
        assert retrieved.status == TaskStatus.DONE


class TestReopen:
    """Test reopen service method."""

    def test_reopen_persists(self, service):
        task = service.add_task("Test task")
        service.mark_done(task.id)

        updated = service.reopen(task.id)
        assert updated.status == TaskStatus.PENDING

        # Verify persistence by retrieving from service
        retrieved = service.get_task(task.id)
        assert retrieved.status == TaskStatus.PENDING


class TestIsPending:
    """Test is_pending service method."""

    def test_is_pending_true(self, service):
        task = service.add_task("Test task")
        assert service.is_pending(task.id) is True

    def test_is_pending_false(self, service):
        task = service.add_task("Test task")
        service.mark_in_progress(task.id)
        assert service.is_pending(task.id) is False


class TestIsInProgress:
    """Test is_in_progress service method."""

    def test_is_in_progress_true(self, service):
        task = service.add_task("Test task")
        service.mark_in_progress(task.id)
        assert service.is_in_progress(task.id) is True

    def test_is_in_progress_false(self, service):
        task = service.add_task("Test task")
        assert service.is_in_progress(task.id) is False


class TestIsCompleted:
    """Test is_completed service method."""

    def test_is_completed_true(self, service):
        task = service.add_task("Test task")
        service.mark_done(task.id)
        assert service.is_completed(task.id) is True

    def test_is_completed_false(self, service):
        task = service.add_task("Test task")
        assert service.is_completed(task.id) is False


class TestIsOverdue:
    """Test is_overdue service method."""

    def test_is_overdue_no_due_date(self, service):
        task = service.add_task("Test task")
        assert service.is_overdue(task.id) is False

    def test_is_overdue_completed_task(self, service):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        task = service.add_task("Test task", due_date=past)
        service.mark_done(task.id)
        assert service.is_overdue(task.id) is False

    def test_is_overdue_true(self, service):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        task = service.add_task("Test task", due_date=past)
        assert service.is_overdue(task.id) is True

    def test_is_overdue_future(self, service):
        future = datetime.now(timezone.utc) + timedelta(days=1)
        task = service.add_task("Test task", due_date=future)
        assert service.is_overdue(task.id) is False
