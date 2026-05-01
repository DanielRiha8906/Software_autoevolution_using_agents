import pytest
from datetime import datetime, timezone, timedelta
from src.models.task import Task
from src.models.task_status import TaskStatus

CEST = timezone(timedelta(hours=2))


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


def test_task_has_due_date_attribute():
    assert hasattr(Task(title="Buy milk"), "due_date")


def test_due_date_defaults_to_none():
    assert Task(title="Buy milk").due_date is None


def test_due_date_can_be_set():
    due = datetime(2026, 6, 1, 12, 0, tzinfo=CEST)
    assert Task(title="Buy milk", due_date=due).due_date == due


def test_due_date_in_to_dict():
    due = datetime(2026, 6, 1, 12, 0, tzinfo=CEST)
    d = Task(title="Buy milk", due_date=due).to_dict()
    assert "due_date" in d
    assert d["due_date"] == due.isoformat()


def test_due_date_round_trips_via_dict():
    due = datetime(2026, 6, 1, 12, 0, tzinfo=CEST)
    task = Task(title="Buy milk", due_date=due)
    assert Task.from_dict(task.to_dict()).due_date == due


def test_task_without_due_date_in_dict_loads_fine():
    from datetime import timezone
    d = {
        "id": "abc", "title": "Old task", "description": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    assert Task.from_dict(d).due_date is None


def test_invalid_due_date_raises():
    with pytest.raises(Exception):
        Task(title="Buy milk", due_date="not-a-datetime")
