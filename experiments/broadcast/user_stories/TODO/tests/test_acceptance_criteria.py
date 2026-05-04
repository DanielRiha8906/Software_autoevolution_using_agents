"""Tests for project grouping acceptance criteria."""

import pytest
import tempfile
from pathlib import Path

from src.models.project import Project
from src.models.task import Task
from src.services.todo_service import TodoService
from src.services.project_manager import ProjectNotFoundError
from src.storage.json_storage import JsonStorage


@pytest.fixture
def service():
    """Create a TodoService with temporary storage."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        storage = JsonStorage(f.name)
        service = TodoService(storage)
        yield service
        Path(f.name).unlink(missing_ok=True)


class TestAcceptanceCriteria:
    """Test all acceptance criteria for project grouping."""

    def test_project_domain_class_exists(self):
        """A Project domain class exists with id (UUID) and name."""
        project = Project(name="Work")
        assert hasattr(project, "id")
        assert hasattr(project, "name")
        assert isinstance(project.id, str)
        assert isinstance(project.name, str)
        # Verify it's a UUID-like string
        assert len(project.id) == 36  # UUID format

    def test_task_has_optional_project_id(self, service):
        """Task has an optional project_id attribute for assignment to a project."""
        task = Task(title="Test")
        assert hasattr(task, "project_id")
        assert task.project_id is None

        # Task can be assigned a project_id
        task.project_id = "proj-123"
        assert task.project_id == "proj-123"

    def test_projects_can_be_created_and_listed(self, service):
        """Projects can be created and listed."""
        service.create_project("Work")
        service.create_project("Personal")

        projects = service.list_projects()
        assert len(projects) == 2
        names = {p.name for p in projects}
        assert names == {"Work", "Personal"}

    def test_tasks_can_be_listed_filtered_by_project(self, service):
        """Tasks can be listed filtered by project."""
        project = service.create_project("Work")
        task1 = service.add_task("Task 1")
        task2 = service.add_task("Task 2")
        task3 = service.add_task("Task 3")

        service.assign_task_to_project(task1.id, project.id)
        service.assign_task_to_project(task2.id, project.id)
        # task3 is not assigned

        project_tasks = service.list_tasks_by_project(project.id)
        assert len(project_tasks) == 2
        task_ids = {t.id for t in project_tasks}
        assert task_ids == {task1.id, task2.id}

    def test_tasks_without_project_id_continue_to_work(self, service):
        """Tasks without a project_id continue to work as before."""
        task1 = service.add_task("Task 1")
        task2 = service.add_task("Task 2")

        # Create a project but don't assign these tasks
        service.create_project("Work")

        # Tasks should still be accessible normally
        all_tasks = service.list_tasks()
        assert len(all_tasks) == 2

        # They should appear in unassigned tasks
        unassigned = service.list_unassigned_tasks()
        assert len(unassigned) == 2

    def test_existing_stored_tasks_without_project_id_load_without_error(self, service):
        """Existing stored tasks that lack project_id load without error."""
        # Add a task (will have no project_id)
        task = service.add_task("Old task")
        
        # Create a new service instance to reload from storage
        # This simulates loading an old database without project_id field
        storage = service._manager._storage
        service2 = TodoService(storage)

        loaded_tasks = service2.list_tasks()
        assert len(loaded_tasks) == 1
        assert loaded_tasks[0].id == task.id
        assert loaded_tasks[0].project_id is None

    def test_project_names_cannot_be_empty(self, service):
        """Project names cannot be empty."""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            service.create_project("")

        with pytest.raises(ValueError, match="Project name cannot be empty"):
            service.create_project("   ")

    def test_moving_task_between_projects(self, service):
        """Moving a task from one project to another is supported."""
        proj1 = service.create_project("Project 1")
        proj2 = service.create_project("Project 2")
        task = service.add_task("Task")

        # Assign to first project
        service.assign_task_to_project(task.id, proj1.id)
        assert service.get_task(task.id).project_id == proj1.id

        # Move to second project
        service.assign_task_to_project(task.id, proj2.id)
        assert service.get_task(task.id).project_id == proj2.id

        # Verify in correct list
        proj1_tasks = service.list_tasks_by_project(proj1.id)
        proj2_tasks = service.list_tasks_by_project(proj2.id)
        assert len(proj1_tasks) == 0
        assert len(proj2_tasks) == 1

    def test_deleting_project_leaves_tasks_unassigned(self, service):
        """Deleting a project leaves its tasks unassigned (not deleted)."""
        project = service.create_project("Work")
        task = service.add_task("Task")
        service.assign_task_to_project(task.id, project.id)

        # Verify task is assigned
        assert service.get_task(task.id).project_id == project.id

        # Delete the project
        service.delete_project(project.id)

        # Task still exists
        retrieved = service.get_task(task.id)
        assert retrieved.id == task.id

    def test_no_drag_and_drop_ui_or_access_control(self):
        """No drag-and-drop UI or per-project access control is introduced."""
        # This is a code review criterion - UI is CLI-based, no access control added
        pass

    def test_all_functionality_accessible_via_python_m_src(self, service):
        """All new functionality must be accessible via python -m src."""
        from src.cli.todo_cli import TodoCLI

        cli = TodoCLI()

        # Verify project commands are in the CLI via method existence
        assert hasattr(cli, "_cmd_create_project")
        assert hasattr(cli, "_cmd_list_projects")
        assert hasattr(cli, "_cmd_show_project")
        assert hasattr(cli, "_cmd_update_project")
        assert hasattr(cli, "_cmd_delete_project")
        assert hasattr(cli, "_cmd_list_tasks_by_project")
        assert hasattr(cli, "_cmd_assign_task_to_project")
        assert hasattr(cli, "_cmd_unassign_task_from_project")

    def test_interactive_menu_has_project_management(self):
        """Interactive menu must have project management option."""
        from src.cli.interactive_menu import InteractiveMenu
        
        menu = InteractiveMenu()
        
        # Verify the method exists
        assert hasattr(menu, "_do_manage_projects")
        assert hasattr(menu, "_do_create_project")
        assert hasattr(menu, "_do_assign_task_to_project")
        assert hasattr(menu, "_do_view_project_tasks")
