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


def test_set_due_date(manager):
    task = manager.add("Task with due date")
    future = datetime.now(timezone.utc) + timedelta(days=1)
    updated = manager.set_due_date(task.id, future)
    assert updated.due_date == future


def test_set_due_date_none(manager):
    future = datetime.now(timezone.utc) + timedelta(days=1)
    task = manager.add("Task", description=None)
    manager.set_due_date(task.id, future)
    # Clear due date
    updated = manager.set_due_date(task.id, None)
    assert updated.due_date is None


def test_set_due_date_in_past_raises(manager):
    task = manager.add("Task with past due date")
    past = datetime.now(timezone.utc) - timedelta(days=1)
    with pytest.raises(ValueError, match="Due date cannot be in the past"):
        manager.set_due_date(task.id, past)


def test_set_due_date_updates_updated_at(manager):
    task = manager.add("Task")
    original_updated_at = task.updated_at
    future = datetime.now(timezone.utc) + timedelta(days=1)
    updated = manager.set_due_date(task.id, future)
    assert updated.updated_at > original_updated_at


def test_set_due_date_persists(tmp_path):
    path = str(tmp_path / "tasks.json")
    m1 = TaskManager(JsonStorage(path))
    task = m1.add("Task with due date")
    future = datetime.now(timezone.utc) + timedelta(days=1)
    m1.set_due_date(task.id, future)
    # Load from disk
    m2 = TaskManager(JsonStorage(path))
    loaded = m2.get(task.id)
    assert loaded.due_date == future


def test_backward_compatibility_load_old_tasks(tmp_path):
    """Test that old task files without due_date field still load."""
    import json
    path = str(tmp_path / "tasks.json")
    # Create a task file in old format (no due_date field)
    old_task = {
        "id": "old-task-id",
        "title": "Old task",
        "description": "Old description",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(path, "w") as f:
        json.dump([old_task], f)
    # Load it with new TaskManager
    manager = TaskManager(JsonStorage(path))
    task = manager.get("old-task-id")
    assert task.title == "Old task"
    assert task.due_date is None
