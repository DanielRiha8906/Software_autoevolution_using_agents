import pytest
from datetime import datetime, timezone
from src.models.task import Task
from src.models.task_status import TaskStatus


def test_task_project_id_default_none():
    """Test that task project_id defaults to None."""
    task = Task(title="Buy milk")
    assert task.project_id is None


def test_task_with_project_id():
    """Test creating a task with a project_id."""
    project_id = "test-project-id"
    task = Task(title="Buy milk", project_id=project_id)
    assert task.project_id == project_id


def test_task_project_id_in_serialization():
    """Test that project_id is included in serialization if set."""
    project_id = "test-project-id"
    task = Task(title="Buy milk", project_id=project_id)
    data = task.to_dict()
    assert data["project_id"] == project_id


def test_task_project_id_not_in_serialization_if_none():
    """Test that project_id is not included if None."""
    task = Task(title="Buy milk", project_id=None)
    data = task.to_dict()
    assert "project_id" not in data


def test_task_roundtrip_with_project_id():
    """Test that task survives serialization with project_id."""
    project_id = "test-project-id"
    task = Task(title="Buy milk", project_id=project_id)
    restored = Task.from_dict(task.to_dict())
    assert restored.project_id == project_id


def test_task_roundtrip_without_project_id():
    """Test that task survives serialization without project_id."""
    task = Task(title="Buy milk")
    restored = Task.from_dict(task.to_dict())
    assert restored.project_id is None


def test_task_backward_compatibility_missing_project_id():
    """Test that tasks without project_id field load correctly."""
    # This simulates old task data that doesn't have project_id
    old_data = {
        "id": "123",
        "title": "Buy milk",
        "description": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    task = Task.from_dict(old_data)
    assert task.project_id is None
