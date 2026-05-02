import pytest
from datetime import datetime, timezone, timedelta
from src.models.task_status import TaskStatus
from src.services.task_manager import TaskManager, TaskNotFoundError
from src.storage.json_storage import JsonStorage


@pytest.fixture
def manager(tmp_path):
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TaskManager(storage)


def test_add_returns_task(manager):
    task = manager.add("Buy milk")
    assert task.title == "Buy milk"
    assert task.status == TaskStatus.PENDING


def test_get_existing(manager):
    task = manager.add("Test")
    fetched = manager.get(task.id)
    assert fetched.id == task.id


def test_get_missing_raises(manager):
    with pytest.raises(TaskNotFoundError):
        manager.get("nonexistent-id")


def test_list_all(manager):
    manager.add("A")
    manager.add("B")
    assert len(manager.list_all()) == 2


def test_list_by_status(manager):
    t1 = manager.add("A")
    t2 = manager.add("B")
    manager.set_status(t1.id, TaskStatus.DONE)
    done = manager.list_by_status(TaskStatus.DONE)
    pending = manager.list_by_status(TaskStatus.PENDING)
    assert len(done) == 1
    assert len(pending) == 1


def test_update_title(manager):
    task = manager.add("Old")
    updated = manager.update(task.id, title="New")
    assert updated.title == "New"


def test_update_description(manager):
    task = manager.add("T")
    updated = manager.update(task.id, description="Some detail")
    assert updated.description == "Some detail"


def test_set_status(manager):
    task = manager.add("Work")
    manager.set_status(task.id, TaskStatus.IN_PROGRESS)
    assert manager.get(task.id).status == TaskStatus.IN_PROGRESS


def test_delete(manager):
    task = manager.add("Delete me")
    manager.delete(task.id)
    with pytest.raises(TaskNotFoundError):
        manager.get(task.id)


def test_delete_missing_raises(manager):
    with pytest.raises(TaskNotFoundError):
        manager.delete("nonexistent-id")


def test_persistence(tmp_path):
    path = str(tmp_path / "tasks.json")
    m1 = TaskManager(JsonStorage(path))
    task = m1.add("Persisted")
    m2 = TaskManager(JsonStorage(path))
    assert m2.get(task.id).title == "Persisted"


# ─── Due date tests ─────────────────────────────────────────────────────────

def test_add_with_due_date(manager):
    """Test add() accepts due_date parameter"""
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    task = manager.add("Task with deadline", due_date=dt)
    assert task.due_date == dt
    assert task.due_date.tzinfo is not None


def test_add_without_due_date(manager):
    """Test add() without due_date defaults to None"""
    task = manager.add("No deadline")
    assert task.due_date is None


def test_set_due_date(manager):
    """Test set_due_date() method works"""
    task = manager.add("Task")
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    updated = manager.set_due_date(task.id, dt)
    assert updated.due_date == dt


def test_set_due_date_with_none_clears(manager):
    """Test set_due_date() with None clears the due_date"""
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    task = manager.add("Task", due_date=dt)
    assert task.due_date is not None
    updated = manager.set_due_date(task.id, None)
    assert updated.due_date is None


def test_update_with_due_date(manager):
    """Test update() accepts due_date parameter"""
    task = manager.add("Task")
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    updated = manager.update(task.id, due_date=dt)
    assert updated.due_date == dt


def test_update_preserves_other_fields_when_setting_due_date(manager):
    """Test update() with due_date preserves title and description"""
    task = manager.add("Original", description="Original desc")
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    updated = manager.update(task.id, due_date=dt)
    assert updated.title == "Original"
    assert updated.description == "Original desc"
    assert updated.due_date == dt


def test_persistence_with_due_date(tmp_path):
    """Test due_date persists across manager instances"""
    path = str(tmp_path / "tasks.json")
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)

    # Create first manager and add task with due_date
    m1 = TaskManager(JsonStorage(path))
    task = m1.add("Persisted deadline", due_date=dt)
    task_id = task.id

    # Create second manager and verify due_date is persisted
    m2 = TaskManager(JsonStorage(path))
    fetched = m2.get(task_id)
    assert fetched.due_date == dt
    assert fetched.due_date.tzinfo is not None


def test_set_due_date_missing_task_raises(manager):
    """Test set_due_date() with missing task raises TaskNotFoundError"""
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    with pytest.raises(TaskNotFoundError):
        manager.set_due_date("nonexistent-id", dt)
