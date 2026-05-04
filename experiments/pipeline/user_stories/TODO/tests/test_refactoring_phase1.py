"""Tests for Phase 1 refactoring: making boundary methods public and set_task() method.

Covers:
- Exception hierarchy (ServiceError base class)
- Public date boundary methods on TaskManager (get_week_boundaries, get_month_boundaries, get_year_boundaries)
- set_task() method functionality (add, replace, validation)
- Exception imports from src.services
- TodoService using public methods (not private)
- import_tasks() using set_task() internally
- CLI imports work correctly
"""

import pytest
from datetime import datetime, timezone, date
from pathlib import Path
import json

from src.services import ServiceError, TaskNotFoundError, ProjectNotFoundError, TodoService
from src.services.task_manager import TaskManager
from src.models.task import Task
from src.models.task_status import TaskStatus
from src.storage.json_storage import JsonStorage


# ─── Test Exception Hierarchy ────────────────────────────────────────────────


class TestExceptionHierarchy:
    """Test that exceptions are properly defined and inherit from ServiceError."""

    def test_service_error_is_base_exception(self):
        """ServiceError should be a base exception class."""
        assert issubclass(ServiceError, Exception)

    def test_task_not_found_error_inherits_from_service_error(self):
        """TaskNotFoundError should inherit from ServiceError."""
        assert issubclass(TaskNotFoundError, ServiceError)

    def test_project_not_found_error_inherits_from_service_error(self):
        """ProjectNotFoundError should inherit from ServiceError."""
        assert issubclass(ProjectNotFoundError, ServiceError)

    def test_exceptions_can_be_caught_as_service_error(self):
        """All exceptions should be catchable as ServiceError."""
        with pytest.raises(ServiceError):
            raise TaskNotFoundError("Task not found")

        with pytest.raises(ServiceError):
            raise ProjectNotFoundError("Project not found")

    def test_exceptions_importable_from_src_services(self):
        """All exceptions should be importable from src.services.__init__."""
        # This tests the __all__ export
        from src.services import ServiceError, TaskNotFoundError, ProjectNotFoundError
        assert ServiceError is not None
        assert TaskNotFoundError is not None
        assert ProjectNotFoundError is not None


# ─── Test Public Boundary Methods ────────────────────────────────────────────


class TestPublicWeekBoundaries:
    """Test public get_week_boundaries() method on TaskManager."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a TaskManager with temporary storage."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        return TaskManager(storage)

    def test_get_week_boundaries_is_public(self, manager):
        """get_week_boundaries should be a public method (no leading underscore)."""
        assert hasattr(manager, "get_week_boundaries")
        assert callable(getattr(manager, "get_week_boundaries"))
        # Ensure it's not private
        assert not hasattr(manager, "_get_week_boundaries") or (
            hasattr(manager, "get_week_boundaries") and
            not getattr(manager, "get_week_boundaries").__name__.startswith("_")
        )

    def test_get_week_boundaries_returns_tuple(self, manager):
        """Should return a tuple of (start, end) datetimes."""
        result = manager.get_week_boundaries(2026, 20)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], datetime)
        assert isinstance(result[1], datetime)

    def test_get_week_boundaries_valid_week_20(self, manager):
        """Should calculate correct boundaries for week 20 of 2026."""
        start, end = manager.get_week_boundaries(2026, 20)
        # Week 20, 2026: Monday May 11 to Sunday May 17
        assert start.year == 2026
        assert start.month == 5
        assert start.day == 11  # Monday
        assert start.hour == 0
        assert start.tzinfo == timezone.utc

        assert end.year == 2026
        assert end.month == 5
        assert end.day == 17  # Sunday
        assert end.tzinfo == timezone.utc

    def test_get_week_boundaries_week_1(self, manager):
        """Week 1 should follow ISO 8601 standard."""
        start, end = manager.get_week_boundaries(2026, 1)
        # 2026-01-01 is a Thursday, so week 1 starts Mon 2025-12-29
        assert start.month == 12
        assert start.year == 2025
        assert start.tzinfo == timezone.utc

    def test_get_week_boundaries_invalid_week_zero(self, manager):
        """Should raise ValueError for week 0."""
        with pytest.raises(ValueError, match="Week must be 1-53"):
            manager.get_week_boundaries(2026, 0)

    def test_get_week_boundaries_invalid_week_54(self, manager):
        """Should raise ValueError for week 54."""
        with pytest.raises(ValueError, match="Week must be 1-53"):
            manager.get_week_boundaries(2026, 54)

    def test_get_week_boundaries_invalid_week_negative(self, manager):
        """Should raise ValueError for negative week."""
        with pytest.raises(ValueError, match="Week must be 1-53"):
            manager.get_week_boundaries(2026, -1)

    def test_get_week_boundaries_utc_timezone(self, manager):
        """Week boundaries should always be in UTC."""
        start, end = manager.get_week_boundaries(2026, 20)
        assert start.tzinfo == timezone.utc
        assert end.tzinfo == timezone.utc


class TestPublicMonthBoundaries:
    """Test public get_month_boundaries() method on TaskManager."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a TaskManager with temporary storage."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        return TaskManager(storage)

    def test_get_month_boundaries_is_public(self, manager):
        """get_month_boundaries should be a public method."""
        assert hasattr(manager, "get_month_boundaries")
        assert callable(getattr(manager, "get_month_boundaries"))

    def test_get_month_boundaries_returns_tuple(self, manager):
        """Should return a tuple of (start, end) datetimes."""
        result = manager.get_month_boundaries(2026, 5)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], datetime)
        assert isinstance(result[1], datetime)

    def test_get_month_boundaries_valid_month(self, manager):
        """Should return correct start and end for May 2026."""
        start, end = manager.get_month_boundaries(2026, 5)

        assert start.year == 2026
        assert start.month == 5
        assert start.day == 1
        assert start.hour == 0
        assert start.minute == 0
        assert start.second == 0
        assert start.tzinfo == timezone.utc

        assert end.year == 2026
        assert end.month == 5
        assert end.day == 31
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59
        assert end.tzinfo == timezone.utc

    def test_get_month_boundaries_february_non_leap_year(self, manager):
        """February in non-leap year should end on 28th."""
        start, end = manager.get_month_boundaries(2025, 2)
        assert end.day == 28

    def test_get_month_boundaries_february_leap_year(self, manager):
        """February in leap year should end on 29th."""
        start, end = manager.get_month_boundaries(2024, 2)
        assert end.day == 29

    def test_get_month_boundaries_invalid_month_zero(self, manager):
        """Should raise ValueError for month 0."""
        with pytest.raises(ValueError, match="Month must be 1-12"):
            manager.get_month_boundaries(2026, 0)

    def test_get_month_boundaries_invalid_month_13(self, manager):
        """Should raise ValueError for month 13."""
        with pytest.raises(ValueError, match="Month must be 1-12"):
            manager.get_month_boundaries(2026, 13)

    def test_get_month_boundaries_invalid_month_negative(self, manager):
        """Should raise ValueError for negative month."""
        with pytest.raises(ValueError, match="Month must be 1-12"):
            manager.get_month_boundaries(2026, -1)

    def test_get_month_boundaries_utc_timezone(self, manager):
        """Month boundaries should be in UTC."""
        start, end = manager.get_month_boundaries(2026, 5)
        assert start.tzinfo == timezone.utc
        assert end.tzinfo == timezone.utc


class TestPublicYearBoundaries:
    """Test public get_year_boundaries() method on TaskManager."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a TaskManager with temporary storage."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        return TaskManager(storage)

    def test_get_year_boundaries_is_public(self, manager):
        """get_year_boundaries should be a public method."""
        assert hasattr(manager, "get_year_boundaries")
        assert callable(getattr(manager, "get_year_boundaries"))

    def test_get_year_boundaries_returns_tuple(self, manager):
        """Should return a tuple of (start, end) datetimes."""
        result = manager.get_year_boundaries(2026)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], datetime)
        assert isinstance(result[1], datetime)

    def test_get_year_boundaries_valid_year(self, manager):
        """Should return correct start and end for 2026."""
        start, end = manager.get_year_boundaries(2026)

        assert start.year == 2026
        assert start.month == 1
        assert start.day == 1
        assert start.hour == 0
        assert start.minute == 0
        assert start.second == 0
        assert start.tzinfo == timezone.utc

        assert end.year == 2026
        assert end.month == 12
        assert end.day == 31
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59
        assert end.tzinfo == timezone.utc

    def test_get_year_boundaries_leap_year(self, manager):
        """Should handle leap years correctly."""
        start, end = manager.get_year_boundaries(2024)
        assert start.year == 2024
        assert end.year == 2024

    def test_get_year_boundaries_utc_timezone(self, manager):
        """Year boundaries should be in UTC."""
        start, end = manager.get_year_boundaries(2026)
        assert start.tzinfo == timezone.utc
        assert end.tzinfo == timezone.utc


# ─── Test set_task() Method ──────────────────────────────────────────────────


class TestSetTaskMethod:
    """Test the set_task() method functionality."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a TaskManager with temporary storage."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        return TaskManager(storage)

    def test_set_task_exists(self, manager):
        """set_task() method should exist on TaskManager."""
        assert hasattr(manager, "set_task")
        assert callable(getattr(manager, "set_task"))

    def test_set_task_adds_new_task(self, manager):
        """set_task() should add a new task with the given ID."""
        task = Task(title="New Task")
        task_id = task.id

        manager.set_task(task_id, task)

        retrieved = manager.get(task_id)
        assert retrieved.id == task_id
        assert retrieved.title == "New Task"

    def test_set_task_replaces_existing_task(self, manager):
        """set_task() should replace an existing task."""
        # Create and add initial task
        task1 = Task(title="Original Title")
        task1_id = task1.id
        manager.set_task(task1_id, task1)

        # Replace with new task having the same ID but different title
        task2 = Task(title="Updated Title")
        task2.id = task1_id  # Use same ID
        manager.set_task(task1_id, task2)

        # Retrieve and verify replacement
        retrieved = manager.get(task1_id)
        assert retrieved.title == "Updated Title"

    def test_set_task_persists_to_storage(self, manager, tmp_path):
        """set_task() should persist the task to storage."""
        task = Task(title="Persisted Task")
        task_id = task.id

        manager.set_task(task_id, task)

        # Create new manager with same storage to verify persistence
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        manager2 = TaskManager(storage)

        retrieved = manager2.get(task_id)
        assert retrieved.title == "Persisted Task"

    def test_set_task_with_all_fields(self, manager):
        """set_task() should handle tasks with all fields set."""
        task = Task(
            title="Complete Task",
            description="Full description",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
            status=TaskStatus.IN_PROGRESS
        )
        task_id = task.id

        manager.set_task(task_id, task)

        retrieved = manager.get(task_id)
        assert retrieved.title == "Complete Task"
        assert retrieved.description == "Full description"
        assert retrieved.due_date == datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        assert retrieved.status == TaskStatus.IN_PROGRESS

    def test_set_task_with_comments(self, manager):
        """set_task() should preserve task comments."""
        task = Task(title="Task with Comments")
        task_id = task.id

        # Add some comments
        from src.models.task_comment import TaskComment
        comment = TaskComment(content="A comment", task_id=task_id)
        task.comments.append(comment)

        manager.set_task(task_id, task)

        retrieved = manager.get(task_id)
        assert len(retrieved.comments) == 1
        assert retrieved.comments[0].content == "A comment"


# ─── Test TodoService Uses Public Methods ────────────────────────────────────


class TestTodoServiceUsesPublicMethods:
    """Verify TodoService calls public methods on TaskManager."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create a TodoService with temporary storage."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        return TodoService(storage)

    def test_list_tasks_by_week_uses_public_method(self, service):
        """list_tasks_by_week() should work (using public get_week_boundaries())."""
        # Add some tasks
        dt = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        service.add_task("Task in week 20", due_date=dt)

        # Call list_tasks_by_week - this should use public get_week_boundaries()
        result = service.list_tasks_by_week(2026, 20)

        assert len(result) >= 1

    def test_list_tasks_by_month_uses_public_method(self, service):
        """list_tasks_by_month() should work (using public get_month_boundaries())."""
        dt = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        service.add_task("Task in May", due_date=dt)

        result = service.list_tasks_by_month(2026, 5)

        assert len(result) >= 1

    def test_list_tasks_by_year_uses_public_method(self, service):
        """list_tasks_by_year() should work (using public get_year_boundaries())."""
        dt = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        service.add_task("Task in 2026", due_date=dt)

        result = service.list_tasks_by_year(2026)

        assert len(result) >= 1


# ─── Test import_tasks() Uses set_task() ────────────────────────────────────


class TestImportTasksUsesSetTask:
    """Verify import_tasks() correctly uses set_task() internally."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create a TodoService with temporary storage."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        return TodoService(storage)

    @pytest.fixture
    def export_file(self, tmp_path):
        """Create a temporary export file with test tasks."""
        file_path = tmp_path / "export.json"
        tasks = [
            {
                "id": "task-1",
                "title": "Imported Task 1",
                "description": None,
                "status": "pending",
                "due_date": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "project_id": None,
                "comments": []
            },
            {
                "id": "task-2",
                "title": "Imported Task 2",
                "description": "With description",
                "status": "pending",
                "due_date": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "project_id": None,
                "comments": []
            }
        ]
        with open(file_path, "w") as f:
            json.dump(tasks, f)
        return str(file_path)

    def test_import_tasks_new_tasks(self, service, export_file):
        """import_tasks() should successfully import new tasks using set_task()."""
        result = service.import_tasks(export_file)

        assert result["imported_count"] == 2
        assert result["skipped_count"] == 0
        assert len(result["errors"]) == 0

        # Verify tasks were actually imported
        all_tasks = service.list_tasks()
        assert len(all_tasks) == 2

    def test_import_tasks_skip_duplicates(self, service, export_file):
        """import_tasks() should skip duplicates when using 'skip' strategy."""
        # Import once
        result1 = service.import_tasks(export_file, duplicate_strategy="skip")
        assert result1["imported_count"] == 2

        # Import again - should skip the duplicates
        result2 = service.import_tasks(export_file, duplicate_strategy="skip")
        assert result2["imported_count"] == 0
        assert result2["skipped_count"] == 2

    def test_import_tasks_replace_duplicates(self, service, export_file, tmp_path):
        """import_tasks() should replace duplicates when using 'replace' strategy."""
        # Import once
        result1 = service.import_tasks(export_file, duplicate_strategy="skip")
        assert result1["imported_count"] == 2

        # Verify original import
        task = service.get_task("task-1")
        assert task.title == "Imported Task 1"

        # Create modified export with replacement task
        modified_tasks = [
            {
                "id": "task-1",
                "title": "Modified Task 1",  # Changed title
                "description": None,
                "status": "pending",
                "due_date": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "project_id": None,
                "comments": []
            }
        ]
        modified_file = tmp_path / "modified_export.json"
        with open(modified_file, "w") as f:
            json.dump(modified_tasks, f)

        # Import with replace strategy
        result2 = service.import_tasks(str(modified_file), duplicate_strategy="replace")
        assert result2["skipped_count"] == 1  # Replacement counts as skipped in result

        # Verify replacement occurred
        task = service.get_task("task-1")
        assert task.title == "Modified Task 1"


# ─── Test CLI Exception Handling ─────────────────────────────────────────────


class TestCLIExceptionHandling:
    """Test that CLI can catch both exception types."""

    @pytest.fixture
    def cli(self, tmp_path):
        """Create a TodoCLI with temporary storage."""
        from src.cli.todo_cli import TodoCLI
        return TodoCLI(str(tmp_path / "tasks.json"))

    def test_cli_can_import_task_not_found_error(self):
        """TaskNotFoundError should be importable in CLI module."""
        from src.cli.todo_cli import TaskNotFoundError
        assert TaskNotFoundError is not None

    def test_cli_can_import_project_not_found_error(self):
        """ProjectNotFoundError should be importable in CLI module."""
        from src.cli.todo_cli import ProjectNotFoundError
        assert ProjectNotFoundError is not None

    def test_cli_catches_task_not_found_error(self, cli):
        """CLI should catch TaskNotFoundError gracefully."""
        # Try to delete a non-existent task
        result = cli.run(["delete", "nonexistent-task-id"])
        assert result == 1  # Should return error code

    def test_cli_catches_project_not_found_error(self, cli):
        """CLI should catch ProjectNotFoundError gracefully."""
        # Try to delete a non-existent project
        result = cli.run(["delete-project", "nonexistent-project-id"])
        assert result == 1  # Should return error code
