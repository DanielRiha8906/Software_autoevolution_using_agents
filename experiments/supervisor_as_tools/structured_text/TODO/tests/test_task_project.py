import pytest
import tempfile
from pathlib import Path

from src.models.task import Task
from src.services.task_manager import TaskManager
from src.storage.json_storage import JsonStorage


@pytest.fixture
def temp_storage():
    """Create a temporary storage file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


def test_task_project_id_field():
    """Test that tasks have a project_id field."""
    task = Task(title="Test", project_id="proj-123")
    assert task.project_id == "proj-123"


def test_task_project_id_defaults_to_none():
    """Test that project_id defaults to None."""
    task = Task(title="Test")
    assert task.project_id is None


def test_task_project_id_serialization():
    """Test that project_id is included in serialization."""
    task = Task(title="Test", project_id="proj-123")
    data = task.to_dict()
    assert "project_id" in data
    assert data["project_id"] == "proj-123"


def test_task_project_id_deserialization():
    """Test that project_id is loaded from dict."""
    data = {
        "id": "task-1",
        "title": "Test",
        "description": None,
        "status": "pending",
        "project_id": "proj-123",
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
        "due_date": None,
    }
    task = Task.from_dict(data)
    assert task.project_id == "proj-123"


def test_task_project_id_backward_compatibility():
    """Test backward compatibility with old task dicts without project_id."""
    data = {
        "id": "task-1",
        "title": "Test",
        "description": None,
        "status": "pending",
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
        "due_date": None,
    }
    task = Task.from_dict(data)
    assert task.project_id is None


def test_task_manager_add_with_project_id(temp_storage):
    """Test adding a task with a project_id."""
    storage = JsonStorage(temp_storage)
    manager = TaskManager(storage)
    task = manager.add("Test Task", project_id="proj-123")
    assert task.project_id == "proj-123"


def test_task_manager_list_by_project(temp_storage):
    """Test listing tasks by project."""
    storage = JsonStorage(temp_storage)
    manager = TaskManager(storage)
    t1 = manager.add("Task 1", project_id="proj-1")
    t2 = manager.add("Task 2", project_id="proj-1")
    t3 = manager.add("Task 3", project_id="proj-2")
    t4 = manager.add("Task 4")

    proj1_tasks = manager.list_by_project("proj-1")
    assert len(proj1_tasks) == 2
    assert t1 in proj1_tasks
    assert t2 in proj1_tasks

    proj2_tasks = manager.list_by_project("proj-2")
    assert len(proj2_tasks) == 1
    assert t3 in proj2_tasks

    no_project = manager.list_by_project("missing")
    assert no_project == []


def test_task_manager_unassign_from_project(temp_storage):
    """Test unassigning all tasks from a project."""
    storage = JsonStorage(temp_storage)
    manager = TaskManager(storage)
    t1 = manager.add("Task 1", project_id="proj-1")
    t2 = manager.add("Task 2", project_id="proj-1")
    t3 = manager.add("Task 3", project_id="proj-2")

    manager.unassign_from_project("proj-1")

    updated_t1 = manager.get(t1.id)
    updated_t2 = manager.get(t2.id)
    updated_t3 = manager.get(t3.id)

    assert updated_t1.project_id is None
    assert updated_t2.project_id is None
    assert updated_t3.project_id == "proj-2"
