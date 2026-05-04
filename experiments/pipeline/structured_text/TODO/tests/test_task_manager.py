import pytest
from datetime import datetime, timezone
from src.models.task_status import TaskStatus
from src.services.task_manager import TaskManager, TaskNotFoundError
from src.storage.json_storage import JsonStorage


@pytest.fixture
def manager(tmp_path):
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TaskManager(storage)


def test_add_returns_task(manager):
    task = manager.add("Buy milk")
    assert task.title == "Buy milk"
    assert task.status == TaskStatus.PENDING


def test_get_existing(manager):
    task = manager.add("Test")
    fetched = manager.get(task.id)
    assert fetched.id == task.id


def test_get_missing_raises(manager):
    with pytest.raises(TaskNotFoundError):
        manager.get("nonexistent-id")


def test_list_all(manager):
    manager.add("A")
    manager.add("B")
    assert len(manager.list_all()) == 2


def test_list_by_status(manager):
    t1 = manager.add("A")
    t2 = manager.add("B")
    manager.set_status(t1.id, TaskStatus.DONE)
    done = manager.list_by_status(TaskStatus.DONE)
    pending = manager.list_by_status(TaskStatus.PENDING)
    assert len(done) == 1
    assert len(pending) == 1


def test_update_title(manager):
    task = manager.add("Old")
    updated = manager.update(task.id, title="New")
    assert updated.title == "New"


def test_update_description(manager):
    task = manager.add("T")
    updated = manager.update(task.id, description="Some detail")
    assert updated.description == "Some detail"


def test_set_status(manager):
    task = manager.add("Work")
    manager.set_status(task.id, TaskStatus.IN_PROGRESS)
    assert manager.get(task.id).status == TaskStatus.IN_PROGRESS


def test_delete(manager):
    task = manager.add("Delete me")
    manager.delete(task.id)
    with pytest.raises(TaskNotFoundError):
        manager.get(task.id)


def test_delete_missing_raises(manager):
    with pytest.raises(TaskNotFoundError):
        manager.delete("nonexistent-id")


def test_persistence(tmp_path):
    path = str(tmp_path / "tasks.json")
    m1 = TaskManager(JsonStorage(path))
    task = m1.add("Persisted")
    m2 = TaskManager(JsonStorage(path))
    assert m2.get(task.id).title == "Persisted"


# ===== Due Date Persistence Tests =====

def test_persistence_with_due_date(tmp_path):
    """Add task with due_date, reload from file, verify persists."""
    path = str(tmp_path / "tasks.json")

    # Create manager and add task with due_date
    m1 = TaskManager(JsonStorage(path))
    due_date = datetime(2025, 12, 25, 10, 0, 0, tzinfo=timezone.utc)
    task = m1.add("Holiday gift")

    # Manually set due_date (since add doesn't support it directly)
    # We'll need to verify this persists via from_dict/to_dict
    task.due_date = due_date
    m1._persist()

    # Reload and verify
    m2 = TaskManager(JsonStorage(path))
    loaded_task = m2.get(task.id)
    assert loaded_task.due_date == due_date


def test_load_mixed_old_and_new_tasks(tmp_path):
    """Mix old (no due_date) and new (with due_date) tasks, verify both load."""
    import json

    path = str(tmp_path / "tasks.json")

    # Create a JSON file with mixed old and new tasks
    old_task = {
        "id": "old-task-id",
        "title": "Old task",
        "description": None,
        "status": "pending",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00"
        # Note: no due_date key
    }

    new_task = {
        "id": "new-task-id",
        "title": "New task",
        "description": None,
        "status": "pending",
        "due_date": "2025-12-25T10:00:00+00:00",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00"
    }

    # Write mixed data to file
    with open(path, "w") as f:
        json.dump([old_task, new_task], f)

    # Load with TaskManager
    manager = TaskManager(JsonStorage(path))
    tasks = manager.list_all()

    # Verify both loaded correctly
    assert len(tasks) == 2

    old = manager.get("old-task-id")
    assert old.title == "Old task"
    assert old.due_date is None

    new = manager.get("new-task-id")
    assert new.title == "New task"
    assert new.due_date == datetime(2025, 12, 25, 10, 0, 0, tzinfo=timezone.utc)


# ===== Project Assignment Tests (Task 08) =====

class TestListByProject:
    """Tests for TaskManager.list_by_project() method."""

    def test_list_by_project_empty(self, manager):
        """list_by_project() returns empty list when no tasks in project."""
        result = manager.list_by_project("proj-123")
        assert result == []

    def test_list_by_project_with_single_task(self, manager):
        """list_by_project() returns task assigned to project."""
        task = manager.add("Task 1")
        task.project_id = "proj-123"
        manager._persist()

        result = manager.list_by_project("proj-123")
        assert len(result) == 1
        assert result[0].id == task.id

    def test_list_by_project_with_multiple_tasks(self, manager):
        """list_by_project() returns all tasks in project."""
        t1 = manager.add("Task 1")
        t2 = manager.add("Task 2")
        t3 = manager.add("Task 3")
        t4 = manager.add("Task 4")

        t1.project_id = "proj-123"
        t2.project_id = "proj-123"
        t3.project_id = "proj-456"
        t4.project_id = None

        manager._persist()

        result = manager.list_by_project("proj-123")
        assert len(result) == 2
        assert set(t.id for t in result) == {t1.id, t2.id}

    def test_list_by_project_filters_correctly(self, manager):
        """list_by_project() excludes tasks with different project_id."""
        t1 = manager.add("A")
        t2 = manager.add("B")

        t1.project_id = "proj-1"
        t2.project_id = "proj-2"
        manager._persist()

        result_1 = manager.list_by_project("proj-1")
        result_2 = manager.list_by_project("proj-2")

        assert len(result_1) == 1
        assert result_1[0].id == t1.id

        assert len(result_2) == 1
        assert result_2[0].id == t2.id

    def test_list_by_project_excludes_unassigned(self, manager):
        """list_by_project() excludes tasks with project_id=None."""
        t1 = manager.add("Assigned")
        t2 = manager.add("Unassigned")

        t1.project_id = "proj-123"
        manager._persist()

        result = manager.list_by_project("proj-123")
        assert len(result) == 1
        assert result[0].id == t1.id


class TestAssignToProject:
    """Tests for TaskManager.assign_to_project() method."""

    def test_assign_to_project_sets_project_id(self, manager):
        """assign_to_project() sets the task's project_id."""
        task = manager.add("Task")
        result = manager.assign_to_project(task.id, "proj-123")

        assert result.project_id == "proj-123"

    def test_assign_to_project_returns_task(self, manager):
        """assign_to_project() returns the updated Task."""
        from src.models.task import Task
        task = manager.add("Task")
        result = manager.assign_to_project(task.id, "proj-123")
        assert isinstance(result, Task)
        assert result.id == task.id

    def test_assign_to_project_persists(self, tmp_path):
        """assign_to_project() persists the change."""
        path = str(tmp_path / "tasks.json")
        m1 = TaskManager(JsonStorage(path))
        task = m1.add("Task")
        m1.assign_to_project(task.id, "proj-123")

        m2 = TaskManager(JsonStorage(path))
        loaded = m2.get(task.id)
        assert loaded.project_id == "proj-123"

    def test_assign_to_project_updates_timestamp(self, manager):
        """assign_to_project() updates the updated_at timestamp."""
        task = manager.add("Task")
        original_time = task.updated_at

        import time
        time.sleep(0.01)

        updated = manager.assign_to_project(task.id, "proj-123")
        assert updated.updated_at > original_time

    def test_assign_to_project_by_prefix(self, manager):
        """assign_to_project() works with task ID prefix."""
        task = manager.add("Task")
        prefix = task.id[:8]

        result = manager.assign_to_project(prefix, "proj-123")
        assert result.project_id == "proj-123"

    def test_assign_to_project_nonexistent_raises(self, manager):
        """assign_to_project() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            manager.assign_to_project("nonexistent-id", "proj-123")

    def test_assign_to_project_can_reassign(self, manager):
        """assign_to_project() can reassign task to different project."""
        task = manager.add("Task")
        manager.assign_to_project(task.id, "proj-1")
        result = manager.assign_to_project(task.id, "proj-2")

        assert result.project_id == "proj-2"

    def test_assign_to_project_multiple_tasks(self, manager):
        """assign_to_project() can assign multiple tasks to same project."""
        t1 = manager.add("Task 1")
        t2 = manager.add("Task 2")

        manager.assign_to_project(t1.id, "proj-123")
        manager.assign_to_project(t2.id, "proj-123")

        result = manager.list_by_project("proj-123")
        assert len(result) == 2


class TestUnassignFromProject:
    """Tests for TaskManager.unassign_from_project() method."""

    def test_unassign_from_project_clears_project_id(self, manager):
        """unassign_from_project() sets project_id to None."""
        task = manager.add("Task")
        manager.assign_to_project(task.id, "proj-123")

        result = manager.unassign_from_project(task.id)
        assert result.project_id is None

    def test_unassign_from_project_returns_task(self, manager):
        """unassign_from_project() returns the updated Task."""
        task = manager.add("Task")
        manager.assign_to_project(task.id, "proj-123")

        result = manager.unassign_from_project(task.id)
        assert result.id == task.id

    def test_unassign_from_project_persists(self, tmp_path):
        """unassign_from_project() persists the change."""
        path = str(tmp_path / "tasks.json")
        m1 = TaskManager(JsonStorage(path))
        task = m1.add("Task")
        m1.assign_to_project(task.id, "proj-123")
        m1.unassign_from_project(task.id)

        m2 = TaskManager(JsonStorage(path))
        loaded = m2.get(task.id)
        assert loaded.project_id is None

    def test_unassign_from_project_updates_timestamp(self, manager):
        """unassign_from_project() updates the updated_at timestamp."""
        task = manager.add("Task")
        manager.assign_to_project(task.id, "proj-123")
        original_time = task.updated_at

        import time
        time.sleep(0.01)

        updated = manager.unassign_from_project(task.id)
        assert updated.updated_at > original_time

    def test_unassign_from_project_by_prefix(self, manager):
        """unassign_from_project() works with task ID prefix."""
        task = manager.add("Task")
        manager.assign_to_project(task.id, "proj-123")

        prefix = task.id[:8]
        result = manager.unassign_from_project(prefix)
        assert result.project_id is None

    def test_unassign_from_project_nonexistent_raises(self, manager):
        """unassign_from_project() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            manager.unassign_from_project("nonexistent-id")

    def test_unassign_from_project_idempotent(self, manager):
        """unassign_from_project() is idempotent on unassigned tasks."""
        task = manager.add("Task")
        # Task starts with project_id=None
        result = manager.unassign_from_project(task.id)
        assert result.project_id is None

    def test_unassign_removes_from_list_by_project(self, manager):
        """After unassign_from_project(), task doesn't appear in list_by_project()."""
        task = manager.add("Task")
        manager.assign_to_project(task.id, "proj-123")
        assert len(manager.list_by_project("proj-123")) == 1

        manager.unassign_from_project(task.id)
        assert len(manager.list_by_project("proj-123")) == 0
