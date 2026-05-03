"""Tests for storage roundtrip with projects."""
import pytest
from datetime import datetime, timezone
from src.models.task import Task
from src.models.project import Project
from src.services.project_service import ProjectService
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def storage(tmp_path):
    """Create a JsonStorage with temporary file."""
    return JsonStorage(str(tmp_path / "data.json"))


def test_save_load_projects(storage):
    """Test saving and loading projects from storage."""
    # Create and save projects
    projects_data = [
        {
            "id": "proj-1",
            "name": "Work",
            "description": "Work tasks",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "proj-2",
            "name": "Home",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    storage.save_projects(projects_data)

    # Load and verify
    loaded = storage.load_projects()
    assert len(loaded) == 2
    assert loaded[0]["name"] == "Work"
    assert loaded[1]["name"] == "Home"


def test_save_load_projects_with_service(tmp_path):
    """Test roundtrip through ProjectService."""
    path = str(tmp_path / "data.json")

    # Create projects
    service1 = ProjectService(JsonStorage(path))
    p1 = service1.create("Work", description="Work tasks")
    p2 = service1.create("Home")

    # Load with new service
    service2 = ProjectService(JsonStorage(path))
    projects = service2.list_all()

    assert len(projects) == 2
    work = [p for p in projects if p.name == "Work"][0]
    home = [p for p in projects if p.name == "Home"][0]

    assert work.description == "Work tasks"
    assert home.description is None


def test_task_with_project_storage_roundtrip(tmp_path):
    """Test that tasks with project_id survive storage roundtrip."""
    path = str(tmp_path / "data.json")

    # Create task with project
    todo1 = TodoService(JsonStorage(path))
    projects1 = ProjectService(JsonStorage(path))

    project = projects1.create("Work")
    task = todo1.add_task("Task", project_id=project.id)

    # Load with new services
    todo2 = TodoService(JsonStorage(path))
    loaded_task = todo2.get_task(task.id)

    assert loaded_task.project_id == project.id
    assert loaded_task.title == "Task"


def test_old_storage_without_projects_key(tmp_path):
    """Test that old storage files without projects key don't error."""
    storage = JsonStorage(str(tmp_path / "data.json"))

    # Simulate old storage with only tasks
    import json
    storage.path.parent.mkdir(parents=True, exist_ok=True)
    with open(storage.path, "w") as f:
        json.dump({"tasks": []}, f)

    # Load projects should return empty list
    projects = storage.load_projects()
    assert projects == []


def test_old_task_storage_loads_fine(tmp_path):
    """Test that old task storage without project_id field loads."""
    storage = JsonStorage(str(tmp_path / "data.json"))

    # Save old-format task (no project_id, no projects key)
    import json
    storage.path.parent.mkdir(parents=True, exist_ok=True)
    old_tasks = [
        {
            "id": "task-1",
            "title": "Old task",
            "description": None,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ]
    with open(storage.path, "w") as f:
        json.dump({"tasks": old_tasks}, f)

    # Load with TodoService
    todo = TodoService(storage)
    tasks = todo.list_tasks()

    assert len(tasks) == 1
    assert tasks[0].title == "Old task"
    assert tasks[0].project_id is None


def test_upgrade_storage_old_to_new(tmp_path):
    """Test that upgrading from old to new storage format works."""
    path = str(tmp_path / "data.json")
    storage = JsonStorage(path)

    # Start with old format (tasks only, no projects)
    import json
    storage.path.parent.mkdir(parents=True, exist_ok=True)
    with open(storage.path, "w") as f:
        json.dump(
            {
                "tasks": [
                    {
                        "id": "t-1",
                        "title": "Legacy task",
                        "description": None,
                        "status": "pending",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                ]
            },
            f,
        )

    # Load and use services
    todo = TodoService(storage)
    projects = ProjectService(storage)

    # Old task should load
    tasks = todo.list_tasks()
    assert len(tasks) == 1

    # Can create new projects
    proj = projects.create("New Project")
    assert proj is not None

    # Both tasks and projects now in storage
    reloaded_todo = TodoService(JsonStorage(path))
    reloaded_projects = ProjectService(JsonStorage(path))

    assert len(reloaded_todo.list_tasks()) == 1
    assert len(reloaded_projects.list_all()) == 1


def test_storage_preserves_comments_when_saving_projects(tmp_path):
    """Test that saving projects doesn't lose comments."""
    storage = JsonStorage(str(tmp_path / "data.json"))

    # Set up with tasks and comments
    import json
    storage.path.parent.mkdir(parents=True, exist_ok=True)
    with open(storage.path, "w") as f:
        json.dump(
            {
                "tasks": [
                    {
                        "id": "t-1",
                        "title": "Task",
                        "description": None,
                        "status": "pending",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                ],
                "comments": [
                    {"id": "c-1", "task_id": "t-1", "text": "A comment"}
                ],
            },
            f,
        )

    # Add a project
    projects = ProjectService(storage)
    projects.create("New Project")

    # Verify comments still exist
    loaded_comments = storage.load_comments()
    assert len(loaded_comments) == 1
    assert loaded_comments[0]["text"] == "A comment"


def test_storage_with_both_projects_and_tasks(tmp_path):
    """Test storage correctly handles both tasks and projects."""
    path = str(tmp_path / "data.json")

    # Create both
    todo = TodoService(JsonStorage(path))
    projects = ProjectService(JsonStorage(path))

    p = projects.create("Work")
    t = todo.add_task("Task", project_id=p.id)

    # Verify file has both
    import json
    with open(path) as f:
        data = json.load(f)

    assert "tasks" in data
    assert "projects" in data
    assert len(data["tasks"]) == 1
    assert len(data["projects"]) == 1
