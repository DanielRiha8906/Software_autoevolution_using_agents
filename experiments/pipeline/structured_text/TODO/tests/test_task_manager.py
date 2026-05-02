import pytest
from datetime import datetime, timezone
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


# ===== Due Date Persistence Tests =====

def test_persistence_with_due_date(tmp_path):
    """Add task with due_date, reload from file, verify persists."""
    path = str(tmp_path / "tasks.json")

    # Create manager and add task with due_date
    m1 = TaskManager(JsonStorage(path))
    due_date = datetime(2025, 12, 25, 10, 0, 0, tzinfo=timezone.utc)
    task = m1.add("Holiday gift")

    # Manually set due_date (since add doesn't support it directly)
    # We'll need to verify this persists via from_dict/to_dict
    task.due_date = due_date
    m1._persist()

    # Reload and verify
    m2 = TaskManager(JsonStorage(path))
    loaded_task = m2.get(task.id)
    assert loaded_task.due_date == due_date


def test_load_mixed_old_and_new_tasks(tmp_path):
    """Mix old (no due_date) and new (with due_date) tasks, verify both load."""
    import json

    path = str(tmp_path / "tasks.json")

    # Create a JSON file with mixed old and new tasks
    old_task = {
        "id": "old-task-id",
        "title": "Old task",
        "description": None,
        "status": "pending",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00"
        # Note: no due_date key
    }

    new_task = {
        "id": "new-task-id",
        "title": "New task",
        "description": None,
        "status": "pending",
        "due_date": "2025-12-25T10:00:00+00:00",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00"
    }

    # Write mixed data to file
    with open(path, "w") as f:
        json.dump([old_task, new_task], f)

    # Load with TaskManager
    manager = TaskManager(JsonStorage(path))
    tasks = manager.list_all()

    # Verify both loaded correctly
    assert len(tasks) == 2

    old = manager.get("old-task-id")
    assert old.title == "Old task"
    assert old.due_date is None

    new = manager.get("new-task-id")
    assert new.title == "New task"
    assert new.due_date == datetime(2025, 12, 25, 10, 0, 0, tzinfo=timezone.utc)
