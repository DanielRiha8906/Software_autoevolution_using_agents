import pytest
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from src.models.task import Task
from src.models.task_comment import TaskComment
from src.models.task_status import TaskStatus
from src.services.import_export_service import ImportExportService
from src.services.task_manager import TaskManager
from src.services.comments_service import CommentsService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def temp_storage(tmp_path):
    """Create a temporary storage for tests."""
    storage_path = tmp_path / "test_data.json"
    return JsonStorage(str(storage_path)), str(storage_path)


@pytest.fixture
def setup_services(temp_storage):
    """Set up manager, comments service, and import/export service."""
    storage, _ = temp_storage
    manager = TaskManager(storage)
    comments_service = CommentsService(manager, storage)
    import_export = ImportExportService(manager, comments_service)
    return manager, comments_service, import_export


class TestExport:
    def test_export_empty_database(self, setup_services, tmp_path):
        """Test exporting an empty database."""
        manager, comments_service, import_export = setup_services
        export_file = tmp_path / "export.json"

        count = import_export.export_to_file(str(export_file))

        assert count == 0
        assert export_file.exists()
        with open(export_file) as f:
            data = json.load(f)
            assert data["tasks"] == []
            assert data["comments"] == []

    def test_export_with_tasks_only(self, setup_services, tmp_path):
        """Test exporting database with tasks but no comments."""
        manager, comments_service, import_export = setup_services

        task1 = manager.add("Task 1", "Description 1")
        task2 = manager.add("Task 2")

        export_file = tmp_path / "export.json"
        count = import_export.export_to_file(str(export_file))

        assert count == 2
        with open(export_file) as f:
            data = json.load(f)
            assert len(data["tasks"]) == 2
            assert len(data["comments"]) == 0
            assert data["tasks"][0]["title"] == "Task 1"
            assert data["tasks"][1]["title"] == "Task 2"

    def test_export_with_tasks_and_comments(self, setup_services, tmp_path):
        """Test exporting database with tasks and comments."""
        manager, comments_service, import_export = setup_services

        task = manager.add("Task", "Description")
        comment1 = comments_service.add_comment(task.id, "Comment 1", author="User1")
        comment2 = comments_service.add_comment(task.id, "Comment 2", author="User2")

        export_file = tmp_path / "export.json"
        count = import_export.export_to_file(str(export_file))

        assert count == 3  # 1 task + 2 comments
        with open(export_file) as f:
            data = json.load(f)
            assert len(data["tasks"]) == 1
            assert len(data["comments"]) == 2
            assert data["comments"][0]["task_id"] == task.id
            assert data["comments"][0]["author"] == "User1"

    def test_export_preserves_all_task_fields(self, setup_services, tmp_path):
        """Test that export preserves all task fields including due_date."""
        manager, comments_service, import_export = setup_services

        due_date = datetime(2026, 12, 25, 15, 30, 0, tzinfo=timezone.utc)
        task = manager.add("Task with due date")
        task.due_date = due_date
        task.status = TaskStatus.IN_PROGRESS
        manager._persist()

        export_file = tmp_path / "export.json"
        import_export.export_to_file(str(export_file))

        with open(export_file) as f:
            data = json.load(f)
            exported_task = data["tasks"][0]
            assert exported_task["title"] == "Task with due date"
            assert exported_task["status"] == "in_progress"
            assert exported_task["due_date"] is not None


class TestImport:
    def test_import_valid_json_with_tasks(self, setup_services, tmp_path):
        """Test importing valid JSON with tasks."""
        manager, comments_service, import_export = setup_services

        # Create a JSON file with tasks
        import_file = tmp_path / "import.json"
        data = {
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Imported Task 1",
                    "description": "Description 1",
                    "status": "pending",
                    "created_at": "2026-01-01T10:00:00+00:00",
                    "updated_at": "2026-01-01T10:00:00+00:00",
                    "due_date": None,
                }
            ],
            "comments": [],
        }
        with open(import_file, "w") as f:
            json.dump(data, f)

        summary = import_export.import_from_file(str(import_file))

        assert summary.tasks_imported == 1
        assert summary.comments_imported == 0
        assert len(manager._tasks) == 1
        assert manager._tasks["task-1"].title == "Imported Task 1"

    def test_import_valid_json_with_comments(self, setup_services, tmp_path):
        """Test importing valid JSON with tasks and comments."""
        manager, comments_service, import_export = setup_services

        # First create a task in the system
        task = manager.add("Existing Task")

        # Create a JSON file with comments for the existing task
        import_file = tmp_path / "import.json"
        data = {
            "tasks": [],
            "comments": [
                {
                    "id": "comment-1",
                    "task_id": task.id,
                    "content": "Imported comment",
                    "created_at": "2026-01-01T10:00:00+00:00",
                    "author": "Importer",
                }
            ],
        }
        with open(import_file, "w") as f:
            json.dump(data, f)

        summary = import_export.import_from_file(str(import_file))

        assert summary.comments_imported == 1
        assert len(comments_service._comments) == 1
        assert comments_service._comments["comment-1"].content == "Imported comment"

    def test_import_invalid_json_structure(self, setup_services, tmp_path):
        """Test importing invalid JSON structure."""
        manager, comments_service, import_export = setup_services

        # Create a JSON file with invalid structure
        import_file = tmp_path / "invalid.json"
        with open(import_file, "w") as f:
            f.write('{"invalid": "structure"}')

        summary = import_export.import_from_file(str(import_file))

        assert summary.tasks_imported == 0
        assert summary.comments_imported == 0

    def test_import_malformed_json(self, setup_services, tmp_path):
        """Test importing malformed JSON."""
        manager, comments_service, import_export = setup_services

        # Create a file with invalid JSON
        import_file = tmp_path / "malformed.json"
        with open(import_file, "w") as f:
            f.write('{invalid json}')

        with pytest.raises(ValueError, match="Invalid JSON"):
            import_export.import_from_file(str(import_file))

    def test_import_nonexistent_file(self, setup_services, tmp_path):
        """Test importing from nonexistent file."""
        manager, comments_service, import_export = setup_services

        with pytest.raises(FileNotFoundError):
            import_export.import_from_file(str(tmp_path / "nonexistent.json"))

    def test_import_duplicate_task_ids_skipped(self, setup_services, tmp_path):
        """Test that duplicate task IDs are skipped during import."""
        manager, comments_service, import_export = setup_services

        # Add a task to the system
        existing_task = manager.add("Existing Task")

        # Create a JSON file with duplicate task ID
        import_file = tmp_path / "import.json"
        data = {
            "tasks": [
                {
                    "id": existing_task.id,
                    "title": "Duplicate Task",
                    "description": None,
                    "status": "pending",
                    "created_at": "2026-01-01T10:00:00+00:00",
                    "updated_at": "2026-01-01T10:00:00+00:00",
                    "due_date": None,
                }
            ],
            "comments": [],
        }
        with open(import_file, "w") as f:
            json.dump(data, f)

        summary = import_export.import_from_file(str(import_file))

        assert summary.tasks_imported == 0
        assert summary.tasks_skipped == 1
        # Original task should still have original title
        assert manager._tasks[existing_task.id].title == "Existing Task"

    def test_import_duplicate_comment_ids_skipped(self, setup_services, tmp_path):
        """Test that duplicate comment IDs are skipped during import."""
        manager, comments_service, import_export = setup_services

        task = manager.add("Task")
        existing_comment = comments_service.add_comment(task.id, "Existing comment")

        # Create a JSON file with duplicate comment ID
        import_file = tmp_path / "import.json"
        data = {
            "tasks": [],
            "comments": [
                {
                    "id": existing_comment.id,
                    "task_id": task.id,
                    "content": "Duplicate comment",
                    "created_at": "2026-01-01T10:00:00+00:00",
                    "author": None,
                }
            ],
        }
        with open(import_file, "w") as f:
            json.dump(data, f)

        summary = import_export.import_from_file(str(import_file))

        assert summary.comments_imported == 0
        assert summary.comments_skipped == 1
        # Original comment should still have original content
        assert comments_service._comments[existing_comment.id].content == "Existing comment"

    def test_import_comment_with_missing_task(self, setup_services, tmp_path):
        """Test that comments with missing tasks are skipped."""
        manager, comments_service, import_export = setup_services

        # Create a JSON file with comment for non-existent task
        import_file = tmp_path / "import.json"
        data = {
            "tasks": [],
            "comments": [
                {
                    "id": "comment-1",
                    "task_id": "nonexistent-task",
                    "content": "Comment for missing task",
                    "created_at": "2026-01-01T10:00:00+00:00",
                    "author": None,
                }
            ],
        }
        with open(import_file, "w") as f:
            json.dump(data, f)

        summary = import_export.import_from_file(str(import_file))

        assert summary.comments_imported == 0
        assert summary.comments_skipped == 1

    def test_import_invalid_task_data(self, setup_services, tmp_path):
        """Test that invalid task data is skipped."""
        manager, comments_service, import_export = setup_services

        # Create a JSON file with invalid task (missing title)
        import_file = tmp_path / "import.json"
        data = {
            "tasks": [
                {
                    "id": "task-1",
                    "description": "No title",
                    "status": "pending",
                    "created_at": "2026-01-01T10:00:00+00:00",
                    "updated_at": "2026-01-01T10:00:00+00:00",
                    "due_date": None,
                }
            ],
            "comments": [],
        }
        with open(import_file, "w") as f:
            json.dump(data, f)

        summary = import_export.import_from_file(str(import_file))

        assert summary.tasks_imported == 0
        assert summary.tasks_skipped == 1

    def test_import_merges_data(self, setup_services, tmp_path):
        """Test that import merges with existing data when merge=True."""
        manager, comments_service, import_export = setup_services

        # Add existing task
        existing_task = manager.add("Existing Task")

        # Import new tasks
        import_file = tmp_path / "import.json"
        data = {
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Imported Task",
                    "description": None,
                    "status": "pending",
                    "created_at": "2026-01-01T10:00:00+00:00",
                    "updated_at": "2026-01-01T10:00:00+00:00",
                    "due_date": None,
                }
            ],
            "comments": [],
        }
        with open(import_file, "w") as f:
            json.dump(data, f)

        summary = import_export.import_from_file(str(import_file), merge=True)

        # Both tasks should exist
        assert len(manager._tasks) == 2
        assert manager._tasks[existing_task.id].title == "Existing Task"
        assert manager._tasks["task-1"].title == "Imported Task"

    def test_import_preserves_task_attributes(self, setup_services, tmp_path):
        """Test that import preserves task IDs, statuses, and due dates."""
        manager, comments_service, import_export = setup_services

        import_file = tmp_path / "import.json"
        task_id = "preserved-task-id"
        due_date_str = "2026-12-25T15:30:00+00:00"
        data = {
            "tasks": [
                {
                    "id": task_id,
                    "title": "Task with attributes",
                    "description": "Test",
                    "status": "in_progress",
                    "created_at": "2026-01-01T10:00:00+00:00",
                    "updated_at": "2026-01-01T10:00:00+00:00",
                    "due_date": due_date_str,
                }
            ],
            "comments": [],
        }
        with open(import_file, "w") as f:
            json.dump(data, f)

        summary = import_export.import_from_file(str(import_file))

        assert summary.tasks_imported == 1
        imported_task = manager._tasks[task_id]
        assert imported_task.id == task_id
        assert imported_task.status == TaskStatus.IN_PROGRESS
        assert imported_task.due_date is not None
        assert imported_task.due_date.isoformat() == due_date_str

    def test_import_with_partial_invalid_data(self, setup_services, tmp_path):
        """Test that valid items are imported even if some are invalid."""
        manager, comments_service, import_export = setup_services

        import_file = tmp_path / "import.json"
        data = {
            "tasks": [
                {
                    "id": "valid-task",
                    "title": "Valid Task",
                    "description": None,
                    "status": "pending",
                    "created_at": "2026-01-01T10:00:00+00:00",
                    "updated_at": "2026-01-01T10:00:00+00:00",
                    "due_date": None,
                },
                {
                    "id": "invalid-task",
                    # Missing title
                    "status": "pending",
                    "created_at": "2026-01-01T10:00:00+00:00",
                    "updated_at": "2026-01-01T10:00:00+00:00",
                    "due_date": None,
                },
            ],
            "comments": [],
        }
        with open(import_file, "w") as f:
            json.dump(data, f)

        summary = import_export.import_from_file(str(import_file))

        assert summary.tasks_imported == 1
        assert summary.tasks_skipped == 1
        assert "valid-task" in manager._tasks

    def test_roundtrip_export_import(self, setup_services, tmp_path):
        """Test that data can be exported and reimported without loss."""
        manager, comments_service, import_export = setup_services

        # Create some data
        task1 = manager.add("Task 1", "Description 1")
        task2 = manager.add("Task 2")
        task2.status = TaskStatus.DONE
        manager._persist()

        comment1 = comments_service.add_comment(task1.id, "Comment 1", "User1")
        comment2 = comments_service.add_comment(task1.id, "Comment 2", "User2")

        # Export
        export_file = tmp_path / "export.json"
        export_count = import_export.export_to_file(str(export_file))

        # Create new storage and re-import
        new_storage = JsonStorage(str(tmp_path / "new_data.json"))
        new_manager = TaskManager(new_storage)
        new_comments = CommentsService(new_manager, new_storage)
        new_import_export = ImportExportService(new_manager, new_comments)

        summary = new_import_export.import_from_file(str(export_file))

        # Verify all data was imported
        assert summary.tasks_imported == 2
        assert summary.comments_imported == 2

        # Verify attributes are preserved
        assert new_manager._tasks[task1.id].title == "Task 1"
        assert new_manager._tasks[task2.id].status == TaskStatus.DONE
        assert len(new_comments._comments) == 2
