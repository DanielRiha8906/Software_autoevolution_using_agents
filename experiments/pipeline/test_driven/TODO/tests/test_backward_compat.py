"""Tests for backward compatibility with old data formats."""
import pytest
from datetime import datetime, timezone
from src.models.task import Task
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


def test_old_task_dict_loads():
    """Test that old task dicts without project_id load correctly."""
    old_task_dict = {
        "id": "abc123",
        "title": "Old Task",
        "description": "An old description",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    task = Task.from_dict(old_task_dict)

    assert task.id == "abc123"
    assert task.title == "Old Task"
    assert task.description == "An old description"
    assert task.status.value == "pending"
    assert task.project_id is None


def test_old_storage_file_loads(tmp_path):
    """Test that old storage files load without errors."""
    import json

    storage_path = str(tmp_path / "old_tasks.json")
    storage = JsonStorage(storage_path)

    # Create old-format storage file (list of tasks, no projects key)
    storage.path.parent.mkdir(parents=True, exist_ok=True)
    old_tasks = [
        {
            "id": "t1",
            "title": "Task 1",
            "description": None,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "t2",
            "title": "Task 2",
            "description": "Details",
            "status": "done",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    ]
    with open(storage_path, "w") as f:
        json.dump({"tasks": old_tasks}, f)

    # Load with TodoService
    service = TodoService(storage)
    tasks = service.list_tasks()

    assert len(tasks) == 2
    assert tasks[0].title == "Task 1"
    assert tasks[1].title == "Task 2"
    assert all(t.project_id is None for t in tasks)


def test_old_tasks_without_project_id_load_fine(tmp_path):
    """Test old tasks in storage don't have project_id field."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    storage.save([{
        "id": "abc", "title": "Old", "description": None, "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }])
    assert TodoService(storage).list_tasks()[0].project_id is None


def test_task_roundtrip_old_format(tmp_path):
    """Test that old tasks survive a full roundtrip."""
    import json

    storage_path = str(tmp_path / "data.json")

    # Write old-format task data
    storage = JsonStorage(storage_path)
    storage.path.parent.mkdir(parents=True, exist_ok=True)
    with open(storage_path, "w") as f:
        json.dump({
            "tasks": [{
                "id": "old-id",
                "title": "Ancient Task",
                "description": None,
                "status": "in_progress",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }]
        }, f)

    # Load and verify
    service = TodoService(storage)
    task = service.list_tasks()[0]
    assert task.id == "old-id"
    assert task.title == "Ancient Task"
    assert task.project_id is None

    # Make a change
    updated = service.update_task(task.id, title="Updated Ancient Task")
    assert updated.title == "Updated Ancient Task"

    # Reload and verify format is preserved (still no project_id if not set)
    service2 = TodoService(JsonStorage(storage_path))
    reloaded = service2.get_task(task.id)
    assert reloaded.project_id is None


def test_existing_tests_still_pass():
    """Verify that basic Task creation and operations still work."""
    # This validates that no breaking changes were made
    task = Task(title="Basic task")
    assert task.title == "Basic task"
    assert task.id is not None
    assert task.status.value == "pending"
    assert task.description is None

    # to_dict and from_dict still work
    d = task.to_dict()
    restored = Task.from_dict(d)
    assert restored.id == task.id
    assert restored.title == task.title


def test_due_date_still_works():
    """Verify due_date functionality is unaffected."""
    from datetime import timedelta

    CEST = timezone(timedelta(hours=2))
    due = datetime(2099, 12, 31, tzinfo=CEST)
    task = Task(title="Future task", due_date=due)

    assert task.due_date == due

    d = task.to_dict()
    restored = Task.from_dict(d)
    assert restored.due_date == due


def test_no_required_project_id_on_new_tasks():
    """Test that creating tasks doesn't require project_id."""
    # This ensures backward compatibility - existing code that creates
    # tasks without project_id should continue to work
    task1 = Task(title="Task 1")
    task2 = Task(title="Task 2", description="With desc")

    assert task1.project_id is None
    assert task2.project_id is None


def test_service_add_task_backward_compat(tmp_path):
    """Test that TodoService.add_task still works without project_id."""
    service = TodoService(JsonStorage(str(tmp_path / "data.json")))

    # Old way: no project_id parameter
    task = service.add_task("No project")
    assert task.project_id is None

    # With description but no project
    task2 = service.add_task("With desc", description="Details")
    assert task2.project_id is None
    assert task2.description == "Details"


def test_storage_legacy_list_format(tmp_path):
    """Test that storage can handle legacy pure-list format."""
    import json

    storage_path = str(tmp_path / "legacy.json")
    storage = JsonStorage(storage_path)

    # Write pure list format (very old format)
    storage.path.parent.mkdir(parents=True, exist_ok=True)
    with open(storage_path, "w") as f:
        json.dump([
            {
                "id": "t1",
                "title": "Task",
                "description": None,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ], f)

    # Should load fine
    loaded = storage.load()
    assert len(loaded) == 1
    assert loaded[0]["title"] == "Task"

    # Projects should return empty
    projects = storage.load_projects()
    assert projects == []
