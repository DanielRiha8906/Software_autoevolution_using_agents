import pytest
from datetime import datetime, timedelta, timezone
from src.models.task import Task
from src.models.task_status import TaskStatus


def test_task_defaults():
    task = Task(title="Buy milk")
    assert task.title == "Buy milk"
    assert task.status == TaskStatus.PENDING
    assert task.description is None
    assert task.id is not None


def test_task_unique_ids():
    a = Task(title="A")
    b = Task(title="B")
    assert a.id != b.id


def test_task_roundtrip():
    task = Task(title="Test", description="desc")
    restored = Task.from_dict(task.to_dict())
    assert restored.id == task.id
    assert restored.title == task.title
    assert restored.description == task.description
    assert restored.status == task.status
    assert restored.created_at == task.created_at
    assert restored.updated_at == task.updated_at


def test_task_status_serialisation():
    for status in TaskStatus:
        task = Task(title="x", status=status)
        restored = Task.from_dict(task.to_dict())
        assert restored.status == status


def test_task_due_date_default():
    task = Task(title="Test")
    assert task.due_date is None


def test_task_due_date_set():
    due = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    task = Task(title="Test", due_date=due)
    assert task.due_date == due


def test_task_due_date_roundtrip():
    due = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    task = Task(title="Test", due_date=due)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == due


def test_task_due_date_none_roundtrip():
    task = Task(title="Test", due_date=None)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date is None


def test_task_due_date_backward_compatibility():
    data = {
        "id": "test-id",
        "title": "Old task",
        "description": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    task = Task.from_dict(data)
    assert task.due_date is None


def test_task_due_date_with_cest_timezone():
    from datetime import timezone as tz
    cest = tz(timedelta(hours=2))
    due = datetime(2025, 12, 31, 23, 59, 59, tzinfo=cest)
    task = Task(title="Test", due_date=due)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == due


def test_task_is_overdue_true():
    past = datetime.now(timezone.utc) - timedelta(days=1)
    task = Task(title="Test", due_date=past)
    assert task.is_overdue() is True


def test_task_is_overdue_false_future():
    future = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Test", due_date=future)
    assert task.is_overdue() is False


def test_task_is_overdue_none():
    task = Task(title="Test", due_date=None)
    assert task.is_overdue() is False
