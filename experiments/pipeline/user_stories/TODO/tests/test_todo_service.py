import pytest
from datetime import datetime, timezone, timedelta
from src.models.task_status import TaskStatus
from src.services.task_manager import TaskNotFoundError
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    return TodoService(JsonStorage(str(tmp_path / "tasks.json")))


def test_add_task(service):
    task = service.add_task("Hello")
    assert task.title == "Hello"


def test_add_task_strips_whitespace(service):
    task = service.add_task("  padded  ")
    assert task.title == "padded"


def test_add_empty_title_raises(service):
    with pytest.raises(ValueError):
        service.add_task("   ")


def test_start_task(service):
    task = service.add_task("Do it")
    started = service.start_task(task.id)
    assert started.status == TaskStatus.IN_PROGRESS


def test_complete_task(service):
    task = service.add_task("Do it")
    done = service.complete_task(task.id)
    assert done.status == TaskStatus.DONE


def test_reopen_task(service):
    task = service.add_task("Redo")
    service.complete_task(task.id)
    reopened = service.reopen_task(task.id)
    assert reopened.status == TaskStatus.PENDING


def test_list_tasks_all(service):
    service.add_task("A")
    service.add_task("B")
    assert len(service.list_tasks()) == 2


def test_list_tasks_filtered(service):
    t = service.add_task("A")
    service.add_task("B")
    service.complete_task(t.id)
    assert len(service.list_tasks(TaskStatus.DONE)) == 1
    assert len(service.list_tasks(TaskStatus.PENDING)) == 1


def test_update_task(service):
    task = service.add_task("Old title")
    updated = service.update_task(task.id, title="New title")
    assert updated.title == "New title"


def test_update_task_empty_title_raises(service):
    task = service.add_task("Valid")
    with pytest.raises(ValueError):
        service.update_task(task.id, title="")


def test_delete_task(service):
    task = service.add_task("Bye")
    service.delete_task(task.id)
    with pytest.raises(TaskNotFoundError):
        service.get_task(task.id)


# ─── Due date tests ─────────────────────────────────────────────────────────

def test_add_task_with_due_date(service):
    """Test add_task() accepts due_date parameter"""
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    task = service.add_task("Deadline task", due_date=dt)
    assert task.due_date == dt
    assert task.due_date.tzinfo is not None


def test_add_task_rejects_naive_datetime(service):
    """Test add_task() rejects naive datetime"""
    dt_naive = datetime(2026, 5, 15, 14, 30)  # no tzinfo
    with pytest.raises(ValueError, match="due_date must be timezone-aware"):
        service.add_task("Task", due_date=dt_naive)


def test_add_task_with_no_due_date(service):
    """Test add_task() works without due_date (optional parameter)"""
    task = service.add_task("No deadline")
    assert task.due_date is None


def test_set_due_date(service):
    """Test set_due_date() method works"""
    task = service.add_task("Task")
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    updated = service.set_due_date(task.id, dt)
    assert updated.due_date == dt


def test_set_due_date_rejects_naive_datetime(service):
    """Test set_due_date() rejects naive datetime"""
    task = service.add_task("Task")
    dt_naive = datetime(2026, 5, 15, 14, 30)  # no tzinfo
    with pytest.raises(ValueError, match="due_date must be timezone-aware"):
        service.set_due_date(task.id, dt_naive)


def test_set_due_date_with_none_clears(service):
    """Test set_due_date() with None clears the due_date"""
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    task = service.add_task("Task", due_date=dt)
    assert task.due_date is not None
    updated = service.set_due_date(task.id, None)
    assert updated.due_date is None


def test_update_task_with_due_date(service):
    """Test update_task() accepts due_date parameter"""
    task = service.add_task("Task")
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    updated = service.update_task(task.id, due_date=dt)
    assert updated.due_date == dt


def test_update_task_rejects_naive_datetime(service):
    """Test update_task() rejects naive datetime"""
    task = service.add_task("Task")
    dt_naive = datetime(2026, 5, 15, 14, 30)  # no tzinfo
    with pytest.raises(ValueError, match="due_date must be timezone-aware"):
        service.update_task(task.id, due_date=dt_naive)


def test_update_task_preserves_other_fields_with_due_date(service):
    """Test update_task() with due_date preserves title and description"""
    task = service.add_task("Original", description="Original desc")
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    updated = service.update_task(task.id, due_date=dt)
    assert updated.title == "Original"
    assert updated.description == "Original desc"
    assert updated.due_date == dt


def test_set_due_date_missing_task_raises(service):
    """Test set_due_date() with missing task raises TaskNotFoundError"""
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    with pytest.raises(TaskNotFoundError):
        service.set_due_date("nonexistent-id", dt)


@pytest.mark.parametrize("tz_offset", [0, 1, -5, 12])
def test_add_task_preserves_timezone_in_due_date(service, tz_offset):
    """Test add_task() preserves timezone in due_date"""
    tz = timezone(timedelta(hours=tz_offset))
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=tz)
    task = service.add_task("Task", due_date=dt)
    assert task.due_date == dt
    assert task.due_date.tzinfo.utcoffset(None) == tz.utcoffset(None)
