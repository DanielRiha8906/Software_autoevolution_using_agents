import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
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


def test_add_with_due_date_string(manager):
    task = manager.add("Task", due_date="2025-12-31")
    assert task.due_date is not None
    assert task.due_date.year == 2025
    assert task.due_date.month == 12
    assert task.due_date.day == 31


def test_add_with_due_date_datetime(manager):
    cest = ZoneInfo("Europe/Paris")
    due_dt = datetime(2025, 12, 31, 23, 59, tzinfo=cest)
    task = manager.add("Task", due_date=due_dt)
    assert task.due_date == due_dt


def test_add_with_invalid_due_date_raises(manager):
    with pytest.raises(ValueError):
        manager.add("Task", due_date="invalid-date")


def test_update_due_date(manager):
    task = manager.add("Task")
    assert task.due_date is None
    updated = manager.update(task.id, due_date="2025-12-31")
    assert updated.due_date is not None
    assert updated.due_date.year == 2025


def test_update_due_date_with_invalid_raises(manager):
    task = manager.add("Task")
    with pytest.raises(ValueError):
        manager.update(task.id, due_date="not-a-date")


def test_due_date_persists(tmp_path):
    path = str(tmp_path / "tasks.json")
    m1 = TaskManager(JsonStorage(path))
    task = m1.add("Task", due_date="2025-12-31")
    m2 = TaskManager(JsonStorage(path))
    fetched = m2.get(task.id)
    assert fetched.due_date is not None
    assert fetched.due_date.year == 2025
    assert fetched.due_date.month == 12
    assert fetched.due_date.day == 31
