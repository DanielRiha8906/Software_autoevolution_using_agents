import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
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
    task = Task(title="Buy milk")
    assert task.due_date is None


def test_task_due_date_roundtrip():
    due_date = datetime(2025, 12, 31, 23, 59, 59, tzinfo=ZoneInfo("Europe/Paris"))
    task = Task(title="Finish project", due_date=due_date)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == due_date


def test_task_backward_compatibility_no_due_date():
    """Load old JSON without due_date field should set due_date to None."""
    old_data = {
        "id": "test-id",
        "title": "Old task",
        "description": None,
        "status": "pending",
        "created_at": "2025-01-01T12:00:00+00:00",
        "updated_at": "2025-01-01T12:00:00+00:00",
    }
    task = Task.from_dict(old_data)
    assert task.due_date is None


def test_task_is_overdue_no_due_date():
    task = Task(title="No due date")
    assert task.is_overdue() is False


def test_task_is_overdue_future_date():
    future_date = datetime(2099, 12, 31, 23, 59, 59, tzinfo=ZoneInfo("Europe/Paris"))
    task = Task(title="Future task", due_date=future_date)
    assert task.is_overdue() is False


def test_task_is_overdue_past_date():
    past_date = datetime(2000, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))
    task = Task(title="Past task", due_date=past_date)
    assert task.is_overdue() is True
