"""Tests for import/export functionality."""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.models.task import Task
from src.models.task_comment import TaskComment
from src.models.task_status import TaskStatus
from src.services.import_export_service import ImportExportService, ImportExportValidationError
from src.storage.json_storage import JsonStorage


@pytest.fixture
def storage(tmp_path):
    """Create a temporary storage for each test."""
    return JsonStorage(str(tmp_path / "test_data.json"))


@pytest.fixture
def service(storage):
    """Create an ImportExportService with temporary storage."""
    return ImportExportService(storage)


class TestExport:
    """Tests for export functionality."""

    def test_export_empty_data(self, service, tmp_path):
        """Test exporting when no tasks exist."""
        export_path = str(tmp_path / "export.json")
        result = service.export_to_file(export_path)

        assert Path(export_path).exists()
        assert result["tasks"] == []
        assert result["comments"] == []

    def test_export_with_tasks(self, service, tmp_path, storage):
        """Test exporting tasks."""
        # Add tasks to storage
        task_data = {
            "id": "task-1",
            "title": "Test Task",
            "description": "Test description",
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        storage.save({"tasks": [task_data], "comments": []})

        export_path = str(tmp_path / "export.json")
        result = service.export_to_file(export_path)

        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["id"] == "task-1"
        assert result["tasks"][0]["title"] == "Test Task"

    def test_export_with_tasks_and_comments(self, service, tmp_path, storage):
        """Test exporting tasks with comments."""
        now = datetime.now(timezone.utc)
        task_data = {
            "id": "task-1",
            "title": "Test Task",
            "status": "pending",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        comment_data = {
            "id": "comment-1",
            "task_id": "task-1",
            "content": "Test comment",
            "created_at": now.isoformat(),
            "author": "Test Author",
        }
        storage.save({"tasks": [task_data], "comments": [comment_data]})

        export_path = str(tmp_path / "export.json")
        result = service.export_to_file(export_path)

        assert len(result["tasks"]) == 1
        assert len(result["comments"]) == 1
        assert result["comments"][0]["task_id"] == "task-1"

    def test_export_creates_directories(self, service, tmp_path):
        """Test that export creates necessary directories."""
        export_path = str(tmp_path / "nested" / "dir" / "export.json")
        service.export_to_file(export_path)

        assert Path(export_path).exists()

    def test_export_file_is_valid_json(self, service, tmp_path, storage):
        """Test that exported file is valid JSON."""
        task_data = {
            "id": "task-1",
            "title": "Test Task",
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        storage.save({"tasks": [task_data], "comments": []})

        export_path = str(tmp_path / "export.json")
        service.export_to_file(export_path)

        with open(export_path) as f:
            data = json.load(f)

        assert "tasks" in data
        assert "comments" in data


class TestImportValidation:
    """Tests for import data validation."""

    def test_validate_invalid_root_type(self, service):
        """Test validation rejects non-dict root."""
        is_valid, error = service.validate_import_data([])
        assert not is_valid
        assert "JSON object" in error

    def test_validate_invalid_tasks_type(self, service):
        """Test validation rejects non-list tasks."""
        is_valid, error = service.validate_import_data({"tasks": "invalid"})
        assert not is_valid
        assert "list" in error

    def test_validate_invalid_comments_type(self, service):
        """Test validation rejects non-list comments."""
        is_valid, error = service.validate_import_data({"comments": "invalid"})
        assert not is_valid
        assert "list" in error

    def test_validate_task_missing_required_field(self, service):
        """Test validation rejects tasks with missing required fields."""
        is_valid, error = service.validate_import_data({
            "tasks": [{"id": "1", "title": "Test"}],
            "comments": []
        })
        assert not is_valid
        assert "required fields" in error.lower()

    def test_validate_comment_missing_required_field(self, service):
        """Test validation rejects comments with missing required fields."""
        is_valid, error = service.validate_import_data({
            "tasks": [],
            "comments": [{"id": "1"}]
        })
        assert not is_valid
        assert "required fields" in error.lower()

    def test_validate_invalid_status(self, service):
        """Test validation rejects invalid task status."""
        is_valid, error = service.validate_import_data({
            "tasks": [{
                "id": "1",
                "title": "Test",
                "status": "invalid_status",
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T00:00:00+00:00"
            }],
            "comments": []
        })
        assert not is_valid
        assert "invalid status" in error.lower()

    def test_validate_valid_data(self, service):
        """Test validation accepts valid data."""
        now = datetime.now(timezone.utc).isoformat()
        is_valid, error = service.validate_import_data({
            "tasks": [{
                "id": "task-1",
                "title": "Test Task",
                "status": "pending",
                "created_at": now,
                "updated_at": now
            }],
            "comments": [{
                "id": "comment-1",
                "task_id": "task-1",
                "content": "Test comment",
                "created_at": now
            }]
        })
        assert is_valid
        assert error == ""


class TestImport:
    """Tests for import functionality."""

    def test_import_file_not_found(self, service):
        """Test import raises error for missing file."""
        with pytest.raises(FileNotFoundError):
            service.import_from_file("/nonexistent/path.json")

    def test_import_invalid_json(self, service, tmp_path):
        """Test import raises error for invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json")

        with pytest.raises(ValueError):
            service.import_from_file(str(invalid_file))

    def test_import_invalid_structure(self, service, tmp_path):
        """Test import raises error for invalid structure."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text('{"tasks": "not a list"}')

        with pytest.raises(ImportExportValidationError):
            service.import_from_file(str(invalid_file))

    def test_import_empty_data(self, service, tmp_path, storage):
        """Test importing empty data."""
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps({"tasks": [], "comments": []}))

        result = service.import_from_file(str(import_file))

        assert result["added_tasks"] == []
        assert result["added_comments"] == []
        assert result["skipped_tasks"] == []
        assert result["skipped_comments"] == []

    def test_import_new_tasks(self, service, tmp_path):
        """Test importing new tasks."""
        now = datetime.now(timezone.utc).isoformat()
        import_file = tmp_path / "import.json"
        import_data = {
            "tasks": [{
                "id": "task-1",
                "title": "Imported Task",
                "description": "Description",
                "status": "pending",
                "created_at": now,
                "updated_at": now
            }],
            "comments": []
        }
        import_file.write_text(json.dumps(import_data))

        result = service.import_from_file(str(import_file))

        assert len(result["added_tasks"]) == 1
        assert "task-1" in result["added_tasks"]
        assert result["skipped_tasks"] == []

    def test_import_new_comments(self, service, tmp_path):
        """Test importing new comments."""
        now = datetime.now(timezone.utc).isoformat()
        import_file = tmp_path / "import.json"
        import_data = {
            "tasks": [],
            "comments": [{
                "id": "comment-1",
                "task_id": "task-1",
                "content": "Imported comment",
                "created_at": now,
                "author": "Importer"
            }]
        }
        import_file.write_text(json.dumps(import_data))

        result = service.import_from_file(str(import_file))

        assert len(result["added_comments"]) == 1
        assert "comment-1" in result["added_comments"]
        assert result["skipped_comments"] == []

    def test_import_skip_duplicates_by_default(self, service, tmp_path, storage):
        """Test that duplicates are skipped by default."""
        now = datetime.now(timezone.utc).isoformat()
        existing_task = {
            "id": "task-1",
            "title": "Existing Task",
            "status": "pending",
            "created_at": now,
            "updated_at": now
        }
        storage.save({"tasks": [existing_task], "comments": []})

        import_file = tmp_path / "import.json"
        import_data = {
            "tasks": [{
                "id": "task-1",
                "title": "Different Title",
                "status": "done",
                "created_at": now,
                "updated_at": now
            }],
            "comments": []
        }
        import_file.write_text(json.dumps(import_data))

        result = service.import_from_file(str(import_file), overwrite=False)

        assert result["added_tasks"] == []
        assert "task-1" in result["skipped_tasks"]

    def test_import_overwrite_existing(self, service, tmp_path, storage):
        """Test overwriting existing items."""
        now = datetime.now(timezone.utc).isoformat()
        existing_task = {
            "id": "task-1",
            "title": "Old Title",
            "status": "pending",
            "created_at": now,
            "updated_at": now
        }
        storage.save({"tasks": [existing_task], "comments": []})

        import_file = tmp_path / "import.json"
        import_data = {
            "tasks": [{
                "id": "task-1",
                "title": "New Title",
                "status": "done",
                "created_at": now,
                "updated_at": now
            }],
            "comments": []
        }
        import_file.write_text(json.dumps(import_data))

        result = service.import_from_file(str(import_file), overwrite=True)

        # Task should be updated
        updated_data = storage.load()
        assert len(updated_data["tasks"]) == 1
        assert updated_data["tasks"][0]["title"] == "New Title"

    def test_import_mixed_new_and_duplicate_tasks(self, service, tmp_path, storage):
        """Test importing mix of new and duplicate tasks."""
        now = datetime.now(timezone.utc).isoformat()
        existing_task = {
            "id": "task-1",
            "title": "Existing",
            "status": "pending",
            "created_at": now,
            "updated_at": now
        }
        storage.save({"tasks": [existing_task], "comments": []})

        import_file = tmp_path / "import.json"
        import_data = {
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Duplicate",
                    "status": "pending",
                    "created_at": now,
                    "updated_at": now
                },
                {
                    "id": "task-2",
                    "title": "New Task",
                    "status": "pending",
                    "created_at": now,
                    "updated_at": now
                }
            ],
            "comments": []
        }
        import_file.write_text(json.dumps(import_data))

        result = service.import_from_file(str(import_file), overwrite=False)

        assert len(result["added_tasks"]) == 1
        assert "task-2" in result["added_tasks"]
        assert "task-1" in result["skipped_tasks"]

    def test_import_preserves_data_on_error(self, service, tmp_path, storage):
        """Test that storage is not corrupted on validation error."""
        now = datetime.now(timezone.utc).isoformat()
        existing_task = {
            "id": "task-1",
            "title": "Original",
            "status": "pending",
            "created_at": now,
            "updated_at": now
        }
        storage.save({"tasks": [existing_task], "comments": []})

        import_file = tmp_path / "import.json"
        import_file.write_text('{"tasks": "invalid"}')

        with pytest.raises(ImportExportValidationError):
            service.import_from_file(str(import_file))

        # Original data should still be intact
        data = storage.load()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == "task-1"

    def test_export_then_import_round_trip(self, service, tmp_path, storage):
        """Test that data survives export then import."""
        now = datetime.now(timezone.utc).isoformat()
        original_task = {
            "id": "task-1",
            "title": "Round Trip Task",
            "description": "Test",
            "status": "in_progress",
            "created_at": now,
            "updated_at": now,
            "due_date": now
        }
        original_comment = {
            "id": "comment-1",
            "task_id": "task-1",
            "content": "Round trip comment",
            "created_at": now,
            "author": "Tester",
            "updated_at": now
        }
        storage.save({"tasks": [original_task], "comments": [original_comment]})

        # Export
        export_file = tmp_path / "export.json"
        service.export_to_file(str(export_file))

        # Clear storage and import
        storage2 = JsonStorage(str(tmp_path / "test2.json"))
        service2 = ImportExportService(storage2)
        service2.import_from_file(str(export_file))

        # Verify
        imported_data = storage2.load()
        assert len(imported_data["tasks"]) == 1
        assert imported_data["tasks"][0]["title"] == "Round Trip Task"
        assert imported_data["tasks"][0]["due_date"] == now
        assert len(imported_data["comments"]) == 1
        assert imported_data["comments"][0]["author"] == "Tester"


class TestImportEdgeCases:
    """Tests for edge cases in import functionality."""

    def test_import_task_with_optional_fields(self, service, tmp_path):
        """Test importing task with optional fields."""
        now = datetime.now(timezone.utc).isoformat()
        import_file = tmp_path / "import.json"
        import_data = {
            "tasks": [{
                "id": "task-1",
                "title": "Task with Optional Fields",
                "description": None,
                "status": "pending",
                "created_at": now,
                "updated_at": now,
                "due_date": None
            }],
            "comments": []
        }
        import_file.write_text(json.dumps(import_data))

        result = service.import_from_file(str(import_file))
        assert len(result["added_tasks"]) == 1

    def test_import_comment_with_optional_fields(self, service, tmp_path):
        """Test importing comment with optional fields."""
        now = datetime.now(timezone.utc).isoformat()
        import_file = tmp_path / "import.json"
        import_data = {
            "tasks": [],
            "comments": [{
                "id": "comment-1",
                "task_id": "task-1",
                "content": "Comment without optional fields",
                "created_at": now,
                "author": None,
                "updated_at": None
            }]
        }
        import_file.write_text(json.dumps(import_data))

        result = service.import_from_file(str(import_file))
        assert len(result["added_comments"]) == 1

    def test_import_large_batch(self, service, tmp_path):
        """Test importing a large batch of tasks."""
        now = datetime.now(timezone.utc).isoformat()
        tasks = [
            {
                "id": f"task-{i}",
                "title": f"Task {i}",
                "status": "pending",
                "created_at": now,
                "updated_at": now
            }
            for i in range(100)
        ]
        import_file = tmp_path / "import.json"
        import_data = {"tasks": tasks, "comments": []}
        import_file.write_text(json.dumps(import_data))

        result = service.import_from_file(str(import_file))
        assert len(result["added_tasks"]) == 100
        assert result["skipped_tasks"] == []
