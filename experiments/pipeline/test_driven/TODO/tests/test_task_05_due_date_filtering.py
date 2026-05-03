import pytest
from datetime import datetime, timezone, timedelta
from src.models.task import Task
from src.models.task_status import TaskStatus
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage

CEST = timezone(timedelta(hours=2))
PAST = datetime(2020, 1, 1, tzinfo=CEST)
FUTURE = datetime(2099, 1, 1, tzinfo=CEST)


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
    from datetime import timezone
    cutoff = datetime(2025, 1, 1, tzinfo=timezone.utc)

    # using non-CEST should raise
    with pytest.raises(Exception):
        svc.list_tasks(due_before=cutoff)

def test_results_are_task_objects(svc):
    assert all(isinstance(t, Task) for t in svc.list_tasks(overdue=True))
