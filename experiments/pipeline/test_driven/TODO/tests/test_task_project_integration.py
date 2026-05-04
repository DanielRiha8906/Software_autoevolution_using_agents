"""Tests for Task and Project integration."""
import pytest
from datetime import datetime, timezone
from src.models.task import Task
from src.models.project import Project


def test_task_with_project_id():
    """Test creating a task with a project_id."""
    task = Task(title="Work on project", project_id="project-123")
    assert task.project_id == "project-123"


def test_task_project_id_defaults_to_none():
    """Test that project_id defaults to None."""
    task = Task(title="Generic task")
    assert task.project_id is None


def test_task_to_dict_with_project_id():
    """Test that project_id is included in to_dict() when set."""
    task = Task(title="Work", project_id="proj-456")
    d = task.to_dict()
    assert "project_id" in d
    assert d["project_id"] == "proj-456"


def test_task_to_dict_without_project_id():
    """Test that project_id is not included in to_dict() when None."""
    task = Task(title="Work")
    d = task.to_dict()
    # Should not include project_id key when None
    assert "project_id" not in d or d.get("project_id") is None


def test_task_to_dict_project_id_none():
    """Test to_dict() explicitly sets project_id to None."""
    task = Task(title="Work", project_id=None)
    d = task.to_dict()
    # None project_id should not be in dict
    assert "project_id" not in d


def test_task_from_dict_with_project_id():
    """Test loading a task from dict with project_id."""
    data = {
        "id": "task-123",
        "title": "Work",
        "description": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "project_id": "proj-789",
    }
    task = Task.from_dict(data)
    assert task.project_id == "proj-789"


def test_task_from_dict_without_project_id():
    """Test loading a task from dict without project_id field."""
    data = {
        "id": "task-123",
        "title": "Work",
        "description": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    task = Task.from_dict(data)
    assert task.project_id is None


def test_backward_compat_old_task_loads():
    """Test that old tasks without project_id field load fine."""
    # Simulate loading an old task dict from storage
    data = {
        "id": "abc",
        "title": "Old Task",
        "description": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    task = Task.from_dict(data)
    assert task.project_id is None
    assert task.title == "Old Task"


def test_task_roundtrip_with_project_id():
    """Test roundtrip: create -> to_dict -> from_dict with project_id."""
    original = Task(title="Work", description="Task details", project_id="proj-abc")
    d = original.to_dict()
    restored = Task.from_dict(d)

    assert restored.id == original.id
    assert restored.title == original.title
    assert restored.project_id == original.project_id
    assert restored.description == original.description


def test_task_roundtrip_without_project_id():
    """Test roundtrip for task without project_id."""
    original = Task(title="Generic task")
    d = original.to_dict()
    restored = Task.from_dict(d)

    assert restored.id == original.id
    assert restored.title == original.title
    assert restored.project_id is None


def test_task_can_reference_real_project():
    """Test that a task's project_id can match a real Project's id."""
    project = Project(name="Work")
    task = Task(title="Task in project", project_id=project.id)

    # Both should have compatible IDs
    assert isinstance(task.project_id, str)
    assert isinstance(project.id, str)
    assert task.project_id == project.id


def test_multiple_tasks_same_project():
    """Test multiple tasks can reference the same project."""
    project = Project(name="Work")
    t1 = Task(title="Task 1", project_id=project.id)
    t2 = Task(title="Task 2", project_id=project.id)

    assert t1.project_id == t2.project_id == project.id


def test_task_project_id_can_be_none_and_reassigned():
    """Test that project_id can be changed from None to a value."""
    task = Task(title="Start unassigned")
    assert task.project_id is None

    # Now assign to a project
    project = Project(name="Work")
    task.project_id = project.id

    assert task.project_id == project.id
