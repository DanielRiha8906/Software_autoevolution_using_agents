import pytest
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


def test_list_by_date_range_before(manager):
    """Test filtering tasks with due date before a given datetime."""
    from datetime import datetime, timezone

    task1 = manager.add("Early")
    task1.due_date = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    task2 = manager.add("Late")
    task2.due_date = datetime(2026, 12, 15, 12, 0, 0, tzinfo=timezone.utc)

    task3 = manager.add("No date")
    # task3.due_date is None

    manager._persist()

    cutoff = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    tasks = manager.list_by_date_range(before=cutoff)

    assert len(tasks) == 1
    assert tasks[0].title == "Early"


def test_list_by_date_range_after(manager):
    """Test filtering tasks with due date after a given datetime."""
    from datetime import datetime, timezone

    task1 = manager.add("Early")
    task1.due_date = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    task2 = manager.add("Late")
    task2.due_date = datetime(2026, 12, 15, 12, 0, 0, tzinfo=timezone.utc)

    manager._persist()

    cutoff = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    tasks = manager.list_by_date_range(after=cutoff)

    assert len(tasks) == 1
    assert tasks[0].title == "Late"


def test_list_by_date_range_both(manager):
    """Test filtering tasks within a date range (before and after)."""
    from datetime import datetime, timezone

    task1 = manager.add("Q1")
    task1.due_date = datetime(2026, 2, 15, 12, 0, 0, tzinfo=timezone.utc)

    task2 = manager.add("Q2")
    task2.due_date = datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc)

    task3 = manager.add("Q4")
    task3.due_date = datetime(2026, 11, 15, 12, 0, 0, tzinfo=timezone.utc)

    manager._persist()

    start = datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    tasks = manager.list_by_date_range(after=start, before=end)

    assert len(tasks) == 1
    assert tasks[0].title == "Q2"


def test_list_by_date_range_excludes_no_due_date(manager):
    """Test that date range filtering excludes tasks without due dates."""
    from datetime import datetime, timezone

    task1 = manager.add("With date")
    task1.due_date = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

    task2 = manager.add("No date")
    # task2.due_date is None

    manager._persist()

    cutoff = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    tasks = manager.list_by_date_range(after=cutoff)

    assert len(tasks) == 1
    assert tasks[0].title == "With date"


def test_list_overdue(manager):
    """Test filtering overdue tasks."""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)

    task1 = manager.add("Overdue")
    task1.due_date = now - timedelta(days=1)

    task2 = manager.add("Future")
    task2.due_date = now + timedelta(days=1)

    task3 = manager.add("No due")
    # task3.due_date is None

    manager._persist()

    overdue = manager.list_overdue()

    assert len(overdue) == 1
    assert overdue[0].title == "Overdue"


def test_list_overdue_empty(manager):
    """Test that list_overdue returns empty list when no tasks are overdue."""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)

    task1 = manager.add("Future")
    task1.due_date = now + timedelta(days=5)

    task2 = manager.add("No due")

    manager._persist()

    overdue = manager.list_overdue()

    assert len(overdue) == 0
