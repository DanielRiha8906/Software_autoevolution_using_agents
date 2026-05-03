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


# Tests for list_by_due_date_range
def test_list_by_due_date_range_empty(manager):
    """Empty list when no tasks match."""
    tasks = manager.list_by_due_date_range()
    assert tasks == []


def test_list_by_due_date_range_excludes_no_due_date(manager):
    """Tasks without due_date are excluded."""
    manager.add("No due date")
    future = datetime.now(timezone.utc) + timedelta(days=1)
    manager.add("With due date")
    manager.set_due_date(manager.list_all()[1].id, future)

    tasks = manager.list_by_due_date_range(future - timedelta(days=1), future + timedelta(days=1))
    assert len(tasks) == 1
    assert tasks[0].due_date is not None


def test_list_by_due_date_range_inclusive_bounds(manager):
    """Date range is inclusive on both ends."""
    now = datetime.now(timezone.utc)
    t1 = manager.add("Task 1")
    t2 = manager.add("Task 2")
    t3 = manager.add("Task 3")

    due1 = now + timedelta(days=1)
    due2 = now + timedelta(days=2)
    due3 = now + timedelta(days=3)

    manager.set_due_date(t1.id, due1)
    manager.set_due_date(t2.id, due2)
    manager.set_due_date(t3.id, due3)

    tasks = manager.list_by_due_date_range(due1, due3)
    assert len(tasks) == 3

    tasks = manager.list_by_due_date_range(due2, due2)
    assert len(tasks) == 1
    assert tasks[0].id == t2.id


def test_list_by_due_date_range_start_only(manager):
    """Filter with only start bound."""
    now = datetime.now(timezone.utc)
    t1 = manager.add("Task 1")
    t2 = manager.add("Task 2")

    due1 = now + timedelta(days=1)
    due2 = now + timedelta(days=3)

    manager.set_due_date(t1.id, due1)
    manager.set_due_date(t2.id, due2)

    tasks = manager.list_by_due_date_range(start=due1 + timedelta(days=1))
    assert len(tasks) == 1
    assert tasks[0].id == t2.id


def test_list_by_due_date_range_end_only(manager):
    """Filter with only end bound."""
    now = datetime.now(timezone.utc)
    t1 = manager.add("Task 1")
    t2 = manager.add("Task 2")

    due1 = now + timedelta(days=1)
    due2 = now + timedelta(days=3)

    manager.set_due_date(t1.id, due1)
    manager.set_due_date(t2.id, due2)

    tasks = manager.list_by_due_date_range(end=due1 + timedelta(days=1))
    assert len(tasks) == 1
    assert tasks[0].id == t1.id


def test_list_by_due_date_range_start_greater_than_end(manager):
    """Return empty list if start > end."""
    now = datetime.now(timezone.utc)
    t1 = manager.add("Task 1")
    manager.set_due_date(t1.id, now + timedelta(days=1))

    tasks = manager.list_by_due_date_range(
        start=now + timedelta(days=3),
        end=now + timedelta(days=1)
    )
    assert tasks == []


def test_list_by_due_date_range_with_status_filter(manager):
    """Filter by both date range and status."""
    now = datetime.now(timezone.utc)
    t1 = manager.add("Task 1")
    t2 = manager.add("Task 2")
    t3 = manager.add("Task 3")

    due1 = now + timedelta(days=1)
    due2 = now + timedelta(days=2)
    due3 = now + timedelta(days=3)

    manager.set_due_date(t1.id, due1)
    manager.set_due_date(t2.id, due2)
    manager.set_due_date(t3.id, due3)

    manager.set_status(t2.id, TaskStatus.DONE)

    tasks = manager.list_by_due_date_range(due1, due3, status=TaskStatus.PENDING)
    assert len(tasks) == 2
    assert all(t.status == TaskStatus.PENDING for t in tasks)


def test_list_by_due_date_range_no_bounds(manager):
    """With no bounds, return all tasks with due_date."""
    now = datetime.now(timezone.utc)
    t1 = manager.add("Task 1")
    t2 = manager.add("Task 2")
    t3 = manager.add("Task 3")

    manager.set_due_date(t1.id, now + timedelta(days=1))
    manager.set_due_date(t2.id, now + timedelta(days=2))

    tasks = manager.list_by_due_date_range()
    assert len(tasks) == 2


# Tests for list_overdue
def test_list_overdue_empty(manager):
    """No overdue tasks."""
    tasks = manager.list_overdue()
    assert tasks == []


def test_list_overdue_excludes_future(manager):
    """Future due dates are not overdue."""
    now = datetime.now(timezone.utc)
    t1 = manager.add("Future task")
    manager.set_due_date(t1.id, now + timedelta(days=1))

    tasks = manager.list_overdue()
    assert tasks == []


def test_list_overdue_includes_past(manager):
    """Past due dates are overdue (use mocking or real time)."""
    # This test uses real time, so we mock tasks with past due_dates
    t1 = manager.add("Overdue task")
    # Create a task with a past due date by directly setting it
    t1.due_date = datetime.now(timezone.utc) - timedelta(days=1)
    manager._persist()

    tasks = manager.list_overdue()
    assert len(tasks) == 1
    assert tasks[0].id == t1.id


def test_list_overdue_with_status_filter(manager):
    """Filter overdue by status."""
    t1 = manager.add("Overdue pending")
    t2 = manager.add("Overdue done")

    past = datetime.now(timezone.utc) - timedelta(days=1)
    t1.due_date = past
    t2.due_date = past
    manager.set_status(t2.id, TaskStatus.DONE)
    manager._persist()

    tasks = manager.list_overdue(status=TaskStatus.PENDING)
    assert len(tasks) == 1
    assert tasks[0].status == TaskStatus.PENDING


def test_list_overdue_mixed_tasks(manager):
    """Only return overdue tasks, not future or no due_date."""
    now = datetime.now(timezone.utc)
    t1 = manager.add("Overdue")
    t2 = manager.add("Future")
    t3 = manager.add("No due date")

    t1.due_date = now - timedelta(days=1)
    manager.set_due_date(t2.id, now + timedelta(days=1))
    manager._persist()

    tasks = manager.list_overdue()
    assert len(tasks) == 1
    assert tasks[0].id == t1.id
