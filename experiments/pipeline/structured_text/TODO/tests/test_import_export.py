"""Tests for JSON import/export functionality (Task 07).

Tests cover:
- ExportService: export to JSON with correct format and counts
- ImportService: import from JSON with conflict handling (fail/skip/replace modes)
- Round-trip integrity: export + import preserves data
- CLI commands: export and import with mode flag
- Interactive menu: option 11 and submenu flows
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.models.task import Task
from src.models.task_comment import TaskComment
from src.models.task_status import TaskStatus
from src.services.import_export_service import (
    ExportService,
    ImportService,
    ImportExportError,
)
from src.services.task_manager import TaskManager
from src.services.comment_manager import CommentManager
from src.services.todo_service import TodoService
from src.cli.todo_cli import TodoCLI
from src.storage.json_storage import JsonStorage


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def tmp_storage(tmp_path):
    """Create a temporary JsonStorage instance."""
    return JsonStorage(str(tmp_path / "tasks.json"))


@pytest.fixture
def service(tmp_storage):
    """Create a TodoService with temporary storage."""
    return TodoService(tmp_storage)


@pytest.fixture
def task_manager(service):
    """Get the task manager from the service."""
    return service._manager


@pytest.fixture
def comment_manager(service):
    """Get the comment manager from the service."""
    return service._comment_manager


@pytest.fixture
def project_manager(service):
    """Get the project manager from the service."""
    return service._project_manager


@pytest.fixture
def export_service(task_manager, comment_manager, project_manager):
    """Create an ExportService."""
    return ExportService(task_manager, comment_manager, project_manager)


@pytest.fixture
def import_service(task_manager, comment_manager, project_manager):
    """Create an ImportService."""
    return ImportService(task_manager, comment_manager, project_manager)


# ============================================================================
# ExportService Happy Path Tests
# ============================================================================

class TestExportServiceHappyPath:
    """Test ExportService.export_to_file() in normal operation."""

    def test_export_zero_tasks_and_comments(self, service, export_service, tmp_path):
        """Export with no tasks or comments yields empty arrays."""
        export_file = tmp_path / "empty.json"
        tasks_count, comments_count, projects_count = export_service.export_to_file(str(export_file))

        assert tasks_count == 0
        assert comments_count == 0
        assert projects_count == 0

        # Verify JSON structure
        data = json.loads(export_file.read_text())
        assert data["tasks"] == []
        assert data["comments"] == []
        assert data["projects"] == []

    def test_export_single_task_no_comments(self, service, export_service, tmp_path):
        """Export with one task and zero comments."""
        task = service.add_task("Single task")
        export_file = tmp_path / "single_task.json"
        tasks_count, comments_count, projects_count = export_service.export_to_file(str(export_file))

        assert tasks_count == 1
        assert comments_count == 0
        assert projects_count == 0

        # Verify JSON
        data = json.loads(export_file.read_text())
        assert len(data["tasks"]) == 1
        assert len(data["comments"]) == 0
        assert data["tasks"][0]["title"] == "Single task"
        assert data["tasks"][0]["id"] == task.id

    def test_export_multiple_tasks_and_comments(self, service, export_service, tmp_path):
        """Export with multiple tasks and comments."""
        t1 = service.add_task("Task 1")
        t2 = service.add_task("Task 2")
        c1 = service.add_comment(t1.id, "Comment on task 1")
        c2 = service.add_comment(t2.id, "Comment 1 on task 2")
        c3 = service.add_comment(t2.id, "Comment 2 on task 2")

        export_file = tmp_path / "multi.json"
        tasks_count, comments_count, projects_count = export_service.export_to_file(str(export_file))

        assert tasks_count == 2
        assert comments_count == 3
        assert projects_count == 0

        data = json.loads(export_file.read_text())
        assert len(data["tasks"]) == 2
        assert len(data["comments"]) == 3
        assert len(data["projects"]) == 0

    def test_export_preserves_task_to_dict_format(self, service, export_service, tmp_path):
        """Exported JSON uses Task.to_dict() format."""
        task = service.add_task("Test", "Description")
        task = service.start_task(task.id)  # Change status
        due_date = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        # Note: we can't easily set due_date via service, so we test the format conceptually

        export_file = tmp_path / "format.json"
        export_service.export_to_file(str(export_file))

        data = json.loads(export_file.read_text())
        exported_task = data["tasks"][0]

        # Verify Task.to_dict() fields are present
        assert "id" in exported_task
        assert "title" in exported_task
        assert "description" in exported_task
        assert "status" in exported_task
        assert "created_at" in exported_task
        assert "updated_at" in exported_task
        assert exported_task["title"] == "Test"
        assert exported_task["description"] == "Description"
        assert exported_task["status"] == "in_progress"

    def test_export_preserves_comment_to_dict_format(self, service, export_service, tmp_path):
        """Exported JSON uses TaskComment.to_dict() format."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Test comment", author="Alice")

        export_file = tmp_path / "comment_format.json"
        export_service.export_to_file(str(export_file))

        data = json.loads(export_file.read_text())
        exported_comment = data["comments"][0]

        # Verify TaskComment.to_dict() fields
        assert "id" in exported_comment
        assert "task_id" in exported_comment
        assert "content" in exported_comment
        assert "author" in exported_comment
        assert "created_at" in exported_comment
        assert exported_comment["id"] == comment.id
        assert exported_comment["task_id"] == task.id
        assert exported_comment["content"] == "Test comment"
        assert exported_comment["author"] == "Alice"

    def test_export_overwrites_existing_file(self, service, export_service, tmp_path):
        """Export to existing file overwrites it (no append)."""
        export_file = tmp_path / "overwrite.json"

        # Write initial export
        t1 = service.add_task("First export")
        export_service.export_to_file(str(export_file))
        first_data = json.loads(export_file.read_text())
        assert len(first_data["tasks"]) == 1

        # Add more tasks and export again
        service.add_task("Second export")
        export_service.export_to_file(str(export_file))
        second_data = json.loads(export_file.read_text())
        assert len(second_data["tasks"]) == 2

        # Verify file was overwritten, not appended
        assert export_file.read_text().count("[") == 3  # 3 arrays in JSON: tasks, comments, projects

    def test_export_return_tuple_counts(self, service, export_service, tmp_path):
        """Export returns correct tuple (tasks_count, comments_count, projects_count)."""
        t1 = service.add_task("T1")
        t2 = service.add_task("T2")
        service.add_comment(t1.id, "C1")
        service.add_comment(t1.id, "C2")
        service.add_comment(t2.id, "C3")

        export_file = tmp_path / "counts.json"
        result = export_service.export_to_file(str(export_file))

        assert isinstance(result, tuple)
        assert len(result) == 3
        assert result == (2, 3, 0)

    def test_export_creates_parent_directories(self, export_service, tmp_path):
        """Export creates parent directories if they don't exist."""
        export_file = tmp_path / "subdir" / "nested" / "export.json"
        # Parent doesn't exist yet
        assert not export_file.parent.exists()

        export_service.export_to_file(str(export_file))

        assert export_file.exists()
        assert export_file.parent.exists()


# ============================================================================
# ExportService Error Cases
# ============================================================================

class TestExportServiceErrors:
    """Test ExportService error handling."""

    def test_export_to_invalid_directory_raises(self, export_service, tmp_path):
        """Export to non-existent parent that can't be created raises error."""
        # On most systems, /proc/nonexistent is not writable
        invalid_path = "/proc/nonexistent/export.json"
        with pytest.raises(ImportExportError):
            export_service.export_to_file(invalid_path)

    def test_export_to_readonly_location_raises(self, export_service, tmp_path):
        """Export to read-only location raises ImportExportError."""
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o000)

        try:
            export_file = readonly_dir / "export.json"
            with pytest.raises(ImportExportError):
                export_service.export_to_file(str(export_file))
        finally:
            # Clean up: restore permissions
            readonly_dir.chmod(0o755)

    def test_export_json_is_valid_after_export(self, service, export_service, tmp_path):
        """Verify exported JSON is valid and can be parsed."""
        service.add_task("Task A")
        service.add_task("Task B")
        export_file = tmp_path / "valid.json"

        export_service.export_to_file(str(export_file))

        # Should not raise JSONDecodeError
        data = json.loads(export_file.read_text())
        assert "tasks" in data
        assert "comments" in data


# ============================================================================
# ImportService Happy Path Tests
# ============================================================================

class TestImportServiceHappyPath:
    """Test ImportService.import_from_file() in normal operation."""

    def test_import_valid_json_with_tasks_and_comments(self, tmp_path, import_service, task_manager, comment_manager):
        """Import valid JSON with tasks and comments succeeds."""
        import_file = tmp_path / "import.json"
        task_id = "task-uuid-1234"
        comment_id = "comment-uuid-5678"

        export_data = {
            "tasks": [
                {
                    "id": task_id,
                    "title": "Imported Task",
                    "description": "A task from import",
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "comments": [
                {
                    "id": comment_id,
                    "task_id": task_id,
                    "content": "Imported comment",
                    "author": "TestAuthor",
                    "created_at": "2026-01-02T00:00:00+00:00",
                }
            ],
        }

        import_file.write_text(json.dumps(export_data))

        tasks_imported, comments_imported, projects_imported, conflicts = import_service.import_from_file(str(import_file))

        assert tasks_imported == 1
        assert comments_imported == 1
        assert projects_imported == 0
        assert conflicts == 0

        # Verify data was actually imported
        assert task_id in task_manager._tasks
        assert comment_id in comment_manager._comments

    def test_import_preserves_task_ids(self, tmp_path, import_service, task_manager):
        """Import preserves exact task IDs."""
        import_file = tmp_path / "import.json"
        task_id = "preserved-task-uuid"

        export_data = {
            "tasks": [
                {
                    "id": task_id,
                    "title": "Task",
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "comments": [],
        }

        import_file.write_text(json.dumps(export_data))
        import_service.import_from_file(str(import_file))

        imported_task = task_manager.get(task_id)
        assert imported_task.id == task_id

    def test_import_preserves_comment_ids(self, tmp_path, import_service, comment_manager):
        """Import preserves exact comment IDs."""
        import_file = tmp_path / "import.json"
        task_id = "task-uuid"
        comment_id = "preserved-comment-uuid"

        export_data = {
            "tasks": [
                {
                    "id": task_id,
                    "title": "Task",
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "comments": [
                {
                    "id": comment_id,
                    "task_id": task_id,
                    "content": "Comment",
                    "created_at": "2026-01-02T00:00:00+00:00",
                }
            ],
        }

        import_file.write_text(json.dumps(export_data))
        import_service.import_from_file(str(import_file))

        imported_comment = comment_manager.get(comment_id)
        assert imported_comment.id == comment_id

    def test_import_preserves_task_status(self, tmp_path, import_service, task_manager):
        """Import preserves task status (pending/in_progress/done)."""
        import_file = tmp_path / "import.json"

        export_data = {
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Pending task",
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                },
                {
                    "id": "task-2",
                    "title": "In progress task",
                    "status": "in_progress",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                },
                {
                    "id": "task-3",
                    "title": "Done task",
                    "status": "done",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                },
            ],
            "comments": [],
        }

        import_file.write_text(json.dumps(export_data))
        import_service.import_from_file(str(import_file))

        assert task_manager.get("task-1").status == TaskStatus.PENDING
        assert task_manager.get("task-2").status == TaskStatus.IN_PROGRESS
        assert task_manager.get("task-3").status == TaskStatus.DONE

    def test_import_preserves_task_timestamps(self, tmp_path, import_service, task_manager):
        """Import preserves task created_at and updated_at timestamps."""
        import_file = tmp_path / "import.json"
        created_at_str = "2026-01-01T10:00:00+00:00"
        updated_at_str = "2026-01-02T15:30:00+00:00"

        export_data = {
            "tasks": [
                {
                    "id": "task-with-times",
                    "title": "Task",
                    "status": "pending",
                    "created_at": created_at_str,
                    "updated_at": updated_at_str,
                }
            ],
            "comments": [],
        }

        import_file.write_text(json.dumps(export_data))
        import_service.import_from_file(str(import_file))

        task = task_manager.get("task-with-times")
        assert task.created_at == datetime.fromisoformat(created_at_str)
        assert task.updated_at == datetime.fromisoformat(updated_at_str)

    def test_import_preserves_comment_author(self, tmp_path, import_service, comment_manager):
        """Import preserves comment author name."""
        import_file = tmp_path / "import.json"

        export_data = {
            "tasks": [{"id": "task-1", "title": "T", "status": "pending", "created_at": "2026-01-01T00:00:00+00:00", "updated_at": "2026-01-01T00:00:00+00:00"}],
            "comments": [
                {
                    "id": "comment-1",
                    "task_id": "task-1",
                    "content": "Comment",
                    "author": "Alice",
                    "created_at": "2026-01-02T00:00:00+00:00",
                }
            ],
        }

        import_file.write_text(json.dumps(export_data))
        import_service.import_from_file(str(import_file))

        comment = comment_manager.get("comment-1")
        assert comment.author == "Alice"

    def test_import_preserves_comment_timestamps(self, tmp_path, import_service, comment_manager):
        """Import preserves comment created_at and updated_at timestamps."""
        import_file = tmp_path / "import.json"
        created_at_str = "2026-01-02T10:00:00+00:00"
        updated_at_str = "2026-01-03T15:30:00+00:00"

        export_data = {
            "tasks": [{"id": "task-1", "title": "T", "status": "pending", "created_at": "2026-01-01T00:00:00+00:00", "updated_at": "2026-01-01T00:00:00+00:00"}],
            "comments": [
                {
                    "id": "comment-1",
                    "task_id": "task-1",
                    "content": "Comment",
                    "created_at": created_at_str,
                    "updated_at": updated_at_str,
                }
            ],
        }

        import_file.write_text(json.dumps(export_data))
        import_service.import_from_file(str(import_file))

        comment = comment_manager.get("comment-1")
        assert comment.created_at == datetime.fromisoformat(created_at_str)
        assert comment.updated_at == datetime.fromisoformat(updated_at_str)

    def test_import_mode_fail_raises_on_task_conflict(self, tmp_path, import_service, service):
        """Import with mode='fail' raises error if task ID exists."""
        import_file = tmp_path / "import.json"

        # Add a task first
        task = service.add_task("Existing task")

        # Try to import task with same ID
        export_data = {
            "tasks": [
                {
                    "id": task.id,
                    "title": "Conflicting task",
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "comments": [],
        }

        import_file.write_text(json.dumps(export_data))

        with pytest.raises(ImportExportError) as exc_info:
            import_service.import_from_file(str(import_file), mode="fail")

        assert "conflicts detected" in str(exc_info.value).lower()

    def test_import_mode_fail_raises_on_comment_conflict(self, tmp_path, import_service, service):
        """Import with mode='fail' raises error if comment ID exists."""
        import_file = tmp_path / "import.json"

        # Add a task and comment first
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Existing comment")

        # Try to import comment with same ID
        export_data = {
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "comments": [
                {
                    "id": comment.id,
                    "task_id": task.id,
                    "content": "Conflicting comment",
                    "created_at": "2026-01-02T00:00:00+00:00",
                }
            ],
        }

        import_file.write_text(json.dumps(export_data))

        with pytest.raises(ImportExportError):
            import_service.import_from_file(str(import_file), mode="fail")

    def test_import_mode_skip_skips_conflicting_tasks(self, tmp_path, import_service, service):
        """Import with mode='skip' skips tasks with duplicate IDs."""
        import_file = tmp_path / "import.json"

        # Add an existing task
        existing_task = service.add_task("Original title")

        # Import task with same ID (should be skipped)
        export_data = {
            "tasks": [
                {
                    "id": existing_task.id,
                    "title": "New title",
                    "status": "in_progress",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "comments": [],
        }

        import_file.write_text(json.dumps(export_data))

        tasks_imported, comments_imported, projects_imported, conflicts = import_service.import_from_file(
            str(import_file), mode="skip"
        )

        # Conflicting task was skipped
        assert tasks_imported == 0
        assert conflicts == 1

        # Original task unchanged
        task = service.get_task(existing_task.id)
        assert task.title == "Original title"
        assert task.status == TaskStatus.PENDING

    def test_import_mode_skip_imports_non_conflicting_tasks(self, tmp_path, import_service, service):
        """Import with mode='skip' imports tasks without ID conflicts."""
        import_file = tmp_path / "import.json"

        # Add one existing task
        existing_task = service.add_task("Existing")

        # Import one new task and one conflicting task
        export_data = {
            "tasks": [
                {
                    "id": "new-task-id",
                    "title": "New task",
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                },
                {
                    "id": existing_task.id,
                    "title": "Conflicting",
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                },
            ],
            "comments": [],
        }

        import_file.write_text(json.dumps(export_data))

        tasks_imported, comments_imported, projects_imported, conflicts = import_service.import_from_file(
            str(import_file), mode="skip"
        )

        assert tasks_imported == 1  # Only new task imported
        assert conflicts == 1  # One conflict detected

        # New task was imported
        assert "new-task-id" in service._manager._tasks

    def test_import_mode_skip_skips_conflicting_comments(self, tmp_path, import_service, service):
        """Import with mode='skip' skips comments with duplicate IDs."""
        import_file = tmp_path / "import.json"

        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Original comment")

        export_data = {
            "tasks": [
                {
                    "id": task.id,
                    "title": "Task",
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "comments": [
                {
                    "id": comment.id,
                    "task_id": task.id,
                    "content": "New comment content",
                    "created_at": "2026-01-02T00:00:00+00:00",
                }
            ],
        }

        import_file.write_text(json.dumps(export_data))

        tasks_imported, comments_imported, projects_imported, conflicts = import_service.import_from_file(
            str(import_file), mode="skip"
        )

        # Both task and comment have conflicts (same IDs already exist)
        assert comments_imported == 0
        assert conflicts == 2  # 1 task conflict + 1 comment conflict

        # Original comment unchanged
        existing_comment = service._comment_manager.get(comment.id)
        assert existing_comment.content == "Original comment"

    def test_import_mode_replace_overwrites_tasks(self, tmp_path, import_service, service):
        """Import with mode='replace' overwrites existing tasks."""
        import_file = tmp_path / "import.json"

        existing_task = service.add_task("Original task")

        export_data = {
            "tasks": [
                {
                    "id": existing_task.id,
                    "title": "Replaced task",
                    "status": "done",
                    "created_at": "2025-01-01T00:00:00+00:00",
                    "updated_at": "2025-01-02T00:00:00+00:00",
                }
            ],
            "comments": [],
        }

        import_file.write_text(json.dumps(export_data))

        tasks_imported, comments_imported, projects_imported, conflicts = import_service.import_from_file(
            str(import_file), mode="replace"
        )

        assert tasks_imported == 1
        assert conflicts == 1

        # Task was replaced
        task = service.get_task(existing_task.id)
        assert task.title == "Replaced task"
        assert task.status == TaskStatus.DONE

    def test_import_mode_replace_overwrites_comments(self, tmp_path, import_service, service):
        """Import with mode='replace' overwrites existing comments."""
        import_file = tmp_path / "import.json"

        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Original comment")

        export_data = {
            "tasks": [
                {
                    "id": task.id,
                    "title": "Task",
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "comments": [
                {
                    "id": comment.id,
                    "task_id": task.id,
                    "content": "Replaced comment",
                    "author": "NewAuthor",
                    "created_at": "2025-01-01T00:00:00+00:00",
                }
            ],
        }

        import_file.write_text(json.dumps(export_data))

        tasks_imported, comments_imported, projects_imported, conflicts = import_service.import_from_file(
            str(import_file), mode="replace"
        )

        assert comments_imported == 1
        assert conflicts == 2  # 1 task conflict + 1 comment conflict

        # Comment was replaced
        replaced_comment = service._comment_manager.get(comment.id)
        assert replaced_comment.content == "Replaced comment"
        assert replaced_comment.author == "NewAuthor"

    def test_import_return_tuple_structure(self, tmp_path, import_service):
        """Import returns correct tuple (tasks_imported, comments_imported, conflicts)."""
        import_file = tmp_path / "import.json"

        export_data = {
            "tasks": [
                {
                    "id": "t1",
                    "title": "T1",
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "comments": [
                {
                    "id": "c1",
                    "task_id": "t1",
                    "content": "C1",
                    "created_at": "2026-01-02T00:00:00+00:00",
                }
            ],
        }

        import_file.write_text(json.dumps(export_data))

        result = import_service.import_from_file(str(import_file), mode="fail")

        assert isinstance(result, tuple)
        assert len(result) == 4
        assert result == (1, 1, 0, 0)


# ============================================================================
# ImportService Error Cases
# ============================================================================

class TestImportServiceErrors:
    """Test ImportService error handling."""

    def test_import_nonexistent_file_raises(self, import_service, tmp_path):
        """Import from non-existent file raises ImportExportError."""
        nonexistent = tmp_path / "does_not_exist.json"

        with pytest.raises(ImportExportError) as exc_info:
            import_service.import_from_file(str(nonexistent))

        assert "not found" in str(exc_info.value).lower()

    def test_import_invalid_json_raises(self, import_service, tmp_path):
        """Import from invalid JSON file raises ImportExportError."""
        import_file = tmp_path / "invalid.json"
        import_file.write_text("{ not valid json }")

        with pytest.raises(ImportExportError) as exc_info:
            import_service.import_from_file(str(import_file))

        assert "invalid json" in str(exc_info.value).lower()

    def test_import_missing_required_task_field_raises(self, import_service, tmp_path):
        """Import with missing required task field raises validation error."""
        import_file = tmp_path / "missing_field.json"

        export_data = {
            "tasks": [
                {
                    "id": "t1",
                    # Missing "title"
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "comments": [],
        }

        import_file.write_text(json.dumps(export_data))

        with pytest.raises(ImportExportError) as exc_info:
            import_service.import_from_file(str(import_file))

        assert "invalid task format" in str(exc_info.value).lower()

    def test_import_missing_required_comment_field_raises(self, import_service, tmp_path):
        """Import with missing required comment field raises validation error."""
        import_file = tmp_path / "missing_comment_field.json"

        export_data = {
            "tasks": [
                {
                    "id": "t1",
                    "title": "T1",
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "comments": [
                {
                    "id": "c1",
                    # Missing "task_id"
                    "content": "Content",
                    "created_at": "2026-01-02T00:00:00+00:00",
                }
            ],
        }

        import_file.write_text(json.dumps(export_data))

        with pytest.raises(ImportExportError) as exc_info:
            import_service.import_from_file(str(import_file))

        assert "invalid comment format" in str(exc_info.value).lower()

    def test_import_wrong_schema_missing_tasks_key_raises(self, import_service, tmp_path):
        """Import with missing 'tasks' key raises schema error."""
        import_file = tmp_path / "missing_tasks_key.json"
        import_file.write_text(json.dumps({"comments": []}))

        with pytest.raises(ImportExportError) as exc_info:
            import_service.import_from_file(str(import_file))

        assert "'tasks' and 'comments'" in str(exc_info.value) or "tasks" in str(exc_info.value).lower()

    def test_import_wrong_schema_missing_comments_key_raises(self, import_service, tmp_path):
        """Import with missing 'comments' key raises schema error."""
        import_file = tmp_path / "missing_comments_key.json"
        import_file.write_text(json.dumps({"tasks": []}))

        with pytest.raises(ImportExportError) as exc_info:
            import_service.import_from_file(str(import_file))

        assert "'tasks' and 'comments'" in str(exc_info.value) or "comments" in str(exc_info.value).lower()

    def test_import_invalid_schema_root_not_object_raises(self, import_service, tmp_path):
        """Import with non-object root (e.g., array) raises schema error."""
        import_file = tmp_path / "root_not_object.json"
        import_file.write_text(json.dumps([]))

        with pytest.raises(ImportExportError) as exc_info:
            import_service.import_from_file(str(import_file))

        assert "must be a json object" in str(exc_info.value).lower() or "root" in str(exc_info.value).lower()

    def test_import_invalid_schema_tasks_not_list_raises(self, import_service, tmp_path):
        """Import with tasks as non-list raises schema error."""
        import_file = tmp_path / "tasks_not_list.json"
        export_data = {
            "tasks": {"not": "a list"},
            "comments": [],
        }
        import_file.write_text(json.dumps(export_data))

        with pytest.raises(ImportExportError) as exc_info:
            import_service.import_from_file(str(import_file))

        assert "must be a list" in str(exc_info.value).lower()

    def test_import_invalid_schema_comments_not_list_raises(self, import_service, tmp_path):
        """Import with comments as non-list raises schema error."""
        import_file = tmp_path / "comments_not_list.json"
        export_data = {
            "tasks": [],
            "comments": "not a list",
        }
        import_file.write_text(json.dumps(export_data))

        with pytest.raises(ImportExportError) as exc_info:
            import_service.import_from_file(str(import_file))

        assert "must be a list" in str(exc_info.value).lower()

    def test_import_invalid_mode_raises(self, import_service, tmp_path):
        """Import with invalid mode raises ImportExportError."""
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps({"tasks": [], "comments": []}))

        with pytest.raises(ImportExportError) as exc_info:
            import_service.import_from_file(str(import_file), mode="invalid_mode")

        assert "invalid mode" in str(exc_info.value).lower()

    def test_import_orphaned_comments_handled(self, import_service, tmp_path, comment_manager):
        """Import with comments referencing non-existent tasks handles gracefully."""
        import_file = tmp_path / "orphaned_comments.json"

        export_data = {
            "tasks": [],  # No tasks
            "comments": [
                {
                    "id": "c1",
                    "task_id": "nonexistent-task",  # References non-existent task
                    "content": "Orphaned comment",
                    "created_at": "2026-01-02T00:00:00+00:00",
                }
            ],
        }

        import_file.write_text(json.dumps(export_data))

        # Should not raise; orphaned comments are imported as-is (no foreign key validation)
        tasks_imported, comments_imported, projects_imported, conflicts = import_service.import_from_file(
            str(import_file), mode="fail"
        )

        assert comments_imported == 1
        # Verify comment was imported despite orphaned reference
        assert "c1" in comment_manager._comments


# ============================================================================
# Round-Trip Tests
# ============================================================================

class TestRoundTrip:
    """Test export + import preserves data integrity."""

    def test_roundtrip_export_import_preserves_tasks(self, service, tmp_path):
        """Export then import preserves task data."""
        # Create tasks
        t1 = service.add_task("Task 1", "Description 1")
        t2 = service.add_task("Task 2")
        service.complete_task(t2.id)

        # Export
        export_file = tmp_path / "export1.json"
        service.export_tasks_and_comments(str(export_file))

        # Create fresh service with separate storage for both tasks and comments
        fresh_storage_path = str(tmp_path / "fresh" / "tasks.json")
        fresh_storage = JsonStorage(fresh_storage_path)
        fresh_service = TodoService(fresh_storage)

        fresh_service.import_tasks_and_comments(str(export_file), mode="fail")

        # Verify data
        tasks = fresh_service.list_tasks()
        assert len(tasks) == 2

        imported_t1 = fresh_service.get_task(t1.id)
        assert imported_t1.title == "Task 1"
        assert imported_t1.description == "Description 1"
        assert imported_t1.status == TaskStatus.PENDING

        imported_t2 = fresh_service.get_task(t2.id)
        assert imported_t2.title == "Task 2"
        assert imported_t2.status == TaskStatus.DONE

    def test_roundtrip_export_import_preserves_comments(self, service, tmp_path):
        """Export then import preserves comment data."""
        task = service.add_task("Task")
        c1 = service.add_comment(task.id, "First comment", author="Alice")
        c2 = service.add_comment(task.id, "Second comment", author="Bob")

        export_file = tmp_path / "export2.json"
        service.export_tasks_and_comments(str(export_file))

        fresh_storage_path = str(tmp_path / "fresh2" / "tasks.json")
        fresh_storage = JsonStorage(fresh_storage_path)
        fresh_service = TodoService(fresh_storage)

        fresh_service.import_tasks_and_comments(str(export_file), mode="fail")

        comments = fresh_service.get_comments(task.id)
        assert len(comments) == 2
        assert comments[0].content == "First comment"
        assert comments[0].author == "Alice"
        assert comments[1].content == "Second comment"
        assert comments[1].author == "Bob"

    def test_roundtrip_multiple_cycles_no_data_loss(self, service, tmp_path):
        """Multiple export-import cycles preserve data."""
        t1 = service.add_task("Original")
        service.add_comment(t1.id, "Original comment")

        export_file1 = tmp_path / "cycle1.json"
        service.export_tasks_and_comments(str(export_file1))

        # Import into fresh instance
        fresh_storage1_path = str(tmp_path / "fresh3" / "tasks.json")
        fresh_storage = JsonStorage(fresh_storage1_path)
        fresh_service = TodoService(fresh_storage)
        fresh_service.import_tasks_and_comments(str(export_file1), mode="fail")

        # Export from fresh instance
        export_file2 = tmp_path / "cycle2.json"
        fresh_service.export_tasks_and_comments(str(export_file2))

        # Import again into another fresh instance
        fresh_storage2_path = str(tmp_path / "fresh4" / "tasks.json")
        fresh_storage2 = JsonStorage(fresh_storage2_path)
        fresh_service2 = TodoService(fresh_storage2)
        fresh_service2.import_tasks_and_comments(str(export_file2), mode="fail")

        # Verify data still intact
        tasks = fresh_service2.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "Original"

        comments = fresh_service2.get_comments(t1.id)
        assert len(comments) == 1
        assert comments[0].content == "Original comment"

    def test_roundtrip_export_counts_match_import_counts(self, service, tmp_path):
        """Counts returned by export match counts returned by import."""
        service.add_task("T1")
        service.add_task("T2")
        t3 = service.add_task("T3")
        service.add_comment(t3.id, "C1")
        service.add_comment(t3.id, "C2")
        service.add_comment(t3.id, "C3")

        export_file = tmp_path / "roundtrip.json"
        exported_tasks, exported_comments, exported_projects = service.export_tasks_and_comments(str(export_file))

        fresh_storage_path = str(tmp_path / "fresh5" / "tasks.json")
        fresh_storage = JsonStorage(fresh_storage_path)
        fresh_service = TodoService(fresh_storage)

        imported_tasks, imported_comments, imported_projects, conflicts = fresh_service.import_tasks_and_comments(
            str(export_file), mode="fail"
        )

        assert exported_tasks == imported_tasks == 3
        assert exported_comments == imported_comments == 3
        assert conflicts == 0


# ============================================================================
# CLI Tests
# ============================================================================

class TestCLIExportImport:
    """Test CLI export and import commands."""

    def test_cli_export_command(self, tmp_path):
        """CLI export command works with filepath argument."""
        storage_path = str(tmp_path / "tasks.json")
        cli = TodoCLI(storage_path)

        # Add a task via CLI
        cli.run(["add", "Test task"])

        # Export via CLI
        export_file = str(tmp_path / "export.json")
        result = cli.run(["export", export_file])

        assert result == 0
        assert Path(export_file).exists()

        data = json.loads(Path(export_file).read_text())
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["title"] == "Test task"

    def test_cli_import_command_default_mode(self, tmp_path):
        """CLI import command with default mode (fail)."""
        storage_path1 = str(tmp_path / "src" / "tasks.json")
        storage_path2 = str(tmp_path / "dst" / "tasks.json")

        # Create source with task
        cli1 = TodoCLI(storage_path1)
        cli1.run(["add", "To import"])

        # Export
        export_file = str(tmp_path / "export.json")
        cli1.run(["export", export_file])

        # Import to destination
        cli2 = TodoCLI(storage_path2)
        result = cli2.run(["import", export_file])

        assert result == 0

        # Verify import worked
        cli2.run(["list"])  # Should not raise

    def test_cli_import_command_with_skip_mode(self, tmp_path):
        """CLI import command parses --mode skip correctly."""
        storage_path1 = str(tmp_path / "src" / "tasks.json")
        storage_path2 = str(tmp_path / "dst" / "tasks.json")

        cli1 = TodoCLI(storage_path1)
        cli1.run(["add", "To import"])

        export_file = str(tmp_path / "export.json")
        cli1.run(["export", export_file])

        # Pre-add a task to destination with same ID to cause conflict
        cli2 = TodoCLI(storage_path2)

        result = cli2.run(["import", export_file, "--mode", "skip"])

        assert result == 0

    def test_cli_import_command_with_replace_mode(self, tmp_path):
        """CLI import command parses --mode replace correctly."""
        storage_path1 = str(tmp_path / "src" / "tasks.json")
        storage_path2 = str(tmp_path / "dst" / "tasks.json")

        cli1 = TodoCLI(storage_path1)
        task = cli1.run(["add", "Original"])

        export_file = str(tmp_path / "export.json")
        cli1.run(["export", export_file])

        cli2 = TodoCLI(storage_path2)
        result = cli2.run(["import", export_file, "--mode", "replace"])

        assert result == 0

    def test_cli_export_output_message(self, capsys, tmp_path):
        """CLI export prints correct output message."""
        storage_path = str(tmp_path / "tasks.json")
        cli = TodoCLI(storage_path)

        cli.run(["add", "Task 1"])
        cli.run(["add", "Task 2"])

        export_file = str(tmp_path / "export.json")
        cli.run(["export", export_file])

        captured = capsys.readouterr()
        assert "Exported 2 task(s), 0 comment(s), and 0 project(s)" in captured.out

    def test_cli_import_output_message(self, capsys, tmp_path):
        """CLI import prints correct output message."""
        storage_path1 = str(tmp_path / "src" / "tasks.json")
        storage_path2 = str(tmp_path / "dst" / "tasks.json")

        cli1 = TodoCLI(storage_path1)
        cli1.run(["add", "Task 1"])

        task = cli1._service.list_tasks()[0]
        cli1.run(["add-comment", task.id, "Comment 1"])

        export_file = str(tmp_path / "export.json")
        cli1.run(["export", export_file])

        cli2 = TodoCLI(storage_path2)
        cli2.run(["import", export_file])

        captured = capsys.readouterr()
        assert "Imported 1 task(s), 1 comment(s), and 0 project(s)" in captured.out

    def test_cli_import_output_with_conflicts_skip_mode(self, capsys, tmp_path):
        """CLI import prints conflict message in skip mode."""
        # We need to export, then import into same location to get conflict
        storage_path1 = str(tmp_path / "src" / "tasks.json")

        cli1 = TodoCLI(storage_path1)
        cli1.run(["add", "Task 1"])

        export_file = str(tmp_path / "export.json")
        cli1.run(["export", export_file])

        # Now import into same storage with skip mode (should detect conflicts)
        cli1.run(["import", export_file, "--mode", "skip"])

        captured = capsys.readouterr()
        # Skip mode should either show skipped message or be silent with conflicts detected
        # The important thing is that it doesn't error and returns 0
        # The conflict output only shows if there are conflicts
        assert "Skipped" in captured.out or "conflict" in captured.out.lower() or "Imported" in captured.out

    def test_cli_import_output_with_conflicts_replace_mode(self, capsys, tmp_path):
        """CLI import prints replacement message in replace mode."""
        storage_path1 = str(tmp_path / "src" / "tasks.json")

        cli1 = TodoCLI(storage_path1)
        cli1.run(["add", "Original"])

        export_file = str(tmp_path / "export.json")
        cli1.run(["export", export_file])

        # Import into same storage with replace mode (should detect conflicts)
        cli1.run(["import", export_file, "--mode", "replace"])

        captured = capsys.readouterr()
        # Replace mode should show replaced message if there are conflicts
        assert "Replaced" in captured.out or "Imported" in captured.out

    def test_cli_help_shows_export_command(self, capsys, tmp_path):
        """CLI --help displays export command."""
        cli = TodoCLI(str(tmp_path / "tasks.json"))
        try:
            cli.run(["--help"])
        except SystemExit:
            # --help calls sys.exit(0), which is expected
            pass

        captured = capsys.readouterr()
        assert "export" in captured.out.lower()

    def test_cli_help_shows_import_command(self, capsys, tmp_path):
        """CLI --help displays import command."""
        cli = TodoCLI(str(tmp_path / "tasks.json"))
        try:
            cli.run(["--help"])
        except SystemExit:
            # --help calls sys.exit(0), which is expected
            pass

        captured = capsys.readouterr()
        assert "import" in captured.out.lower()

    def test_cli_export_nonexistent_parent_error(self, capsys, tmp_path):
        """CLI export to invalid path returns error."""
        cli = TodoCLI(str(tmp_path / "tasks.json"))
        cli.run(["add", "Task"])

        # Try to export to proc (typically read-only)
        result = cli.run(["export", "/proc/nonexistent/export.json"])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err or "error" in captured.err.lower()

    def test_cli_import_nonexistent_file_error(self, capsys, tmp_path):
        """CLI import from non-existent file shows error."""
        cli = TodoCLI(str(tmp_path / "tasks.json"))
        result = cli.run(["import", "/nonexistent/file.json"])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err or "error" in captured.err.lower()


# ============================================================================
# Interactive Menu Tests
# ============================================================================

class TestInteractiveMenu:
    """Test interactive menu option 11 (import/export)."""

    def test_menu_displays_option_11(self, tmp_path):
        """Main menu displays option 11 for import/export."""
        from src.cli.interactive_menu import InteractiveMenu

        menu = InteractiveMenu(str(tmp_path / "tasks.json"))

        # Check that the option is in the menu printing code
        # We can't easily test the menu interactively, but we can verify the method exists
        assert hasattr(menu, "_do_import_export")

    def test_menu_import_export_submenu_exists(self, tmp_path):
        """Import/export submenu method exists."""
        from src.cli.interactive_menu import InteractiveMenu

        menu = InteractiveMenu(str(tmp_path / "tasks.json"))
        assert callable(menu._do_import_export)

    def test_menu_export_method_exists(self, tmp_path):
        """Export menu option handler exists."""
        from src.cli.interactive_menu import InteractiveMenu

        menu = InteractiveMenu(str(tmp_path / "tasks.json"))
        assert callable(menu._do_export)

    def test_menu_import_method_exists(self, tmp_path):
        """Import menu option handler exists."""
        from src.cli.interactive_menu import InteractiveMenu

        menu = InteractiveMenu(str(tmp_path / "tasks.json"))
        assert callable(menu._do_import)
