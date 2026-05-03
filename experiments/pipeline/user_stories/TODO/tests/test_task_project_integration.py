import pytest
from datetime import datetime, timezone
from src.models.task import Task
from src.models.task_status import TaskStatus
from src.services.task_manager import TaskManager
from src.services.project_manager import ProjectManager, ProjectNotFoundError
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


class TestTaskProjectIdBackwardCompat:
    """Test Task model backward compatibility with project_id field."""

    def test_task_project_id_field(self):
        """Test that Task has project_id field defaulting to None."""
        task = Task(title="Test Task")
        assert hasattr(task, "project_id")
        assert task.project_id is None

    def test_task_to_dict_includes_project_id(self):
        """Test that to_dict includes project_id field."""
        task = Task(title="Test Task", project_id="proj-123")
        data = task.to_dict()

        assert "project_id" in data
        assert data["project_id"] == "proj-123"

    def test_task_from_dict_backward_compat_missing_project_id(self):
        """Test that old task format without project_id loads correctly."""
        data = {
            "id": "task-123",
            "title": "Legacy Task",
            "description": None,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        # Note: no project_id key

        task = Task.from_dict(data)

        assert task.project_id is None


class TestTaskManagerProjectMethods:
    """Test TaskManager methods for project operations."""

    def test_task_manager_list_by_project(self, tmp_path):
        """Test listing tasks by project."""
        storage = JsonStorage(str(tmp_path / "data.json"))
        manager = TaskManager(storage)

        t1 = manager.add("Task 1")
        t2 = manager.add("Task 2")
        t3 = manager.add("Task 3")

        # Assign tasks to project
        manager.set_project(t1.id, "proj-1")
        manager.set_project(t2.id, "proj-1")
        manager.set_project(t3.id, "proj-2")

        # List tasks by project
        proj1_tasks = manager.list_by_project("proj-1")
        proj2_tasks = manager.list_by_project("proj-2")

        assert len(proj1_tasks) == 2
        assert any(t.id == t1.id for t in proj1_tasks)
        assert any(t.id == t2.id for t in proj1_tasks)
        assert len(proj2_tasks) == 1
        assert proj2_tasks[0].id == t3.id

    def test_task_manager_set_project(self, tmp_path):
        """Test assigning a task to a project."""
        storage = JsonStorage(str(tmp_path / "data.json"))
        manager = TaskManager(storage)
        task = manager.add("Test Task")

        updated = manager.set_project(task.id, "proj-123")

        assert updated.project_id == "proj-123"

    def test_task_manager_set_project_none(self, tmp_path):
        """Test unassigning a task from a project."""
        storage = JsonStorage(str(tmp_path / "data.json"))
        manager = TaskManager(storage)
        task = manager.add("Test Task")

        manager.set_project(task.id, "proj-123")
        updated = manager.set_project(task.id, None)

        assert updated.project_id is None

    def test_task_manager_orphan_project_tasks(self, tmp_path):
        """Test orphaning tasks when project is deleted."""
        storage = JsonStorage(str(tmp_path / "data.json"))
        manager = TaskManager(storage)

        t1 = manager.add("Task 1")
        t2 = manager.add("Task 2")
        t3 = manager.add("Task 3")

        manager.set_project(t1.id, "proj-1")
        manager.set_project(t2.id, "proj-1")
        manager.set_project(t3.id, "proj-2")

        # Orphan tasks from proj-1
        count = manager.orphan_project_tasks("proj-1")

        assert count == 2
        assert manager.get(t1.id).project_id is None
        assert manager.get(t2.id).project_id is None
        assert manager.get(t3.id).project_id == "proj-2"


class TestTodoServiceProjectMethods:
    """Test TodoService methods for project operations."""

    def test_todo_service_create_project(self, tmp_path):
        """Test creating a project via TodoService."""
        storage = JsonStorage(str(tmp_path / "data.json"))
        service = TodoService(storage)

        project = service.create_project("My Project")

        assert project.name == "My Project"
        assert project.id is not None

    def test_todo_service_list_projects(self, tmp_path):
        """Test listing all projects via TodoService."""
        storage = JsonStorage(str(tmp_path / "data.json"))
        service = TodoService(storage)

        p1 = service.create_project("Project 1")
        p2 = service.create_project("Project 2")

        projects = service.list_projects()

        assert len(projects) == 2
        assert any(p.id == p1.id for p in projects)
        assert any(p.id == p2.id for p in projects)

    def test_todo_service_get_project(self, tmp_path):
        """Test getting a project by ID via TodoService."""
        storage = JsonStorage(str(tmp_path / "data.json"))
        service = TodoService(storage)

        project = service.create_project("Test Project")
        retrieved = service.get_project(project.id)

        assert retrieved.id == project.id
        assert retrieved.name == project.name

    def test_todo_service_list_tasks_by_project(self, tmp_path):
        """Test listing tasks in a project via TodoService."""
        storage = JsonStorage(str(tmp_path / "data.json"))
        service = TodoService(storage)

        project = service.create_project("Test Project")
        task1 = service.add_task("Task 1")
        task2 = service.add_task("Task 2")

        service.move_task_to_project(task1.id, project.id)
        service.move_task_to_project(task2.id, project.id)

        tasks = service.list_tasks_by_project(project.id)

        assert len(tasks) == 2
        assert any(t.id == task1.id for t in tasks)
        assert any(t.id == task2.id for t in tasks)


class TestTodoServiceDeleteProject:
    """Test TodoService delete_project behavior."""

    def test_todo_service_delete_project(self, tmp_path):
        """Test deleting a project orphans its tasks."""
        storage = JsonStorage(str(tmp_path / "data.json"))
        service = TodoService(storage)

        project = service.create_project("Test Project")
        task = service.add_task("Task in Project")
        service.move_task_to_project(task.id, project.id)

        # Delete the project
        service.delete_project(project.id)

        # Project is gone
        with pytest.raises(ProjectNotFoundError):
            service.get_project(project.id)

        # Task is orphaned but still exists
        retrieved_task = service.get_task(task.id)
        assert retrieved_task.project_id is None


class TestStorageFormatMigration:
    """Test that storage handles both old and new formats."""

    def test_storage_loads_new_dict_format(self, tmp_path):
        """Test loading new storage format with tasks and projects dicts."""
        storage = JsonStorage(str(tmp_path / "data.json"))

        # Save in new format
        data = {
            "tasks": [
                {
                    "id": "t1",
                    "title": "Task 1",
                    "description": None,
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "due_date": None,
                    "comments": [],
                    "project_id": None,
                }
            ],
            "projects": [
                {"id": "p1", "name": "Project 1"}
            ]
        }
        storage.save(data)

        # Load should return dict with both keys
        loaded = storage.load()
        assert isinstance(loaded, dict)
        assert "tasks" in loaded
        assert "projects" in loaded
        assert len(loaded["tasks"]) == 1
        assert len(loaded["projects"]) == 1

    def test_storage_auto_migrates_old_list_format(self, tmp_path):
        """Test that old list format auto-migrates to new dict format."""
        import json
        from pathlib import Path

        path = tmp_path / "data.json"

        # Write old format directly to file (legacy list format)
        old_data = [
            {
                "id": "t1",
                "title": "Task 1",
                "description": None,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "due_date": None,
                "comments": [],
            }
        ]
        with open(path, "w") as f:
            json.dump(old_data, f)

        # Load should auto-migrate
        storage = JsonStorage(str(path))
        loaded = storage.load()

        assert isinstance(loaded, dict)
        assert "tasks" in loaded
        assert "projects" in loaded
        assert loaded["tasks"] == old_data
        assert loaded["projects"] == []

    def test_storage_handles_empty_file(self, tmp_path):
        """Test loading from empty file returns new format."""
        path = tmp_path / "data.json"
        path.write_text("")

        storage = JsonStorage(str(path))
        loaded = storage.load()

        assert loaded == {"tasks": [], "projects": []}


class TestTaskProjectIntegration:
    """End-to-end integration tests for tasks and projects."""

    def test_complete_project_workflow(self, tmp_path):
        """Test complete workflow: create project, add tasks, move tasks, delete project."""
        storage = JsonStorage(str(tmp_path / "data.json"))
        service = TodoService(storage)

        # Create project
        project = service.create_project("Work")

        # Create tasks
        task1 = service.add_task("Fix bug")
        task2 = service.add_task("Write docs")

        # Assign to project
        service.move_task_to_project(task1.id, project.id)
        service.move_task_to_project(task2.id, project.id)

        # Verify assignment
        tasks = service.list_tasks_by_project(project.id)
        assert len(tasks) == 2

        # Mark one as done
        service.start_task(task1.id)
        service.complete_task(task1.id)

        # Delete project
        service.delete_project(project.id)

        # Verify tasks still exist but are orphaned
        task1_after = service.get_task(task1.id)
        task2_after = service.get_task(task2.id)

        assert task1_after.project_id is None
        assert task2_after.project_id is None
        assert task1_after.is_completed()

    def test_persistence_across_instances(self, tmp_path):
        """Test that task-project associations persist across instances."""
        storage = JsonStorage(str(tmp_path / "data.json"))

        # Create project and task in first instance
        service1 = TodoService(storage)
        project = service1.create_project("Persistent Project")
        task = service1.add_task("Persistent Task")
        service1.move_task_to_project(task.id, project.id)

        # Load in second instance
        service2 = TodoService(storage)
        retrieved_project = service2.get_project(project.id)
        retrieved_task = service2.get_task(task.id)
        tasks_in_project = service2.list_tasks_by_project(project.id)

        assert retrieved_project.name == "Persistent Project"
        assert retrieved_task.project_id == project.id
        assert len(tasks_in_project) == 1
        assert tasks_in_project[0].id == task.id

    def test_multiple_projects_multiple_tasks(self, tmp_path):
        """Test managing multiple projects with multiple tasks."""
        storage = JsonStorage(str(tmp_path / "data.json"))
        service = TodoService(storage)

        # Create projects
        p1 = service.create_project("Project 1")
        p2 = service.create_project("Project 2")

        # Create tasks
        t1 = service.add_task("Task 1.1")
        t2 = service.add_task("Task 1.2")
        t3 = service.add_task("Task 2.1")
        t4 = service.add_task("Unassigned")

        # Assign tasks
        service.move_task_to_project(t1.id, p1.id)
        service.move_task_to_project(t2.id, p1.id)
        service.move_task_to_project(t3.id, p2.id)

        # Verify distribution
        p1_tasks = service.list_tasks_by_project(p1.id)
        p2_tasks = service.list_tasks_by_project(p2.id)

        assert len(p1_tasks) == 2
        assert len(p2_tasks) == 1
        assert set(t.id for t in p1_tasks) == {t1.id, t2.id}
        assert p2_tasks[0].id == t3.id

        # Verify unassigned task not in any project
        all_tasks = service.list_tasks()
        assert len(all_tasks) == 4
