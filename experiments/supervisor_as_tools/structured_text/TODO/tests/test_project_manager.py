import pytest
import tempfile
from pathlib import Path

from src.models.project import Project
from src.services.project_manager import ProjectManager, ProjectNotFoundError
from src.storage.json_storage import JsonStorage


@pytest.fixture
def temp_storage():
    """Create a temporary storage file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


def test_project_manager_add(temp_storage):
    storage = JsonStorage(temp_storage)
    manager = ProjectManager(storage)
    project = manager.add("My Project")
    assert project.name == "My Project"
    assert project.id is not None


def test_project_manager_get(temp_storage):
    storage = JsonStorage(temp_storage)
    manager = ProjectManager(storage)
    added = manager.add("Test")
    retrieved = manager.get(added.id)
    assert retrieved.id == added.id
    assert retrieved.name == added.name


def test_project_manager_get_missing_raises(temp_storage):
    storage = JsonStorage(temp_storage)
    manager = ProjectManager(storage)
    with pytest.raises(ProjectNotFoundError, match="Project 'missing' not found"):
        manager.get("missing")


def test_project_manager_list_all(temp_storage):
    storage = JsonStorage(temp_storage)
    manager = ProjectManager(storage)
    manager.add("Project 1")
    manager.add("Project 2")
    projects = manager.list_all()
    assert len(projects) == 2
    names = {p.name for p in projects}
    assert "Project 1" in names
    assert "Project 2" in names


def test_project_manager_delete(temp_storage):
    storage = JsonStorage(temp_storage)
    manager = ProjectManager(storage)
    project = manager.add("To Delete")
    manager.delete(project.id)
    with pytest.raises(ProjectNotFoundError):
        manager.get(project.id)


def test_project_manager_delete_missing_raises(temp_storage):
    storage = JsonStorage(temp_storage)
    manager = ProjectManager(storage)
    with pytest.raises(ProjectNotFoundError, match="Project 'missing' not found"):
        manager.delete("missing")


def test_project_manager_persistence(temp_storage):
    """Test that projects are persisted to storage."""
    storage = JsonStorage(temp_storage)
    manager1 = ProjectManager(storage)
    project1 = manager1.add("Persistent Project")
    project_id = project1.id

    # Create new manager with same storage
    manager2 = ProjectManager(storage)
    retrieved = manager2.get(project_id)
    assert retrieved.name == "Persistent Project"


def test_project_manager_empty_list(temp_storage):
    storage = JsonStorage(temp_storage)
    manager = ProjectManager(storage)
    projects = manager.list_all()
    assert projects == []
