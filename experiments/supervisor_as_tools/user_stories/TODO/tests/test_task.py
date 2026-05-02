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


def test_task_with_due_date():
    cest = ZoneInfo("Europe/Paris")
    due_dt = datetime(2025, 12, 31, 23, 59, tzinfo=cest)
    task = Task(title="Buy milk", due_date=due_dt)
    assert task.due_date == due_dt


def test_task_due_date_roundtrip():
    cest = ZoneInfo("Europe/Paris")
    due_dt = datetime(2025, 12, 31, 23, 59, tzinfo=cest)
    task = Task(title="Buy milk", due_date=due_dt)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == due_dt


def test_task_due_date_none():
    task = Task(title="Buy milk", due_date=None)
    assert task.due_date is None
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date is None


def test_task_backward_compatibility_missing_due_date():
    """Test that tasks without due_date field (legacy) deserialize correctly."""
    data = {
        "id": "123",
        "title": "Test",
        "description": None,
        "status": "pending",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00",
    }
    task = Task.from_dict(data)
    assert task.due_date is None
