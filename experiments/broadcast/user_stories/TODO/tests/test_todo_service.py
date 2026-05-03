import pytest
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


def test_list_tasks_by_due_date_before(service):
    """Test filtering tasks with due_date before a given datetime."""
    from datetime import datetime, timezone

    # Create tasks with different due dates
    task1 = service.add_task("Early task")
    task1.due_date = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    task2 = service.add_task("Late task")
    task2.due_date = datetime(2026, 12, 31, 12, 0, 0, tzinfo=timezone.utc)

    task3 = service.add_task("No due date")

    # Reload to persist changes
    service._manager._persist()

    # Filter for tasks before June 2026
    cutoff = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    tasks = service.list_tasks(before=cutoff)

    assert len(tasks) == 1
    assert tasks[0].title == "Early task"


def test_list_tasks_by_due_date_after(service):
    """Test filtering tasks with due_date after a given datetime."""
    from datetime import datetime, timezone

    task1 = service.add_task("Early task")
    task1.due_date = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    task2 = service.add_task("Late task")
    task2.due_date = datetime(2026, 12, 31, 12, 0, 0, tzinfo=timezone.utc)

    task3 = service.add_task("No due date")

    service._manager._persist()

    cutoff = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    tasks = service.list_tasks(after=cutoff)

    assert len(tasks) == 1
    assert tasks[0].title == "Late task"


def test_list_tasks_by_due_date_range(service):
    """Test filtering tasks within a date range."""
    from datetime import datetime, timezone

    task1 = service.add_task("Q1 task")
    task1.due_date = datetime(2026, 2, 15, 12, 0, 0, tzinfo=timezone.utc)

    task2 = service.add_task("Q3 task")
    task2.due_date = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)

    task3 = service.add_task("No due date")

    service._manager._persist()

    start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 30, 23, 59, 59, tzinfo=timezone.utc)
    tasks = service.list_tasks(after=start, before=end)

    assert len(tasks) == 1
    assert tasks[0].title == "Q1 task"


def test_list_tasks_overdue_only(service):
    """Test filtering to show only overdue tasks."""
    from datetime import datetime, timezone, timedelta

    # Create an overdue task
    now = datetime.now(timezone.utc)
    past = now - timedelta(days=1)

    task1 = service.add_task("Overdue task")
    task1.due_date = past

    task2 = service.add_task("Future task")
    task2.due_date = now + timedelta(days=1)

    service._manager._persist()

    # Get only overdue tasks
    tasks = service.list_tasks(overdue=True)

    assert len(tasks) == 1
    assert tasks[0].title == "Overdue task"


def test_list_tasks_exclude_overdue(service):
    """Test filtering to exclude overdue tasks."""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    past = now - timedelta(days=1)

    task1 = service.add_task("Overdue task")
    task1.due_date = past

    task2 = service.add_task("Future task")
    task2.due_date = now + timedelta(days=1)

    task3 = service.add_task("No due date")

    service._manager._persist()

    # Get non-overdue tasks
    tasks = service.list_tasks(overdue=False)

    # Should get future task and task without due_date
    assert len(tasks) == 2
    task_titles = {t.title for t in tasks}
    assert "Future task" in task_titles
    assert "No due date" in task_titles
    assert "Overdue task" not in task_titles


def test_list_tasks_combined_filters(service):
    """Test combining status, date range, and overdue filters."""
    from datetime import datetime, timezone, timedelta

    # Create tasks with various states
    now = datetime.now(timezone.utc)

    # Overdue pending task
    task1 = service.add_task("Overdue pending")
    task1.due_date = now - timedelta(days=1)
    task1.status = TaskStatus.PENDING

    # Future pending task
    task2 = service.add_task("Future pending")
    task2.due_date = now + timedelta(days=5)
    task2.status = TaskStatus.PENDING

    # Overdue done task
    task3 = service.add_task("Overdue done")
    task3.due_date = now - timedelta(days=1)
    task3.status = TaskStatus.DONE

    service._manager._persist()

    # Get pending tasks that are overdue
    tasks = service.list_tasks(status=TaskStatus.PENDING, overdue=True)

    assert len(tasks) == 1
    assert tasks[0].title == "Overdue pending"


def test_list_tasks_date_range_ignores_tasks_without_due_date(service):
    """Test that date range filters only affect tasks with due dates."""
    from datetime import datetime, timezone

    task1 = service.add_task("Task with due")
    task1.due_date = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

    task2 = service.add_task("Task without due")
    # task2.due_date is None

    service._manager._persist()

    cutoff = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    tasks = service.list_tasks(after=cutoff)

    # Only task with matching due date should be returned
    assert len(tasks) == 1
    assert tasks[0].title == "Task with due"
