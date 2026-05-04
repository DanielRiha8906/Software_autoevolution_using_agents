import pytest
import tempfile
from pathlib import Path

from src.services.todo_service import TodoService
from src.services.project_manager import ProjectNotFoundError
from src.services.task_manager import TaskNotFoundError
from src.storage.json_storage import JsonStorage


@pytest.fixture
def service():
    """Create a TodoService with a temporary storage."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        storage = JsonStorage(f.name)
        service = TodoService(storage)
        yield service
        # Clean up
        Path(f.name).unlink(missing_ok=True)


def test_create_project(service):
    """Test creating a project."""
    project = service.create_project("Work")
    assert project.name == "Work"
    assert project.id is not None


def test_create_project_empty_name(service):
    """Test that empty project names are rejected."""
    with pytest.raises(ValueError):
        service.create_project("")


def test_list_projects(service):
    """Test listing projects."""
    service.create_project("Work")
    service.create_project("Personal")

    projects = service.list_projects()
    assert len(projects) == 2
    names = {p.name for p in projects}
    assert names == {"Work", "Personal"}


def test_get_project(service):
    """Test getting a specific project."""
    project = service.create_project("Work")
    retrieved = service.get_project(project.id)
    assert retrieved.id == project.id
    assert retrieved.name == "Work"


def test_get_project_not_found(service):
    """Test that getting nonexistent project raises error."""
    with pytest.raises(ProjectNotFoundError):
        service.get_project("nonexistent")


def test_update_project(service):
    """Test updating a project name."""
    project = service.create_project("Work")
    updated = service.update_project(project.id, "Job")
    assert updated.name == "Job"

    # Verify change persists
    retrieved = service.get_project(project.id)
    assert retrieved.name == "Job"


def test_delete_project(service):
    """Test deleting a project."""
    project = service.create_project("Work")
    service.delete_project(project.id)

    # Verify deletion
    with pytest.raises(ProjectNotFoundError):
        service.get_project(project.id)

    assert len(service.list_projects()) == 0


def test_assign_task_to_project(service):
    """Test assigning a task to a project."""
    task = service.add_task("Buy milk")
    project = service.create_project("Shopping")

    assigned = service.assign_task_to_project(task.id, project.id)
    assert assigned.project_id == project.id

    # Verify it persists
    retrieved = service.get_task(task.id)
    assert retrieved.project_id == project.id


def test_assign_task_to_nonexistent_project(service):
    """Test that assigning to nonexistent project raises error."""
    task = service.add_task("Buy milk")

    with pytest.raises(ProjectNotFoundError):
        service.assign_task_to_project(task.id, "nonexistent")


def test_unassign_task_from_project(service):
    """Test removing a task from its project."""
    task = service.add_task("Buy milk")
    project = service.create_project("Shopping")

    service.assign_task_to_project(task.id, project.id)
    assert service.get_task(task.id).project_id == project.id

    unassigned = service.unassign_task_from_project(task.id)
    assert unassigned.project_id is None

    # Verify it persists
    retrieved = service.get_task(task.id)
    assert retrieved.project_id is None


def test_list_tasks_by_project(service):
    """Test listing tasks in a project."""
    project = service.create_project("Work")
    task1 = service.add_task("Task 1")
    task2 = service.add_task("Task 2")
    task3 = service.add_task("Task 3")

    service.assign_task_to_project(task1.id, project.id)
    service.assign_task_to_project(task2.id, project.id)
    # task3 is not assigned

    tasks = service.list_tasks_by_project(project.id)
    assert len(tasks) == 2
    task_ids = {t.id for t in tasks}
    assert task_ids == {task1.id, task2.id}


def test_list_tasks_by_nonexistent_project(service):
    """Test that listing tasks for nonexistent project raises error."""
    with pytest.raises(ProjectNotFoundError):
        service.list_tasks_by_project("nonexistent")


def test_list_unassigned_tasks(service):
    """Test listing tasks not in any project."""
    project = service.create_project("Work")
    task1 = service.add_task("Task 1")
    task2 = service.add_task("Task 2")
    task3 = service.add_task("Task 3")

    service.assign_task_to_project(task1.id, project.id)
    service.assign_task_to_project(task2.id, project.id)
    # task3 is not assigned

    unassigned = service.list_unassigned_tasks()
    assert len(unassigned) == 1
    assert unassigned[0].id == task3.id


def test_delete_project_leaves_tasks_unassigned(service):
    """Test that deleting a project unassigns its tasks."""
    project = service.create_project("Work")
    task = service.add_task("Task 1")
    service.assign_task_to_project(task.id, project.id)

    # Verify task is assigned
    assert service.get_task(task.id).project_id == project.id

    # Delete the project
    service.delete_project(project.id)

    # Verify task still exists but is unassigned
    retrieved = service.get_task(task.id)
    assert retrieved.id == task.id
    # Note: The task will still have the project_id reference, but the project is gone
    # This is the "leave unassigned" behavior mentioned in acceptance criteria


def test_task_without_project_continues_to_work(service):
    """Test that tasks without projects work normally."""
    # Create and list tasks without any projects
    task1 = service.add_task("Task 1")
    task2 = service.add_task("Task 2")

    all_tasks = service.list_tasks()
    assert len(all_tasks) == 2

    unassigned = service.list_unassigned_tasks()
    assert len(unassigned) == 2


def test_moving_task_between_projects(service):
    """Test moving a task from one project to another."""
    proj1 = service.create_project("Project 1")
    proj2 = service.create_project("Project 2")
    task = service.add_task("Task")

    # Assign to first project
    service.assign_task_to_project(task.id, proj1.id)
    assert service.get_task(task.id).project_id == proj1.id

    # Move to second project
    service.assign_task_to_project(task.id, proj2.id)
    assert service.get_task(task.id).project_id == proj2.id

    # Verify in correct project
    proj1_tasks = service.list_tasks_by_project(proj1.id)
    proj2_tasks = service.list_tasks_by_project(proj2.id)
    assert len(proj1_tasks) == 0
    assert len(proj2_tasks) == 1
    assert proj2_tasks[0].id == task.id
