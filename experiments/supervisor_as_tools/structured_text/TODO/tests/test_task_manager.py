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


def test_set_due_date_updates_timestamp(manager):
    task = manager.add("Test")
    old_updated_at = task.updated_at
    due = datetime(2025, 12, 31, tzinfo=timezone.utc)
    updated_task = manager.set_due_date(task.id, due)
    assert updated_task.due_date == due
    assert updated_task.updated_at > old_updated_at


def test_set_due_date_persists(tmp_path):
    path = str(tmp_path / "tasks.json")
    m1 = TaskManager(JsonStorage(path))
    task = m1.add("Test")
    due = datetime(2025, 12, 31, tzinfo=timezone.utc)
    m1.set_due_date(task.id, due)
    m2 = TaskManager(JsonStorage(path))
    retrieved = m2.get(task.id)
    assert retrieved.due_date == due


def test_add_with_due_date(manager):
    due = datetime(2025, 12, 31, tzinfo=timezone.utc)
    task = manager.add("Test", due_date=due)
    assert task.due_date == due


def test_update_with_due_date(manager):
    task = manager.add("Test")
    due = datetime(2025, 12, 31, tzinfo=timezone.utc)
    updated = manager.update(task.id, due_date=due)
    assert updated.due_date == due
