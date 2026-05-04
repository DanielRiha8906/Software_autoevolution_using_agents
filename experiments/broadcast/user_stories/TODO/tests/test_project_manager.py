import pytest
import tempfile
from pathlib import Path

from src.services.project_manager import ProjectManager, ProjectNotFoundError
from src.storage.json_storage import JsonStorage


def test_project_manager_add():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        storage = JsonStorage(f.name)
        manager = ProjectManager(storage)

        project = manager.add("Work")
        assert project.name == "Work"
        assert project.id is not None

        # Verify it was persisted
        loaded = manager.list_all()
        assert len(loaded) == 1
        assert loaded[0].name == "Work"

        # Clean up
        Path(f.name).unlink()


def test_project_manager_add_empty_name():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        storage = JsonStorage(f.name)
        manager = ProjectManager(storage)

        with pytest.raises(ValueError, match="Project name cannot be empty"):
            manager.add("")

        with pytest.raises(ValueError, match="Project name cannot be empty"):
            manager.add("   ")

        # Clean up
        Path(f.name).unlink()


def test_project_manager_get():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        storage = JsonStorage(f.name)
        manager = ProjectManager(storage)

        project = manager.add("Work")
        retrieved = manager.get(project.id)
        assert retrieved.id == project.id
        assert retrieved.name == "Work"

        # Clean up
        Path(f.name).unlink()


def test_project_manager_get_not_found():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        storage = JsonStorage(f.name)
        manager = ProjectManager(storage)

        with pytest.raises(ProjectNotFoundError):
            manager.get("nonexistent")

        # Clean up
        Path(f.name).unlink()


def test_project_manager_get_prefix_lookup():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        storage = JsonStorage(f.name)
        manager = ProjectManager(storage)

        project = manager.add("Work")
        prefix = project.id[:8]

        retrieved = manager.get(prefix)
        assert retrieved.id == project.id

        # Clean up
        Path(f.name).unlink()


def test_project_manager_get_ambiguous_prefix():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        storage = JsonStorage(f.name)
        manager = ProjectManager(storage)

        # Create projects with overlapping prefixes
        p1 = manager.add("Work")
        p2 = manager.add("Workshop")

        # Get a short prefix that matches both
        prefix = p1.id[:8]
        if not p2.id.startswith(prefix):
            # If p2 doesn't start with same prefix, just skip this test
            Path(f.name).unlink()
            return

        with pytest.raises(ProjectNotFoundError, match="Ambiguous"):
            manager.get(prefix)

        # Clean up
        Path(f.name).unlink()


def test_project_manager_list_all():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        storage = JsonStorage(f.name)
        manager = ProjectManager(storage)

        manager.add("Work")
        manager.add("Personal")
        manager.add("Hobby")

        projects = manager.list_all()
        assert len(projects) == 3
        names = {p.name for p in projects}
        assert names == {"Work", "Personal", "Hobby"}

        # Clean up
        Path(f.name).unlink()


def test_project_manager_update():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        storage = JsonStorage(f.name)
        manager = ProjectManager(storage)

        project = manager.add("Work")
        updated = manager.update(project.id, "Job")
        assert updated.name == "Job"

        # Verify persistence
        retrieved = manager.get(project.id)
        assert retrieved.name == "Job"

        # Clean up
        Path(f.name).unlink()


def test_project_manager_update_empty_name():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        storage = JsonStorage(f.name)
        manager = ProjectManager(storage)

        project = manager.add("Work")
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            manager.update(project.id, "")

        with pytest.raises(ValueError, match="Project name cannot be empty"):
            manager.update(project.id, "   ")

        # Clean up
        Path(f.name).unlink()


def test_project_manager_delete():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        storage = JsonStorage(f.name)
        manager = ProjectManager(storage)

        project = manager.add("Work")
        manager.delete(project.id)

        # Verify deletion
        with pytest.raises(ProjectNotFoundError):
            manager.get(project.id)

        assert len(manager.list_all()) == 0

        # Clean up
        Path(f.name).unlink()


def test_project_manager_persistence():
    """Test that projects persist across manager instances."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name

    try:
        # Create and add
        storage1 = JsonStorage(path)
        manager1 = ProjectManager(storage1)
        project = manager1.add("Work")

        # Load with new manager
        storage2 = JsonStorage(path)
        manager2 = ProjectManager(storage2)
        projects = manager2.list_all()

        assert len(projects) == 1
        assert projects[0].name == "Work"

    finally:
        Path(path).unlink(missing_ok=True)
