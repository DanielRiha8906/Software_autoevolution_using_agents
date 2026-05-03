import pytest
from datetime import datetime, timezone, timedelta
from src.models.task_status import TaskStatus
from src.models.task import Task
from src.services.task_manager import TaskNotFoundError
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage

CEST = timezone(timedelta(hours=2))
PAST = datetime(2020, 1, 1, tzinfo=CEST)
FUTURE = datetime(2099, 1, 1, tzinfo=CEST)


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


@pytest.fixture
def svc(tmp_path):
    service = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    service.add_task("Overdue task", due_date=PAST)
    service.add_task("Future task", due_date=FUTURE)
    service.add_task("No due date")
    return service


def test_filter_overdue(svc):
    results = svc.list_tasks(overdue=True)
    assert all(t.is_overdue() for t in results)
    assert len(results) == 1


def test_filter_due_before(svc):
    cutoff = datetime(2025, 1, 1, tzinfo=CEST)
    results = svc.list_tasks(due_before=cutoff)
    assert all(t.due_date is not None and t.due_date < cutoff for t in results)


def test_filter_due_after(svc):
    cutoff = datetime(2025, 1, 1, tzinfo=CEST)
    results = svc.list_tasks(due_after=cutoff)
    assert all(t.due_date is not None and t.due_date > cutoff for t in results)


def test_combined_status_and_overdue(svc):
    results = svc.list_tasks(status=TaskStatus.PENDING, overdue=True)
    assert all(t.status == TaskStatus.PENDING and t.is_overdue() for t in results)


def test_existing_status_filter_unchanged(svc):
    results = svc.list_tasks(status=TaskStatus.PENDING)
    assert all(t.status == TaskStatus.PENDING for t in results)


def test_due_date_filters_use_cest(svc):
    cutoff = datetime(2025, 1, 1, tzinfo=timezone.utc)

    # using non-CEST should raise
    with pytest.raises(Exception):
        svc.list_tasks(due_before=cutoff)


def test_results_are_task_objects(svc):
    assert all(isinstance(t, Task) for t in svc.list_tasks(overdue=True))
