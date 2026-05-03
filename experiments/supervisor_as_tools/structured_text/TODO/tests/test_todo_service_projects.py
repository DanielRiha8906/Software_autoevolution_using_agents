import pytest
import tempfile
from pathlib import Path

from src.models.project import Project
from src.services.project_manager import ProjectNotFoundError
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def temp_storage():
    """Create a temporary storage file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


def test_todo_service_add_project(temp_storage):
    """Test adding a project via service."""
    storage = JsonStorage(temp_storage)
    service = TodoService(storage)
    project = service.add_project("My Project")
    assert isinstance(project, Project)
    assert project.name == "My Project"


def test_todo_service_add_project_empty_name_raises(temp_storage):
    """Test that empty project name raises error."""
    storage = JsonStorage(temp_storage)
    service = TodoService(storage)
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        service.add_project("")


def test_todo_service_add_project_whitespace_only_raises(temp_storage):
    """Test that whitespace-only project name raises error."""
    storage = JsonStorage(temp_storage)
    service = TodoService(storage)
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        service.add_project("   ")


def test_todo_service_get_project(temp_storage):
    """Test getting a project."""
    storage = JsonStorage(temp_storage)
    service = TodoService(storage)
    added = service.add_project("Test")
    retrieved = service.get_project(added.id)
    assert retrieved.id == added.id
    assert retrieved.name == "Test"


def test_todo_service_get_project_missing_raises(temp_storage):
    """Test that getting missing project raises error."""
    storage = JsonStorage(temp_storage)
    service = TodoService(storage)
    with pytest.raises(ProjectNotFoundError):
        service.get_project("missing")


def test_todo_service_list_projects(temp_storage):
    """Test listing all projects."""
    storage = JsonStorage(temp_storage)
    service = TodoService(storage)
    service.add_project("Project 1")
    service.add_project("Project 2")
    projects = service.list_projects()
    assert len(projects) == 2


def test_todo_service_delete_project(temp_storage):
    """Test deleting a project."""
    storage = JsonStorage(temp_storage)
    service = TodoService(storage)
    project = service.add_project("To Delete")
    service.delete_project(project.id)
    with pytest.raises(ProjectNotFoundError):
        service.get_project(project.id)


def test_todo_service_delete_project_unassigns_tasks(temp_storage):
    """Test that deleting a project unassigns its tasks."""
    storage = JsonStorage(temp_storage)
    service = TodoService(storage)

    project = service.add_project("Project")
    task = service.add_task("Task", project_id=project.id)

    assert service.get_task(task.id).project_id == project.id

    service.delete_project(project.id)

    updated_task = service.get_task(task.id)
    assert updated_task.project_id is None


def test_todo_service_add_task_with_project(temp_storage):
    """Test adding a task with a project."""
    storage = JsonStorage(temp_storage)
    service = TodoService(storage)

    project = service.add_project("My Project")
    task = service.add_task("Task", project_id=project.id)

    assert task.project_id == project.id


def test_todo_service_list_tasks_by_project(temp_storage):
    """Test listing tasks filtered by project."""
    storage = JsonStorage(temp_storage)
    service = TodoService(storage)

    proj1 = service.add_project("Project 1")
    proj2 = service.add_project("Project 2")

    t1 = service.add_task("Task 1", project_id=proj1.id)
    t2 = service.add_task("Task 2", project_id=proj1.id)
    t3 = service.add_task("Task 3", project_id=proj2.id)
    t4 = service.add_task("Task 4")

    proj1_tasks = service.list_tasks(project_id=proj1.id)
    assert len(proj1_tasks) == 2
    assert t1 in proj1_tasks
    assert t2 in proj1_tasks

    proj2_tasks = service.list_tasks(project_id=proj2.id)
    assert len(proj2_tasks) == 1
    assert t3 in proj2_tasks

    all_tasks = service.list_tasks()
    assert len(all_tasks) == 4
