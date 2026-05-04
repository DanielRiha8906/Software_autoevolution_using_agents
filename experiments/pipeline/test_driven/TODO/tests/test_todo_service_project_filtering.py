"""Tests for TodoService project filtering."""
import pytest
from src.models.task_status import TaskStatus
from src.services.todo_service import TodoService
from src.services.project_service import ProjectService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def services(tmp_path):
    """Create TodoService and ProjectService with shared storage."""
    path = str(tmp_path / "data.json")
    todo = TodoService(JsonStorage(path))
    projects = ProjectService(JsonStorage(path))
    return todo, projects


def test_add_task_with_project_id(services):
    """Test adding a task with a project_id."""
    todo, projects = services
    project = projects.create("Work")
    task = todo.add_task("Task in project", project_id=project.id)
    assert task.project_id == project.id


def test_add_task_without_project_id(services):
    """Test adding a task without project_id remains None."""
    todo, _ = services
    task = todo.add_task("No project")
    assert task.project_id is None


def test_task_without_project_id_is_none(services):
    """Test that tasks without project assignment have None project_id."""
    todo, _ = services
    assert todo.add_task("No project").project_id is None


def test_list_tasks_by_project(services):
    """Test listing tasks filtered by project."""
    todo, projects = services
    p = projects.create("Work")
    todo.add_task("Task A", project_id=p.id)
    todo.add_task("Task B", project_id=p.id)
    todo.add_task("Task C")  # No project

    tasks = todo.list_tasks(project_id=p.id)
    assert len(tasks) == 2
    assert all(t.project_id == p.id for t in tasks)


def test_list_tasks_by_project_no_matches(services):
    """Test listing tasks by project with no matches."""
    todo, projects = services
    p1 = projects.create("Work")
    p2 = projects.create("Home")

    todo.add_task("Task for Work", project_id=p1.id)
    tasks = todo.list_tasks(project_id=p2.id)

    assert len(tasks) == 0


def test_list_tasks_by_project_and_status(services):
    """Test filtering tasks by both project and status."""
    todo, projects = services
    p = projects.create("Work")

    t1 = todo.add_task("Done task", project_id=p.id)
    t2 = todo.add_task("Pending task", project_id=p.id)
    todo.complete_task(t1.id)

    done_tasks = todo.list_tasks(status=TaskStatus.DONE, project_id=p.id)
    assert len(done_tasks) == 1
    assert done_tasks[0].id == t1.id

    pending_tasks = todo.list_tasks(status=TaskStatus.PENDING, project_id=p.id)
    assert len(pending_tasks) == 1
    assert pending_tasks[0].id == t2.id


def test_list_tasks_without_project_unchanged(services):
    """Test that listing without project_id includes all tasks."""
    todo, projects = services
    p = projects.create("Work")

    todo.add_task("With project", project_id=p.id)
    todo.add_task("Without project")

    all_tasks = todo.list_tasks()
    assert len(all_tasks) == 2


def test_update_task_project_id(services):
    """Test updating a task's project_id."""
    todo, projects = services
    p1 = projects.create("Work")
    p2 = projects.create("Home")

    task = todo.add_task("Task", project_id=p1.id)
    assert task.project_id == p1.id

    updated = todo.update_task(task.id, project_id=p2.id)
    assert updated.project_id == p2.id


def test_move_task_between_projects(services):
    """Test moving a task from one project to another."""
    todo, projects = services
    p1 = projects.create("Alpha")
    p2 = projects.create("Beta")

    task = todo.add_task("Movable", project_id=p1.id)
    assert task.project_id == p1.id

    moved = todo.update_task(task.id, project_id=p2.id)
    assert moved.project_id == p2.id

    # Verify it shows up in p2's list
    p2_tasks = todo.list_tasks(project_id=p2.id)
    assert any(t.id == task.id for t in p2_tasks)

    # Verify it's gone from p1's list
    p1_tasks = todo.list_tasks(project_id=p1.id)
    assert not any(t.id == task.id for t in p1_tasks)


def test_add_task_with_description_and_project(services):
    """Test adding a task with both description and project_id."""
    todo, projects = services
    project = projects.create("Work")
    task = todo.add_task("Task", description="Details", project_id=project.id)

    assert task.title == "Task"
    assert task.description == "Details"
    assert task.project_id == project.id


def test_list_tasks_project_and_other_filters(services):
    """Test that project_id filter works alongside other filters."""
    todo, projects = services
    p = projects.create("Work")

    t1 = todo.add_task("Task 1", project_id=p.id)
    t2 = todo.add_task("Task 2", project_id=p.id)
    t3 = todo.add_task("Task 3")

    # Mark first task done
    todo.complete_task(t1.id)

    # Filter by project and status
    pending_in_project = todo.list_tasks(status=TaskStatus.PENDING, project_id=p.id)
    assert len(pending_in_project) == 1
    assert pending_in_project[0].id == t2.id


def test_update_task_removes_project_assignment():
    """Test that updating a task can remove project assignment."""
    from src.services.todo_service import TodoService
    from src.storage.json_storage import JsonStorage
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        todo = TodoService(JsonStorage(str(tmp) + "/data.json"))
        projects = ProjectService(JsonStorage(str(tmp) + "/data.json"))

        project = projects.create("Work")
        task = todo.add_task("Task", project_id=project.id)
        assert task.project_id == project.id

        # Update without project_id should NOT change it
        # (only explicit parameters get updated)
        updated = todo.update_task(task.id, title="New title")
        assert updated.project_id == project.id  # Should still be assigned


def test_list_by_project_includes_all_statuses(services):
    """Test that project filter includes tasks of all statuses."""
    todo, projects = services
    p = projects.create("Work")

    t1 = todo.add_task("Pending", project_id=p.id)
    t2 = todo.add_task("In Progress", project_id=p.id)
    t3 = todo.add_task("Done", project_id=p.id)

    todo.start_task(t2.id)
    todo.complete_task(t3.id)

    tasks = todo.list_tasks(project_id=p.id)
    assert len(tasks) == 3
    statuses = {t.status for t in tasks}
    assert TaskStatus.PENDING in statuses
    assert TaskStatus.IN_PROGRESS in statuses
    assert TaskStatus.DONE in statuses
