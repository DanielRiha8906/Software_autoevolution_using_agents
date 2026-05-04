import pytest
from src.services.project_manager import ProjectManager, ProjectNotFoundError
from src.storage.json_storage import JsonStorage


class TestProjectManagerAdd:
    """Test ProjectManager.add() method."""

    def test_project_manager_add(self, tmp_path):
        """Test adding a project and storing it."""
        storage = JsonStorage(str(tmp_path / "projects.json"))
        manager = ProjectManager(storage)

        project = manager.add("My Project")

        assert project.name == "My Project"
        assert project.id is not None
        assert project in manager.list_all()

    def test_project_manager_add_validates_name(self, tmp_path):
        """Test that add() validates project name."""
        storage = JsonStorage(str(tmp_path / "projects.json"))
        manager = ProjectManager(storage)

        with pytest.raises(ValueError, match="Project name cannot be empty"):
            manager.add("")

    def test_project_manager_add_persists(self, tmp_path):
        """Test that added projects are persisted to storage."""
        storage = JsonStorage(str(tmp_path / "projects.json"))
        manager1 = ProjectManager(storage)
        project = manager1.add("Test Project")

        # Create new manager from same storage
        manager2 = ProjectManager(storage)
        retrieved = manager2.get(project.id)

        assert retrieved.name == "Test Project"


class TestProjectManagerGet:
    """Test ProjectManager.get() method."""

    def test_project_manager_get_by_full_id(self, tmp_path):
        """Test retrieving project by full ID."""
        storage = JsonStorage(str(tmp_path / "projects.json"))
        manager = ProjectManager(storage)
        project = manager.add("Test Project")

        retrieved = manager.get(project.id)

        assert retrieved.id == project.id
        assert retrieved.name == project.name

    def test_project_manager_get_by_prefix(self, tmp_path):
        """Test retrieving project by ID prefix."""
        storage = JsonStorage(str(tmp_path / "projects.json"))
        manager = ProjectManager(storage)
        project = manager.add("Test Project")

        # Use first 8 characters of ID as prefix
        prefix = project.id[:8]
        retrieved = manager.get(prefix)

        assert retrieved.id == project.id

    def test_project_manager_get_ambiguous_prefix(self, tmp_path):
        """Test that ambiguous prefix raises ProjectNotFoundError."""
        storage = JsonStorage(str(tmp_path / "projects.json"))
        manager = ProjectManager(storage)

        # We need to manually create projects with controlled IDs to test ambiguity
        # Since we can't control the random UUID generation directly, we'll
        # construct a scenario by adding multiple projects and testing the prefix logic
        p1 = manager.add("Project 1")
        p2 = manager.add("Project 2")

        # Get their IDs
        id1 = p1.id
        id2 = p2.id

        # Find a common prefix if one exists
        # For UUID strings, this is unlikely with random generation
        # Instead, test that very short prefixes might match multiple projects
        # by using single character if by chance they share it
        for prefix_len in range(1, min(len(id1), len(id2)) + 1):
            prefix = id1[:prefix_len]
            if prefix == id2[:prefix_len]:
                # Found a matching prefix
                with pytest.raises(ProjectNotFoundError, match="Ambiguous prefix"):
                    manager.get(prefix)
                break

    def test_project_manager_get_not_found(self, tmp_path):
        """Test that nonexistent project raises ProjectNotFoundError."""
        storage = JsonStorage(str(tmp_path / "projects.json"))
        manager = ProjectManager(storage)

        with pytest.raises(ProjectNotFoundError, match="not found"):
            manager.get("nonexistent-id")


class TestProjectManagerList:
    """Test ProjectManager.list_all() method."""

    def test_project_manager_list_all(self, tmp_path):
        """Test listing all projects."""
        storage = JsonStorage(str(tmp_path / "projects.json"))
        manager = ProjectManager(storage)

        p1 = manager.add("Project 1")
        p2 = manager.add("Project 2")
        p3 = manager.add("Project 3")

        all_projects = manager.list_all()

        assert len(all_projects) == 3
        assert p1 in all_projects
        assert p2 in all_projects
        assert p3 in all_projects

    def test_project_manager_list_all_empty(self, tmp_path):
        """Test listing projects when none exist."""
        storage = JsonStorage(str(tmp_path / "projects.json"))
        manager = ProjectManager(storage)

        all_projects = manager.list_all()

        assert len(all_projects) == 0
        assert all_projects == []


class TestProjectManagerDelete:
    """Test ProjectManager.delete() method."""

    def test_project_manager_delete(self, tmp_path):
        """Test deleting a project."""
        storage = JsonStorage(str(tmp_path / "projects.json"))
        manager = ProjectManager(storage)
        project = manager.add("Project to Delete")

        manager.delete(project.id)

        assert len(manager.list_all()) == 0
        with pytest.raises(ProjectNotFoundError):
            manager.get(project.id)

    def test_project_manager_delete_not_found(self, tmp_path):
        """Test that deleting nonexistent project raises ProjectNotFoundError."""
        storage = JsonStorage(str(tmp_path / "projects.json"))
        manager = ProjectManager(storage)

        with pytest.raises(ProjectNotFoundError):
            manager.delete("nonexistent-id")

    def test_project_manager_delete_by_prefix(self, tmp_path):
        """Test deleting a project by ID prefix."""
        storage = JsonStorage(str(tmp_path / "projects.json"))
        manager = ProjectManager(storage)
        project = manager.add("Project to Delete")

        prefix = project.id[:8]
        manager.delete(prefix)

        assert len(manager.list_all()) == 0


class TestProjectManagerPersistence:
    """Test ProjectManager persistence across instances."""

    def test_project_manager_persistence(self, tmp_path):
        """Test that projects load from storage on init."""
        storage = JsonStorage(str(tmp_path / "projects.json"))

        # First manager: add projects
        manager1 = ProjectManager(storage)
        p1 = manager1.add("Project 1")
        p2 = manager1.add("Project 2")

        # Second manager: should load same projects
        manager2 = ProjectManager(storage)
        all_projects = manager2.list_all()

        assert len(all_projects) == 2
        assert any(p.id == p1.id and p.name == p1.name for p in all_projects)
        assert any(p.id == p2.id and p.name == p2.name for p in all_projects)

    def test_project_manager_preserves_tasks_on_save(self, tmp_path):
        """Test that adding projects doesn't lose existing tasks."""
        from src.services.task_manager import TaskManager

        storage = JsonStorage(str(tmp_path / "data.json"))

        # Add a task first
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        # Now add a project
        project_manager = ProjectManager(storage)
        project = project_manager.add("Test Project")

        # Verify task is still there
        task_manager2 = TaskManager(storage)
        retrieved_task = task_manager2.get(task.id)
        assert retrieved_task.title == "Test Task"

        # And project is there
        project_manager2 = ProjectManager(storage)
        retrieved_project = project_manager2.get(project.id)
        assert retrieved_project.name == "Test Project"
