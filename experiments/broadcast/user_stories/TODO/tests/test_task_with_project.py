import pytest
from datetime import datetime, timezone

from src.models.task import Task
from src.models.task_status import TaskStatus


def test_task_with_project_id():
    """Test that a task can have a project_id."""
    task = Task(title="Buy milk", project_id="proj-123")
    assert task.project_id == "proj-123"


def test_task_without_project_id():
    """Test that a task can exist without a project_id."""
    task = Task(title="Buy milk")
    assert task.project_id is None


def test_task_project_id_serialization():
    """Test that project_id is serialized when present."""
    task = Task(title="Buy milk", project_id="proj-123")
    task_dict = task.to_dict()
    assert "project_id" in task_dict
    assert task_dict["project_id"] == "proj-123"


def test_task_project_id_not_serialized_when_none():
    """Test that project_id is not included when None."""
    task = Task(title="Buy milk")
    task_dict = task.to_dict()
    assert "project_id" not in task_dict


def test_task_project_id_roundtrip():
    """Test that project_id survives serialization/deserialization."""
    task = Task(title="Buy milk", project_id="proj-123")
    restored = Task.from_dict(task.to_dict())
    assert restored.project_id == "proj-123"


def test_task_backward_compatibility_no_project_id():
    """Test that old tasks without project_id load correctly."""
    old_task_dict = {
        "id": "test-id",
        "title": "Old task",
        "description": "A task created before project support",
        "status": "pending",
        "created_at": "2026-01-01T10:00:00+00:00",
        "updated_at": "2026-01-01T10:00:00+00:00",
    }
    task = Task.from_dict(old_task_dict)
    assert task.id == "test-id"
    assert task.title == "Old task"
    assert task.project_id is None


def test_task_change_project():
    """Test that a task's project can be changed."""
    task = Task(title="Buy milk", project_id="proj-123")
    assert task.project_id == "proj-123"

    # Change project
    task.project_id = "proj-456"
    assert task.project_id == "proj-456"


def test_task_unassign_from_project():
    """Test that a task can be unassigned from a project."""
    task = Task(title="Buy milk", project_id="proj-123")
    assert task.project_id == "proj-123"

    # Unassign
    task.project_id = None
    assert task.project_id is None
