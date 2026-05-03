import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

from src.services.task_import_export_service import TaskImportExportService
from src.services.todo_service import TodoService
from src.services.comments_service import CommentsService
from src.models.task import Task, CEST
from src.models.task_comment import TaskComment
from src.models.task_status import TaskStatus
from src.storage.json_storage import JsonStorage


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def services(temp_dir):
    """Create service instances with isolated storage."""
    storage = JsonStorage(temp_dir / "data.json")
    todo_service = TodoService(storage)
    comments_service = CommentsService(todo_service, storage)
    return todo_service, comments_service


@pytest.fixture
def import_export_service(services):
    """Create the import/export service."""
    todo_service, comments_service = services
    return TaskImportExportService(todo_service, comments_service)


class TestExport:
    """Tests for the export functionality."""

    def test_export_creates_json_file(self, import_export_service, temp_dir):
        """Test that export creates a JSON file at the specified path."""
        export_file = temp_dir / "export.json"

        import_export_service.export(str(export_file))

        assert export_file.exists()
        assert export_file.suffix == ".json"

    def test_export_contains_tasks_and_comments(self, import_export_service, services, temp_dir):
        """Test that exported JSON contains tasks and comments arrays with correct structure."""
        todo_service, comments_service = services

        # Add a task
        task = todo_service.add_task("Test Task", "A description")

        # Add a comment to the task
        comment = comments_service.add_comment(task.id, "Test comment")

        export_file = temp_dir / "export.json"
        import_export_service.export(str(export_file))

        # Read and verify JSON structure
        with open(export_file) as f:
            data = json.load(f)

        assert "tasks" in data
        assert "comments" in data
        assert isinstance(data["tasks"], list)
        assert isinstance(data["comments"], list)

        # Verify task data
        assert len(data["tasks"]) == 1
        exported_task = data["tasks"][0]
        assert exported_task["id"] == task.id
        assert exported_task["title"] == "Test Task"
        assert exported_task["description"] == "A description"
        assert exported_task["status"] == TaskStatus.PENDING.value

        # Verify comment data
        assert len(data["comments"]) == 1
        exported_comment = data["comments"][0]
        assert exported_comment["id"] == comment.id
        assert exported_comment["task_id"] == task.id
        assert exported_comment["content"] == "Test comment"

    def test_export_empty_tasks_and_comments(self, import_export_service, temp_dir):
        """Test exporting with no tasks or comments."""
        export_file = temp_dir / "export.json"

        import_export_service.export(str(export_file))

        with open(export_file) as f:
            data = json.load(f)

        assert data["tasks"] == []
        assert data["comments"] == []

    def test_export_with_multiple_tasks(self, import_export_service, services, temp_dir):
        """Test exporting multiple tasks."""
        todo_service, _ = services

        task1 = todo_service.add_task("Task 1")
        task2 = todo_service.add_task("Task 2")
        task3 = todo_service.add_task("Task 3")

        export_file = temp_dir / "export.json"
        import_export_service.export(str(export_file))

        with open(export_file) as f:
            data = json.load(f)

        assert len(data["tasks"]) == 3
        task_ids = {t["id"] for t in data["tasks"]}
        assert task1.id in task_ids
        assert task2.id in task_ids
        assert task3.id in task_ids

    def test_export_with_due_dates(self, import_export_service, services, temp_dir):
        """Test exporting tasks with due dates."""
        todo_service, _ = services

        due_date = datetime(2025, 12, 31, 23, 59, tzinfo=CEST)
        task = todo_service.add_task("Task with due date", due_date=due_date)

        export_file = temp_dir / "export.json"
        import_export_service.export(str(export_file))

        with open(export_file) as f:
            data = json.load(f)

        assert len(data["tasks"]) == 1
        assert "due_date" in data["tasks"][0]
        assert data["tasks"][0]["due_date"] == due_date.isoformat()


class TestImport:
    """Tests for the import functionality."""

    def test_import_restores_tasks(self, import_export_service, services, temp_dir):
        """Test that import restores tasks from a JSON file."""
        todo_service1, comments_service1 = services

        # Export data from first service
        task1 = todo_service1.add_task("Original Task", "Original description")
        export_file = temp_dir / "export.json"
        import_export_service.export(str(export_file))

        # Create new services with clean storage
        storage2 = JsonStorage(temp_dir / "data2.json")
        todo_service2 = TodoService(storage2)
        comments_service2 = CommentsService(todo_service2, storage2)
        import_export_service2 = TaskImportExportService(todo_service2, comments_service2)

        # Import into second service
        imported_tasks, _ = import_export_service2.import_from(str(export_file))

        # Verify task was imported
        assert len(imported_tasks) == 1
        imported_task = imported_tasks[0]
        assert imported_task.id == task1.id
        assert imported_task.title == "Original Task"
        assert imported_task.description == "Original description"

        # Verify task is accessible from the service
        retrieved_task = todo_service2.get_task(task1.id)
        assert retrieved_task.id == task1.id

    def test_import_restores_comments(self, import_export_service, services, temp_dir):
        """Test that import restores comments from a JSON file."""
        todo_service1, comments_service1 = services

        # Export data from first service
        task1 = todo_service1.add_task("Task with comments")
        comment1 = comments_service1.add_comment(task1.id, "First comment")
        comment2 = comments_service1.add_comment(task1.id, "Second comment")
        export_file = temp_dir / "export.json"
        import_export_service.export(str(export_file))

        # Create new services with clean storage
        storage2 = JsonStorage(temp_dir / "data2.json")
        todo_service2 = TodoService(storage2)
        comments_service2 = CommentsService(todo_service2, storage2)
        import_export_service2 = TaskImportExportService(todo_service2, comments_service2)

        # Import into second service
        _, imported_comments = import_export_service2.import_from(str(export_file))

        # Verify comments were imported
        assert len(imported_comments) == 2
        comment_ids = {c.id for c in imported_comments}
        assert comment1.id in comment_ids
        assert comment2.id in comment_ids

        # Verify comments are accessible from the service
        retrieved_comments = comments_service2.list_comments(task1.id)
        assert len(retrieved_comments) == 2

    def test_import_validates_structure(self, import_export_service, temp_dir):
        """Test that import validates JSON structure."""
        # Test invalid JSON
        bad_json_file = temp_dir / "bad.json"
        bad_json_file.write_text("{invalid json")

        with pytest.raises(ValueError, match="Invalid JSON format"):
            import_export_service.import_from(str(bad_json_file))

        # Test missing tasks array
        no_tasks_file = temp_dir / "no_tasks.json"
        no_tasks_file.write_text(json.dumps({"comments": []}))

        with pytest.raises(ValueError, match="must contain 'tasks'"):
            import_export_service.import_from(str(no_tasks_file))

        # Test missing comments array
        no_comments_file = temp_dir / "no_comments.json"
        no_comments_file.write_text(json.dumps({"tasks": []}))

        with pytest.raises(ValueError, match="must contain 'comments'"):
            import_export_service.import_from(str(no_comments_file))

        # Test tasks not a list
        bad_tasks_file = temp_dir / "bad_tasks.json"
        bad_tasks_file.write_text(json.dumps({"tasks": {}, "comments": []}))

        with pytest.raises(ValueError, match="'tasks' must be an array"):
            import_export_service.import_from(str(bad_tasks_file))

        # Test comments not a list
        bad_comments_file = temp_dir / "bad_comments.json"
        bad_comments_file.write_text(json.dumps({"tasks": [], "comments": {}}))

        with pytest.raises(ValueError, match="'comments' must be an array"):
            import_export_service.import_from(str(bad_comments_file))

        # Test root not an object
        not_object_file = temp_dir / "not_object.json"
        not_object_file.write_text(json.dumps([]))

        with pytest.raises(ValueError, match="JSON root must be an object"):
            import_export_service.import_from(str(not_object_file))

    def test_import_skips_duplicates(self, import_export_service, services, temp_dir):
        """Test that import skips tasks and comments that already exist by ID."""
        todo_service, comments_service = services

        # Create original task and comment
        original_task = todo_service.add_task("Original Title")
        original_comment = comments_service.add_comment(original_task.id, "Original content")

        # Modify the task to have different data
        todo_service.update_task(original_task.id, title="Updated Title")
        updated_task = todo_service.get_task(original_task.id)
        assert updated_task.title == "Updated Title"

        # Create an export file with the original task data (modified in memory)
        export_data = {
            "tasks": [
                {
                    "id": original_task.id,
                    "title": "Different Title",  # Different from current state
                    "description": None,
                    "status": TaskStatus.DONE.value,  # Different status
                    "created_at": original_task.created_at.isoformat(),
                    "updated_at": original_task.updated_at.isoformat(),
                }
            ],
            "comments": [
                {
                    "id": original_comment.id,
                    "task_id": original_task.id,
                    "content": "Different content",  # Different content
                    "created_at": original_comment.created_at.isoformat(),
                    "author": None,
                }
            ],
        }
        export_file = temp_dir / "export.json"
        with open(export_file, "w") as f:
            json.dump(export_data, f)

        # Import from file
        imported_tasks, imported_comments = import_export_service.import_from(str(export_file))

        # Verify duplicates were skipped
        assert imported_tasks == []
        assert imported_comments == []

        # Verify existing data was not modified
        current_task = todo_service.get_task(original_task.id)
        assert current_task.title == "Updated Title"
        assert current_task.status == TaskStatus.PENDING

        current_comments = comments_service.list_comments(original_task.id)
        assert len(current_comments) == 1
        assert current_comments[0].content == "Original content"

    def test_import_skips_comments_for_missing_tasks(self, import_export_service, temp_dir):
        """Test that import silently skips comments referencing non-existent tasks."""
        # Create an export file with tasks and orphaned comments
        task_id = "task-123"
        missing_task_id = "missing-456"

        export_data = {
            "tasks": [
                {
                    "id": task_id,
                    "title": "Test Task",
                    "description": None,
                    "status": TaskStatus.PENDING.value,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            ],
            "comments": [
                {
                    "id": "comment-1",
                    "task_id": task_id,
                    "content": "Valid comment",
                    "created_at": datetime.now(CEST).isoformat(),
                    "author": None,
                },
                {
                    "id": "comment-2",
                    "task_id": missing_task_id,
                    "content": "Orphaned comment",
                    "created_at": datetime.now(CEST).isoformat(),
                    "author": None,
                },
            ],
        }
        export_file = temp_dir / "export.json"
        with open(export_file, "w") as f:
            json.dump(export_data, f)

        # Import
        imported_tasks, imported_comments = import_export_service.import_from(str(export_file))

        # Verify only the task was imported
        assert len(imported_tasks) == 1

        # Verify only the valid comment was imported (orphaned one skipped)
        assert len(imported_comments) == 1
        assert imported_comments[0].task_id == task_id

    def test_import_skips_malformed_entries(self, import_export_service, temp_dir):
        """Test that import gracefully skips malformed task and comment entries."""
        export_data = {
            "tasks": [
                {
                    "id": "valid-task-1",
                    "title": "Valid Task",
                    "description": None,
                    "status": TaskStatus.PENDING.value,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                {
                    # Missing required 'title' field
                    "id": "bad-task-1",
                    "description": None,
                    "status": TaskStatus.PENDING.value,
                },
                {
                    # Invalid status value
                    "id": "bad-task-2",
                    "title": "Bad Task",
                    "description": None,
                    "status": "INVALID_STATUS",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            ],
            "comments": [
                {
                    "id": "valid-comment-1",
                    "task_id": "valid-task-1",
                    "content": "Valid comment",
                    "created_at": datetime.now(CEST).isoformat(),
                    "author": None,
                },
                {
                    # Missing required 'content' field
                    "id": "bad-comment-1",
                    "task_id": "valid-task-1",
                    "created_at": datetime.now(CEST).isoformat(),
                    "author": None,
                },
                {
                    # Missing required 'task_id' field
                    "id": "bad-comment-2",
                    "content": "No task reference",
                    "created_at": datetime.now(CEST).isoformat(),
                    "author": None,
                },
            ],
        }
        export_file = temp_dir / "export.json"
        with open(export_file, "w") as f:
            json.dump(export_data, f)

        # Import
        imported_tasks, imported_comments = import_export_service.import_from(str(export_file))

        # Verify only valid entries were imported
        assert len(imported_tasks) == 1
        assert imported_tasks[0].id == "valid-task-1"

        assert len(imported_comments) == 1
        assert imported_comments[0].id == "valid-comment-1"

    def test_import_file_not_found(self, import_export_service):
        """Test that import raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            import_export_service.import_from("/nonexistent/path/to/file.json")

    def test_import_with_mixed_valid_and_invalid_entries(self, import_export_service, temp_dir):
        """Test import with a realistic mix of valid and invalid entries."""
        export_data = {
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Task 1",
                    "description": "Description 1",
                    "status": TaskStatus.PENDING.value,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "id": "task-2",
                    "title": "Task 2",
                    "status": TaskStatus.IN_PROGRESS.value,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            ],
            "comments": [
                {
                    "id": "comment-1",
                    "task_id": "task-1",
                    "content": "Comment on task 1",
                    "created_at": datetime.now(CEST).isoformat(),
                    "author": "User1",
                },
                {
                    "id": "comment-2",
                    "task_id": "task-2",
                    "content": "Comment on task 2",
                    "created_at": datetime.now(CEST).isoformat(),
                    "author": None,
                },
            ],
        }
        export_file = temp_dir / "export.json"
        with open(export_file, "w") as f:
            json.dump(export_data, f)

        # Import
        imported_tasks, imported_comments = import_export_service.import_from(str(export_file))

        # Verify all valid entries were imported
        assert len(imported_tasks) == 2
        assert len(imported_comments) == 2

        task_ids = {t.id for t in imported_tasks}
        assert "task-1" in task_ids
        assert "task-2" in task_ids

        comment_ids = {c.id for c in imported_comments}
        assert "comment-1" in comment_ids
        assert "comment-2" in comment_ids


class TestRoundTrip:
    """Tests for round-trip export/import cycles."""

    def test_roundtrip_preserves_task_data(self, import_export_service, services, temp_dir):
        """Test that task data is preserved through an export/import cycle."""
        todo_service1, _ = services

        # Create a task with various fields
        due_date = datetime(2025, 6, 15, 14, 30, tzinfo=CEST)
        original_task = todo_service1.add_task("Test Task", "Test description", due_date)
        todo_service1.start_task(original_task.id)

        # Export
        export_file = temp_dir / "export.json"
        import_export_service.export(str(export_file))

        # Create new services and import
        storage2 = JsonStorage(temp_dir / "data2.json")
        todo_service2 = TodoService(storage2)
        comments_service2 = CommentsService(todo_service2, storage2)
        import_export_service2 = TaskImportExportService(todo_service2, comments_service2)

        imported_tasks, _ = import_export_service2.import_from(str(export_file))

        # Verify all fields match
        imported_task = imported_tasks[0]
        assert imported_task.id == original_task.id
        assert imported_task.title == original_task.title
        assert imported_task.description == original_task.description
        assert imported_task.status == TaskStatus.IN_PROGRESS
        assert imported_task.due_date == due_date

    def test_roundtrip_preserves_comments(self, import_export_service, services, temp_dir):
        """Test that comments are preserved through an export/import cycle."""
        todo_service1, comments_service1 = services

        # Create task and comments
        task = todo_service1.add_task("Task")
        comment1 = comments_service1.add_comment(task.id, "First comment")
        comment1_text = comment1.content

        # Export
        export_file = temp_dir / "export.json"
        import_export_service.export(str(export_file))

        # Create new services and import
        storage2 = JsonStorage(temp_dir / "data2.json")
        todo_service2 = TodoService(storage2)
        comments_service2 = CommentsService(todo_service2, storage2)
        import_export_service2 = TaskImportExportService(todo_service2, comments_service2)

        _, imported_comments = import_export_service2.import_from(str(export_file))

        # Verify comment content
        assert len(imported_comments) == 1
        assert imported_comments[0].content == comment1_text
        assert imported_comments[0].id == comment1.id
