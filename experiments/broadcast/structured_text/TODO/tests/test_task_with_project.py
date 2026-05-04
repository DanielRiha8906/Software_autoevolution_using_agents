import pytest
from src.models.task import Task
from src.models.task_status import TaskStatus
from src.services.task_manager import TaskManager
from src.services.project_manager import ProjectManager
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    storage = JsonStorage(str(tmp_path / "data.json"))
    return TodoService(storage)


def test_task_with_project_roundtrip():
    task = Task(title="Test", project_id="proj-123")
    restored = Task.from_dict(task.to_dict())
    assert restored.project_id == "proj-123"


def test_task_without_project_roundtrip():
    task = Task(title="Test")
    restored = Task.from_dict(task.to_dict())
    assert restored.project_id is None


def test_add_task_with_project(service):
    project = service.add_project("Work")
    task = service.add_task("Task 1", project_id=project.id)
    assert task.project_id == project.id


def test_add_task_with_nonexistent_project(service):
    with pytest.raises(Exception):  # ProjectNotFoundError
        service.add_task("Task 1", project_id="nonexistent")


def test_list_tasks_by_project(service):
    p1 = service.add_project("Work")
    p2 = service.add_project("Personal")

    t1 = service.add_task("Work task 1", project_id=p1.id)
    t2 = service.add_task("Work task 2", project_id=p1.id)
    t3 = service.add_task("Personal task", project_id=p2.id)
    t4 = service.add_task("No project")

    work_tasks = service.list_tasks(project_id=p1.id)
    assert len(work_tasks) == 2
    assert all(t.project_id == p1.id for t in work_tasks)

    personal_tasks = service.list_tasks(project_id=p2.id)
    assert len(personal_tasks) == 1
    assert personal_tasks[0].project_id == p2.id


def test_list_tasks_by_nonexistent_project(service):
    with pytest.raises(Exception):  # ProjectNotFoundError
        service.list_tasks(project_id="nonexistent")


def test_delete_project_unassigns_tasks(service):
    project = service.add_project("Work")
    t1 = service.add_task("Task 1", project_id=project.id)
    t2 = service.add_task("Task 2", project_id=project.id)

    service.delete_project(project.id)

    # Verify project is deleted
    with pytest.raises(Exception):
        service.get_project(project.id)

    # Verify tasks are still there but unassigned
    assert service.get_task(t1.id).project_id is None
    assert service.get_task(t2.id).project_id is None


def test_task_manager_list_by_project(tmp_path):
    storage = JsonStorage(str(tmp_path / "data.json"))
    manager = TaskManager(storage)

    t1 = manager.add("Task 1")
    t2 = manager.add("Task 2")
    t3 = manager.add("Task 3")

    # Update project_id manually (normally done via TodoService)
    t1.project_id = "proj-123"
    t2.project_id = "proj-123"
    t3.project_id = "proj-456"
    manager._persist()

    # Now reload and test filtering
    manager2 = TaskManager(storage)
    proj_123_tasks = manager2.list_by_project("proj-123")
    assert len(proj_123_tasks) == 2

    proj_456_tasks = manager2.list_by_project("proj-456")
    assert len(proj_456_tasks) == 1

    proj_empty_tasks = manager2.list_by_project("proj-nonexistent")
    assert len(proj_empty_tasks) == 0
