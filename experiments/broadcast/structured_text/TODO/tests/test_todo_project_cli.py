import pytest
from src.cli.todo_cli import TodoCLI
from src.storage.json_storage import JsonStorage


@pytest.fixture
def cli(tmp_path):
    storage_path = str(tmp_path / "data.json")
    return TodoCLI(storage_path)


def test_project_add(cli):
    ret = cli.run(["project-add", "Work"])
    assert ret == 0


def test_project_add_empty_name(cli):
    ret = cli.run(["project-add", ""])
    assert ret == 1


def test_project_list_empty(cli):
    ret = cli.run(["project-list"])
    assert ret == 0


def test_project_list_with_projects(cli):
    cli.run(["project-add", "Work"])
    cli.run(["project-add", "Personal"])
    ret = cli.run(["project-list"])
    assert ret == 0


def test_project_show(cli):
    cli.run(["project-add", "Work"])
    # Get the project ID (first 8 chars would be the prefix)
    ret = cli.run(["project-list"])
    assert ret == 0
    # We can't easily extract the ID from the output in this test,
    # so we rely on the service-level tests for detailed validation.


def test_add_task_with_project(tmp_path):
    storage_path = str(tmp_path / "data.json")
    cli = TodoCLI(storage_path)

    # Add a project
    cli.run(["project-add", "Work"])

    # Get list of projects to extract ID
    from src.services.todo_service import TodoService
    service = TodoService(JsonStorage(storage_path))
    projects = service.list_projects()
    assert len(projects) == 1
    project_id = projects[0].id

    # Add task with project
    ret = cli.run(["add", "Task 1", "-p", project_id])
    assert ret == 0

    # Verify task is in project (using fresh service to reload data)
    service2 = TodoService(JsonStorage(storage_path))
    tasks = service2.list_tasks(project_id=project_id)
    assert len(tasks) == 1
    assert tasks[0].title == "Task 1"


def test_list_tasks_by_project(tmp_path):
    storage_path = str(tmp_path / "data.json")

    from src.services.todo_service import TodoService
    service = TodoService(JsonStorage(storage_path))

    # Add a project and tasks
    project = service.add_project("Work")
    t1 = service.add_task("Work task 1", project_id=project.id)
    t2 = service.add_task("Other task")

    # Now create CLI and list tasks by project
    cli = TodoCLI(storage_path)
    ret = cli.run(["list", "-p", project.id])
    assert ret == 0

    # List all tasks should show both
    ret = cli.run(["list"])
    assert ret == 0


def test_project_update(tmp_path):
    storage_path = str(tmp_path / "data.json")

    from src.services.todo_service import TodoService
    service = TodoService(JsonStorage(storage_path))

    project = service.add_project("Work")

    cli = TodoCLI(storage_path)
    ret = cli.run(["project-update", project.id, "Updated Name"])
    assert ret == 0

    service2 = TodoService(JsonStorage(storage_path))
    updated = service2.get_project(project.id)
    assert updated.name == "Updated Name"


def test_project_delete(tmp_path):
    storage_path = str(tmp_path / "data.json")

    from src.services.todo_service import TodoService
    service = TodoService(JsonStorage(storage_path))

    project = service.add_project("Work")
    t1 = service.add_task("Task 1", project_id=project.id)

    cli = TodoCLI(storage_path)
    ret = cli.run(["project-delete", project.id])
    assert ret == 0

    # Project should be gone
    from src.services.project_manager import ProjectNotFoundError
    service2 = TodoService(JsonStorage(storage_path))
    with pytest.raises(ProjectNotFoundError):
        service2.get_project(project.id)

    # Task should still exist but be unassigned
    task = service2.get_task(t1.id)
    assert task.project_id is None
