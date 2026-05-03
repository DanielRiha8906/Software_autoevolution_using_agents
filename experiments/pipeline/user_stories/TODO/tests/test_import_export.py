"""Comprehensive tests for export and import functionality at the service layer."""

import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from src.models.task_status import TaskStatus
from src.models.task import Task
from src.models.task_comment import TaskComment
from src.services.todo_service import TodoService
from src.services.import_validator import ImportValidator
from src.storage.json_storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    """Service with isolated storage."""
    return TodoService(JsonStorage(str(tmp_path / "tasks.json")))


@pytest.fixture
def temp_export_file(tmp_path):
    """Temporary export file path."""
    return str(tmp_path / "export.json")


@pytest.fixture
def sample_tasks(service):
    """Create sample tasks with various attributes."""
    t1 = service.add_task("Buy groceries", description="Milk, eggs, bread")
    t2 = service.add_task("Write report")
    t3 = service.add_task(
        "Project deadline",
        description="Q3 planning",
        due_date=datetime(2026, 6, 30, 17, 0, tzinfo=timezone.utc)
    )
    service.start_task(t1.id)
    service.start_task(t3.id)
    service.complete_task(t1.id)

    # Add comment to first task
    service.add_comment(t1.id, "Urgent - needed for dinner party")

    return [t1, t2, t3]


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestExportBasics:
    """Test basic export functionality."""

    def test_export_empty_task_list(self, service, temp_export_file):
        """Export empty task list produces file with empty array."""
        count = service.export_tasks(temp_export_file)
        assert count == 0

        with open(temp_export_file) as f:
            data = json.load(f)
        assert data == []

    def test_export_single_task(self, service, temp_export_file):
        """Export single task produces correct JSON structure."""
        task = service.add_task("Test task")
        count = service.export_tasks(temp_export_file)
        assert count == 1

        with open(temp_export_file) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["id"] == task.id
        assert data[0]["title"] == "Test task"

    def test_export_multiple_tasks(self, service, temp_export_file, sample_tasks):
        """Export multiple tasks with all attributes."""
        count = service.export_tasks(temp_export_file)
        assert count == 3

        with open(temp_export_file) as f:
            data = json.load(f)

        assert len(data) == 3
        titles = {task["title"] for task in data}
        assert titles == {"Buy groceries", "Write report", "Project deadline"}

    def test_export_returns_count(self, service, temp_export_file):
        """Export returns correct task count."""
        service.add_task("A")
        service.add_task("B")
        service.add_task("C")
        count = service.export_tasks(temp_export_file)
        assert count == 3

    def test_export_with_none_description(self, service, temp_export_file):
        """Export task with None description includes null in JSON."""
        task = service.add_task("No description")
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            data = json.load(f)
        assert data[0]["description"] is None

    def test_export_creates_parent_directories(self, tmp_path):
        """Export creates parent directories if they don't exist."""
        service = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
        service.add_task("Test")

        nested_path = str(tmp_path / "deep" / "nested" / "export.json")
        count = service.export_tasks(nested_path)
        assert count == 1
        assert Path(nested_path).exists()

    def test_export_overwrites_existing_file(self, service, temp_export_file):
        """Export overwrites existing file."""
        service.add_task("Task 1")
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            initial_data = json.load(f)
        assert len(initial_data) == 1

        # Clear service and add different tasks
        service._manager._tasks.clear()
        service.add_task("Task 2")
        service.add_task("Task 3")
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            new_data = json.load(f)
        assert len(new_data) == 2
        titles = {task["title"] for task in new_data}
        assert titles == {"Task 2", "Task 3"}

    def test_export_default_path(self, service, monkeypatch):
        """Export without file_path uses default location."""
        service.add_task("Default test")

        default_path = Path.home() / ".todo_export.json"
        count = service.export_tasks(None)
        assert count == 1

        # Verify file was created
        assert default_path.exists()
        with open(default_path) as f:
            data = json.load(f)
        assert len(data) == 1

        # Cleanup
        default_path.unlink()


class TestExportStructure:
    """Test exported JSON structure and field preservation."""

    def test_exported_task_has_all_required_fields(self, service, temp_export_file):
        """Exported task includes all required fields."""
        task = service.add_task(
            "Full task",
            description="With description",
            due_date=datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc)
        )
        service.start_task(task.id)
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            data = json.load(f)

        exported = data[0]
        required_fields = ["id", "title", "status", "created_at", "updated_at"]
        for field in required_fields:
            assert field in exported

    def test_exported_status_is_string(self, service, temp_export_file):
        """Exported status is string, not enum."""
        task = service.add_task("Status test")
        service.start_task(task.id)
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            data = json.load(f)

        assert isinstance(data[0]["status"], str)
        assert data[0]["status"] == "in_progress"

    def test_exported_dates_are_iso_format(self, service, temp_export_file):
        """Exported dates are in ISO 8601 format."""
        task = service.add_task("Date test")
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            data = json.load(f)

        # Should not raise ValueError
        datetime.fromisoformat(data[0]["created_at"])
        datetime.fromisoformat(data[0]["updated_at"])

    def test_exported_due_date_null_when_not_set(self, service, temp_export_file):
        """Exported due_date is null when not set."""
        task = service.add_task("No due date")
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            data = json.load(f)

        assert data[0]["due_date"] is None

    def test_exported_due_date_iso_format_when_set(self, service, temp_export_file):
        """Exported due_date is ISO format when set."""
        dt = datetime(2026, 6, 15, 14, 30, tzinfo=timezone.utc)
        task = service.add_task("With due date", due_date=dt)
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            data = json.load(f)

        exported_dt = datetime.fromisoformat(data[0]["due_date"])
        assert exported_dt == dt

    def test_exported_task_with_comments(self, service, temp_export_file):
        """Exported task includes comments array."""
        task = service.add_task("With comments")
        comment = service.add_comment(task.id, "Great progress!")
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            data = json.load(f)

        exported = data[0]
        assert "comments" in exported
        assert isinstance(exported["comments"], list)
        assert len(exported["comments"]) == 1
        assert exported["comments"][0]["content"] == "Great progress!"

    def test_exported_empty_comments_array_when_no_comments(self, service, temp_export_file):
        """Exported task has empty comments array when no comments."""
        task = service.add_task("No comments")
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            data = json.load(f)

        assert data[0]["comments"] == []

    def test_exported_comment_has_all_fields(self, service, temp_export_file):
        """Exported comment includes all required fields."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Test comment", author="Alice")
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            data = json.load(f)

        exported_comment = data[0]["comments"][0]
        assert "id" in exported_comment
        assert "task_id" in exported_comment
        assert "content" in exported_comment
        assert "author" in exported_comment
        assert "created_at" in exported_comment
        assert exported_comment["author"] == "Alice"


# ─────────────────────────────────────────────────────────────────────────────
# IMPORT TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestImportBasics:
    """Test basic import functionality."""

    def test_import_valid_json_array(self, service, tmp_path):
        """Import valid JSON array imports all tasks."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "task-1",
                "title": "Imported task",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 1
        assert result["skipped_count"] == 0
        assert result["errors"] == []

        # Verify task was added
        tasks = service.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "Imported task"

    def test_import_empty_array(self, service, tmp_path):
        """Import empty array results in 0 imported, 0 errors."""
        import_file = tmp_path / "import.json"

        with open(import_file, "w") as f:
            json.dump([], f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 0
        assert result["skipped_count"] == 0
        assert result["errors"] == []

    def test_import_nonexistent_file(self, service, tmp_path):
        """Import nonexistent file returns file not found error."""
        nonexistent = str(tmp_path / "missing.json")

        result = service.import_tasks(nonexistent)
        assert result["imported_count"] == 0
        assert len(result["errors"]) == 1
        assert "File not found" in result["errors"][0]["error"]

    def test_import_invalid_json(self, service, tmp_path):
        """Import invalid JSON returns JSON syntax error."""
        import_file = tmp_path / "invalid.json"

        with open(import_file, "w") as f:
            f.write("{invalid json syntax}")

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 0
        assert len(result["errors"]) == 1
        assert "Invalid JSON" in result["errors"][0]["error"]

    def test_import_non_array_json(self, service, tmp_path):
        """Import non-array JSON returns array required error."""
        import_file = tmp_path / "not_array.json"

        with open(import_file, "w") as f:
            json.dump({"task": "single"}, f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 0
        assert len(result["errors"]) == 1
        assert "array" in result["errors"][0]["error"].lower()

    def test_import_empty_file(self, service, tmp_path):
        """Import empty file returns empty file error."""
        import_file = tmp_path / "empty.json"
        import_file.write_text("")

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 0
        assert len(result["errors"]) == 1
        assert "empty" in result["errors"][0]["error"].lower()


class TestImportValidation:
    """Test import validation of task fields."""

    def test_import_missing_required_field_id(self, service, tmp_path):
        """Import task missing id field collects error."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "title": "No ID",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 0
        assert len(result["errors"]) == 1
        assert "id" in result["errors"][0]["error"].lower()

    def test_import_missing_required_field_title(self, service, tmp_path):
        """Import task missing title field collects error."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "task-1",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 0
        assert len(result["errors"]) == 1

    def test_import_invalid_status_enum(self, service, tmp_path):
        """Import task with invalid status collects error."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "task-1",
                "title": "Bad status",
                "status": "invalid_status",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 0
        assert len(result["errors"]) == 1
        assert "status" in result["errors"][0]["error"].lower()

    def test_import_invalid_created_at_datetime(self, service, tmp_path):
        """Import task with invalid created_at collects error."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "task-1",
                "title": "Bad date",
                "status": "pending",
                "created_at": "not-a-date",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 0
        assert len(result["errors"]) == 1
        assert "created_at" in result["errors"][0]["error"]

    def test_import_invalid_due_date_datetime(self, service, tmp_path):
        """Import task with invalid due_date collects error."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "task-1",
                "title": "Bad due date",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": "not-a-date",
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 0
        assert len(result["errors"]) == 1
        assert "due_date" in result["errors"][0]["error"]

    def test_import_mixed_valid_invalid_entries(self, service, tmp_path):
        """Import with both valid and invalid entries imports valid ones."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "valid-1",
                "title": "Valid task",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            },
            {
                "id": "invalid-1",
                "title": "Invalid",
                "status": "bad_status",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            },
            {
                "id": "valid-2",
                "title": "Another valid",
                "status": "done",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 2
        assert result["skipped_count"] == 0
        assert len(result["errors"]) == 1

        # Verify valid tasks were imported
        tasks = service.list_tasks()
        assert len(tasks) == 2
        titles = {t.title for t in tasks}
        assert titles == {"Valid task", "Another valid"}


class TestImportDuplicateHandling:
    """Test duplicate task ID handling strategies."""

    def test_import_duplicate_skip_strategy(self, service, tmp_path):
        """Import with skip strategy keeps existing task."""
        # Add existing task
        existing = service.add_task("Original task")
        assert existing.title == "Original task"

        # Import file with duplicate ID but different title
        import_file = tmp_path / "import.json"
        data = [
            {
                "id": existing.id,
                "title": "Imported title",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file), duplicate_strategy="skip")
        assert result["imported_count"] == 0
        assert result["skipped_count"] == 1

        # Verify original task is unchanged
        task = service.get_task(existing.id)
        assert task.title == "Original task"

    def test_import_duplicate_replace_strategy(self, service, tmp_path):
        """Import with replace strategy overwrites existing task."""
        # Add existing task
        existing = service.add_task("Original task")

        # Import file with duplicate ID and different title
        import_file = tmp_path / "import.json"
        data = [
            {
                "id": existing.id,
                "title": "Replaced title",
                "status": "done",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": "New description",
                "due_date": None,
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file), duplicate_strategy="replace")
        assert result["imported_count"] == 0
        assert result["skipped_count"] == 1

        # Verify task was replaced
        task = service.get_task(existing.id)
        assert task.title == "Replaced title"
        assert task.status == TaskStatus.DONE
        assert task.description == "New description"

    def test_import_invalid_strategy_raises(self, service, tmp_path):
        """Import with invalid strategy raises ValueError."""
        import_file = tmp_path / "import.json"
        with open(import_file, "w") as f:
            json.dump([], f)

        with pytest.raises(ValueError, match="duplicate_strategy"):
            service.import_tasks(str(import_file), duplicate_strategy="invalid")

    def test_import_duplicate_in_file_ignored(self, service, tmp_path):
        """Import with duplicate IDs within file ignores duplicates."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "task-1",
                "title": "First",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            },
            {
                "id": "task-1",
                "title": "Duplicate",
                "status": "done",
                "created_at": "2026-05-02T10:00:00+00:00",
                "updated_at": "2026-05-02T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 1
        assert len(result["errors"]) == 1
        assert "duplicate" in result["errors"][0]["error"].lower()


class TestImportRoundTrip:
    """Test export then import preserves data."""

    def test_export_import_roundtrip_single_task(self, service, tmp_path):
        """Export and import single task preserves all data."""
        original = service.add_task(
            "Test task",
            description="Test description",
            due_date=datetime(2026, 6, 15, 14, 30, tzinfo=timezone.utc)
        )
        service.start_task(original.id)

        # Export
        export_file = tmp_path / "export.json"
        service.export_tasks(str(export_file))

        # Create new service with empty storage
        service2 = TodoService(JsonStorage(str(tmp_path / "tasks2.json")))

        # Import
        result = service2.import_tasks(str(export_file))
        assert result["imported_count"] == 1
        assert result["errors"] == []

        # Verify
        imported = service2.get_task(original.id)
        assert imported.id == original.id
        assert imported.title == original.title
        assert imported.description == original.description
        assert imported.status == original.status
        assert imported.due_date == original.due_date

    def test_export_import_roundtrip_with_comments(self, service, tmp_path):
        """Export and import preserves comments."""
        task = service.add_task("Task with comments")
        comment1 = service.add_comment(task.id, "First comment", author="Alice")
        comment2 = service.add_comment(task.id, "Second comment", author="Bob")

        # Export
        export_file = tmp_path / "export.json"
        service.export_tasks(str(export_file))

        # Create new service
        service2 = TodoService(JsonStorage(str(tmp_path / "tasks2.json")))

        # Import
        result = service2.import_tasks(str(export_file))
        assert result["imported_count"] == 1

        # Verify
        imported_task = service2.get_task(task.id)
        imported_comments = service2.get_comments(task.id)
        assert len(imported_comments) == 2

        comment_contents = {c.content for c in imported_comments}
        assert comment_contents == {"First comment", "Second comment"}

    def test_export_import_multiple_tasks_all_statuses(self, service, tmp_path):
        """Export and import tasks with different statuses."""
        t1 = service.add_task("Task 1 - Pending")
        t2 = service.add_task("Task 2 - Done")
        t3 = service.add_task("Task 3 - Done")

        service.start_task(t2.id)
        service.complete_task(t2.id)
        service.start_task(t3.id)
        service.complete_task(t3.id)

        # Export
        export_file = tmp_path / "export.json"
        service.export_tasks(str(export_file))

        # Create new service
        service2 = TodoService(JsonStorage(str(tmp_path / "tasks2.json")))

        # Import
        result = service2.import_tasks(str(export_file))
        assert result["imported_count"] == 3

        # Verify statuses
        pending = service2.list_tasks(status=TaskStatus.PENDING)
        done = service2.list_tasks(status=TaskStatus.DONE)

        assert len(pending) == 1
        assert pending[0].title == "Task 1 - Pending"
        assert len(done) == 2
        done_titles = {t.title for t in done}
        assert done_titles == {"Task 2 - Done", "Task 3 - Done"}


class TestImportValidatorDirectly:
    """Test ImportValidator class directly."""

    def test_validator_validate_file_valid(self, tmp_path):
        """Validator processes valid file."""
        import_file = tmp_path / "import.json"
        data = [
            {
                "id": "task-1",
                "title": "Valid",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]
        with open(import_file, "w") as f:
            json.dump(data, f)

        validator = ImportValidator()
        tasks, errors = validator.validate_file(str(import_file))

        assert len(tasks) == 1
        assert errors == []
        assert tasks[0]["id"] == "task-1"

    def test_validator_validate_task_dict_missing_field(self):
        """Validator detects missing required field."""
        validator = ImportValidator()
        task_dict = {
            "id": "task-1",
            "status": "pending",
            # missing title
            "created_at": "2026-05-01T10:00:00+00:00",
            "updated_at": "2026-05-01T10:00:00+00:00",
        }

        error = validator.validate_task_dict(task_dict, 0)
        assert error is not None
        assert "title" in error.lower()

    def test_validator_validate_comment_missing_required_field(self):
        """Validator detects missing comment required field."""
        validator = ImportValidator()
        task_dict = {
            "id": "task-1",
            "title": "Task",
            "status": "pending",
            "created_at": "2026-05-01T10:00:00+00:00",
            "updated_at": "2026-05-01T10:00:00+00:00",
            "comments": [
                {
                    "id": "comment-1",
                    "task_id": "task-1",
                    # missing content
                    "created_at": "2026-05-01T10:00:00+00:00"
                }
            ]
        }

        error = validator.validate_task_dict(task_dict, 0)
        assert error is not None
        assert "comment" in error.lower()

    def test_validator_filters_empty_comments(self):
        """Validator allows task but skips empty comments."""
        validator = ImportValidator()
        task_dict = {
            "id": "task-1",
            "title": "Task",
            "status": "pending",
            "created_at": "2026-05-01T10:00:00+00:00",
            "updated_at": "2026-05-01T10:00:00+00:00",
            "comments": [
                {
                    "id": "comment-1",
                    "task_id": "task-1",
                    "content": "   ",  # whitespace only
                    "created_at": "2026-05-01T10:00:00+00:00"
                }
            ]
        }

        error = validator.validate_task_dict(task_dict, 0)
        # Should not error out - empty comments are filtered, not rejected
        assert error is None


class TestImportCommentHandling:
    """Test comment handling during import."""

    def test_import_task_with_valid_comment(self, service, tmp_path):
        """Import task with valid comment."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "task-1",
                "title": "Task",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": [
                    {
                        "id": "comment-1",
                        "task_id": "task-1",
                        "content": "Great work",
                        "author": "Alice",
                        "created_at": "2026-05-01T11:00:00+00:00",
                        "updated_at": None
                    }
                ]
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 1

        comments = service.get_comments("task-1")
        assert len(comments) == 1
        assert comments[0].content == "Great work"
        assert comments[0].author == "Alice"

    def test_import_filters_empty_comments(self, service, tmp_path):
        """Import filters out empty comments but keeps task."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "task-1",
                "title": "Task",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": [
                    {
                        "id": "comment-1",
                        "task_id": "task-1",
                        "content": "Good comment",
                        "author": None,
                        "created_at": "2026-05-01T11:00:00+00:00",
                        "updated_at": None
                    },
                    {
                        "id": "comment-2",
                        "task_id": "task-1",
                        "content": "   ",  # whitespace only
                        "author": None,
                        "created_at": "2026-05-01T12:00:00+00:00",
                        "updated_at": None
                    }
                ]
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 1

        comments = service.get_comments("task-1")
        assert len(comments) == 1
        assert comments[0].content == "Good comment"


# ─────────────────────────────────────────────────────────────────────────────
# EDGE CASES
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_export_with_special_characters_in_description(self, service, temp_export_file):
        """Export handles special characters correctly."""
        task = service.add_task("Task", description="Quote: \"Hello\" & friends <tag>")
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            data = json.load(f)

        assert data[0]["description"] == 'Quote: "Hello" & friends <tag>'

    def test_export_with_unicode_characters(self, service, temp_export_file):
        """Export preserves unicode characters."""
        task = service.add_task("Task", description="Japanese: 日本語, Emoji: 🎉")
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            data = json.load(f)

        assert "日本語" in data[0]["description"]
        assert "🎉" in data[0]["description"]

    def test_export_with_newlines_in_description(self, service, temp_export_file):
        """Export preserves newlines in description."""
        task = service.add_task("Task", description="Line 1\nLine 2\nLine 3")
        service.export_tasks(temp_export_file)

        with open(temp_export_file) as f:
            data = json.load(f)

        assert "\n" in data[0]["description"]

    def test_import_preserves_timezone_in_dates(self, service, tmp_path):
        """Import preserves timezone information in dates."""
        import_file = tmp_path / "import.json"

        # ISO format with specific timezone
        data = [
            {
                "id": "task-1",
                "title": "Task",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+05:30",
                "updated_at": "2026-05-01T10:00:00+05:30",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        task = service.get_task("task-1")

        # Verify timezone is preserved (though may be converted to UTC internally)
        assert task.created_at.tzinfo is not None

    def test_export_large_number_of_tasks(self, service, temp_export_file):
        """Export handles large number of tasks efficiently."""
        for i in range(100):
            service.add_task(f"Task {i}", description=f"Description {i}")

        count = service.export_tasks(temp_export_file)
        assert count == 100

        with open(temp_export_file) as f:
            data = json.load(f)

        assert len(data) == 100

    def test_import_preserves_task_id_format(self, service, tmp_path):
        """Import preserves task ID exactly as provided."""
        import_file = tmp_path / "import.json"

        # Use various ID formats
        data = [
            {
                "id": "simple-id",
                "title": "Task 1",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Task 2",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 2

        t1 = service.get_task("simple-id")
        t2 = service.get_task("550e8400-e29b-41d4-a716-446655440000")
        assert t1.id == "simple-id"
        assert t2.id == "550e8400-e29b-41d4-a716-446655440000"

    def test_export_file_is_valid_json(self, service, temp_export_file):
        """Exported file is always valid JSON."""
        service.add_task("A")
        service.add_task("B")

        service.export_tasks(temp_export_file)

        # Should not raise
        with open(temp_export_file) as f:
            data = json.load(f)
        assert isinstance(data, list)

    def test_import_task_dict_with_null_optional_fields(self, service, tmp_path):
        """Import succeeds when comments is null, treating it as empty list."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "task-1",
                "title": "Task",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": None
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        # Task.from_dict now correctly handles None comments using data.get("comments") or []
        assert result["imported_count"] == 1
        assert result["errors"] == []

        # Verify task was imported with empty comments list
        task = service.get_task("task-1")
        assert task.title == "Task"
        assert task.comments == []

    def test_non_dict_entry_in_array_collects_error(self, service, tmp_path):
        """Import collects error for non-dict entries in array."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "task-1",
                "title": "Valid",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            },
            "not a dict",
            {
                "id": "task-2",
                "title": "Also valid",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        result = service.import_tasks(str(import_file))
        assert result["imported_count"] == 2
        assert len(result["errors"]) == 1
        assert "object" in result["errors"][0]["error"].lower()
