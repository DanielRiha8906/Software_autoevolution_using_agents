import pytest
import tempfile
from pathlib import Path

from src.storage.json_storage import JsonStorage


@pytest.fixture
def temp_storage():
    """Create a temporary storage file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


def test_load_projects_empty(temp_storage):
    """Test loading projects from non-existent file."""
    storage = JsonStorage(temp_storage)
    projects = storage.load_projects()
    assert projects == []


def test_save_and_load_projects(temp_storage):
    """Test saving and loading projects."""
    storage = JsonStorage(temp_storage)
    projects = [
        {"id": "proj-1", "name": "Project 1"},
        {"id": "proj-2", "name": "Project 2"},
    ]
    storage.save_projects(projects)

    loaded = storage.load_projects()
    assert loaded == projects


def test_save_projects_preserves_tasks(temp_storage):
    """Test that saving projects preserves existing tasks."""
    storage = JsonStorage(temp_storage)
    tasks = [{"id": "task-1", "title": "Task 1"}]
    storage.save(tasks)

    projects = [{"id": "proj-1", "name": "Project 1"}]
    storage.save_projects(projects)

    loaded_tasks = storage.load()
    loaded_projects = storage.load_projects()

    assert len(loaded_tasks) == 1
    assert len(loaded_projects) == 1


def test_save_tasks_preserves_projects(temp_storage):
    """Test that saving tasks preserves existing projects."""
    storage = JsonStorage(temp_storage)
    projects = [{"id": "proj-1", "name": "Project 1"}]
    storage.save_projects(projects)

    tasks = [{"id": "task-1", "title": "Task 1"}]
    storage.save(tasks)

    loaded_tasks = storage.load()
    loaded_projects = storage.load_projects()

    assert len(loaded_tasks) == 1
    assert len(loaded_projects) == 1


def test_save_comments_preserves_projects(temp_storage):
    """Test that saving comments preserves existing projects."""
    storage = JsonStorage(temp_storage)
    projects = [{"id": "proj-1", "name": "Project 1"}]
    storage.save_projects(projects)

    comments = [{"id": "comment-1", "task_id": "task-1", "content": "Comment"}]
    storage.save_comments(comments)

    loaded_projects = storage.load_projects()
    loaded_comments = storage.load_comments()

    assert len(loaded_projects) == 1
    assert len(loaded_comments) == 1


def test_import_data_includes_projects(temp_storage):
    """Test that import_data creates projects key."""
    storage = JsonStorage(temp_storage)
    tasks = [{"id": "task-1", "title": "Task 1"}]
    comments = [{"id": "comment-1", "task_id": "task-1", "content": "Comment"}]
    storage.import_data(tasks, comments)

    loaded_projects = storage.load_projects()
    assert loaded_projects == []
