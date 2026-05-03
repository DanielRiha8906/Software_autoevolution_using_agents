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


# Tests for extended list_tasks with new parameters
def test_list_tasks_backward_compatible_no_args(service):
    """Calling list_tasks() with no args still works."""
    service.add_task("Task 1")
    service.add_task("Task 2")
    tasks = service.list_tasks()
    assert len(tasks) == 2


def test_list_tasks_backward_compatible_with_status(service):
    """Calling list_tasks(status=...) still works."""
    t1 = service.add_task("Task 1")
    t2 = service.add_task("Task 2")
    service.complete_task(t1.id)
    tasks = service.list_tasks(status=TaskStatus.PENDING)
    assert len(tasks) == 1
    assert tasks[0].id == t2.id


def test_list_tasks_due_before(service):
    """Filter with due_before parameter."""
    now = datetime.now(timezone.utc)
    t1 = service.add_task("Task 1")
    t2 = service.add_task("Task 2")

    service.set_due_date(t1.id, now + timedelta(days=1))
    service.set_due_date(t2.id, now + timedelta(days=3))

    tasks = service.list_tasks(due_before=now + timedelta(days=2))
    assert len(tasks) == 1
    assert tasks[0].id == t1.id


def test_list_tasks_due_after(service):
    """Filter with due_after parameter."""
    now = datetime.now(timezone.utc)
    t1 = service.add_task("Task 1")
    t2 = service.add_task("Task 2")

    service.set_due_date(t1.id, now + timedelta(days=1))
    service.set_due_date(t2.id, now + timedelta(days=3))

    tasks = service.list_tasks(due_after=now + timedelta(days=2))
    assert len(tasks) == 1
    assert tasks[0].id == t2.id


def test_list_tasks_due_range(service):
    """Filter with both due_after and due_before."""
    now = datetime.now(timezone.utc)
    t1 = service.add_task("Task 1")
    t2 = service.add_task("Task 2")
    t3 = service.add_task("Task 3")

    service.set_due_date(t1.id, now + timedelta(days=1))
    service.set_due_date(t2.id, now + timedelta(days=2))
    service.set_due_date(t3.id, now + timedelta(days=3))

    tasks = service.list_tasks(
        due_after=now + timedelta(days=1),
        due_before=now + timedelta(days=2)
    )
    assert len(tasks) == 2
    ids = {t.id for t in tasks}
    assert t1.id in ids and t2.id in ids


def test_list_tasks_due_range_with_status(service):
    """Filter by date range and status."""
    now = datetime.now(timezone.utc)
    t1 = service.add_task("Task 1")
    t2 = service.add_task("Task 2")
    t3 = service.add_task("Task 3")

    service.set_due_date(t1.id, now + timedelta(days=1))
    service.set_due_date(t2.id, now + timedelta(days=2))
    service.set_due_date(t3.id, now + timedelta(days=3))

    service.complete_task(t2.id)

    tasks = service.list_tasks(
        status=TaskStatus.PENDING,
        due_after=now + timedelta(days=1),
        due_before=now + timedelta(days=2)
    )
    assert len(tasks) == 1
    assert tasks[0].id == t1.id


def test_list_tasks_overdue(service):
    """Filter with overdue parameter."""
    t1 = service.add_task("Overdue task")
    t2 = service.add_task("Future task")

    past = datetime.now(timezone.utc) - timedelta(days=1)
    t1_obj = service.get_task(t1.id)
    t1_obj.due_date = past

    future = datetime.now(timezone.utc) + timedelta(days=1)
    service.set_due_date(t2.id, future)

    # Persist the past due date
    service._manager._persist()

    tasks = service.list_tasks(overdue=True)
    assert len(tasks) == 1
    assert tasks[0].id == t1.id


def test_list_tasks_overdue_with_status(service):
    """Filter overdue with status filter."""
    t1 = service.add_task("Overdue pending")
    t2 = service.add_task("Overdue done")

    past = datetime.now(timezone.utc) - timedelta(days=1)
    t1_obj = service.get_task(t1.id)
    t2_obj = service.get_task(t2.id)
    t1_obj.due_date = past
    t2_obj.due_date = past

    service.complete_task(t2.id)
    service._manager._persist()

    tasks = service.list_tasks(overdue=True, status=TaskStatus.PENDING)
    assert len(tasks) == 1
    assert tasks[0].status == TaskStatus.PENDING


def test_list_tasks_overdue_ignores_due_before_due_after(service):
    """overdue=True ignores due_before/due_after parameters."""
    now = datetime.now(timezone.utc)
    t1 = service.add_task("Task 1")

    past = datetime.now(timezone.utc) - timedelta(days=1)
    t1_obj = service.get_task(t1.id)
    t1_obj.due_date = past
    service._manager._persist()

    # Even though we pass due_before/due_after, overdue=True should take precedence
    tasks = service.list_tasks(
        overdue=True,
        due_after=now + timedelta(days=10),
        due_before=now + timedelta(days=20)
    )
    assert len(tasks) == 1
    assert tasks[0].id == t1.id


def test_list_tasks_empty_with_filters(service):
    """Return empty list when filters match nothing."""
    now = datetime.now(timezone.utc)
    service.add_task("Task 1")
    service.set_due_date(service.list_tasks()[0].id, now + timedelta(days=10))

    tasks = service.list_tasks(due_before=now)
    assert tasks == []
