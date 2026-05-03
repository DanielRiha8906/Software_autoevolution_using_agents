"""Tests for interactive menu export and import functionality."""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from src.cli.interactive_menu import InteractiveMenu
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage
from src.models.task_status import TaskStatus


@pytest.fixture
def menu(tmp_path):
    """Interactive menu with isolated storage."""
    return InteractiveMenu(str(tmp_path / "tasks.json"))


@pytest.fixture
def temp_export_file(tmp_path):
    """Temporary export file."""
    return str(tmp_path / "export.json")


@pytest.fixture
def temp_import_file(tmp_path):
    """Temporary import file."""
    return str(tmp_path / "import.json")


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT MENU TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestMenuExport:
    """Test interactive menu export functionality."""

    def test_do_export_prompts_for_file_path(self, menu, temp_export_file, monkeypatch, capsys):
        """Export prompts user for file path."""
        menu._service.add_task("Task 1")

        # Mock input to provide file path
        monkeypatch.setattr("builtins.input", lambda _: temp_export_file)

        menu._do_export()
        captured = capsys.readouterr()

        assert "Export" in captured.out
        assert Path(temp_export_file).exists()

    def test_do_export_uses_default_path_when_empty(self, menu, monkeypatch, capsys):
        """Export uses default path when user enters empty input."""
        menu._service.add_task("Task 1")

        # Mock input to return empty (accept default)
        monkeypatch.setattr("builtins.input", lambda prompt: "")

        menu._do_export()
        captured = capsys.readouterr()

        # Check for success message
        assert "Exported" in captured.out

        # Check default path was used
        default_path = Path.home() / ".todo_export.json"
        assert default_path.exists()
        default_path.unlink()

    def test_do_export_shows_success_message(self, menu, temp_export_file, monkeypatch, capsys):
        """Export shows success message with count and path."""
        menu._service.add_task("Task 1")
        menu._service.add_task("Task 2")

        monkeypatch.setattr("builtins.input", lambda _: temp_export_file)

        menu._do_export()
        captured = capsys.readouterr()

        assert "Success" in captured.out
        assert "2 task" in captured.out
        assert temp_export_file in captured.out

    def test_do_export_shows_error_on_unwritable_directory(self, menu, tmp_path, monkeypatch, capsys):
        """Export shows error message when directory is unwritable."""
        menu._service.add_task("Task 1")

        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)

        try:
            bad_path = str(readonly_dir / "export.json")
            monkeypatch.setattr("builtins.input", lambda _: bad_path)

            menu._do_export()
            captured = capsys.readouterr()

            assert "Error" in captured.out
        finally:
            readonly_dir.chmod(0o755)

    def test_do_export_empty_task_list(self, menu, temp_export_file, monkeypatch, capsys):
        """Export empty task list exports array with no items."""
        monkeypatch.setattr("builtins.input", lambda _: temp_export_file)

        menu._do_export()

        with open(temp_export_file) as f:
            data = json.load(f)
        assert data == []

    def test_do_export_with_descriptions(self, menu, temp_export_file, monkeypatch, capsys):
        """Export preserves task descriptions."""
        menu._service.add_task("Task", description="Important task")

        monkeypatch.setattr("builtins.input", lambda _: temp_export_file)

        menu._do_export()

        with open(temp_export_file) as f:
            data = json.load(f)
        assert data[0]["description"] == "Important task"

    def test_do_export_with_due_dates(self, menu, temp_export_file, monkeypatch, capsys):
        """Export preserves due dates."""
        dt = datetime(2026, 6, 15, 14, 30, tzinfo=timezone.utc)
        menu._service.add_task("Task", due_date=dt)

        monkeypatch.setattr("builtins.input", lambda _: temp_export_file)

        menu._do_export()

        with open(temp_export_file) as f:
            data = json.load(f)
        assert data[0]["due_date"] is not None
        assert datetime.fromisoformat(data[0]["due_date"]) == dt

    def test_do_export_creates_parent_directories(self, menu, tmp_path, monkeypatch, capsys):
        """Export creates parent directories automatically."""
        menu._service.add_task("Task")

        nested_path = str(tmp_path / "export" / "subdir" / "tasks.json")
        monkeypatch.setattr("builtins.input", lambda _: nested_path)

        menu._do_export()

        assert Path(nested_path).exists()


# ─────────────────────────────────────────────────────────────────────────────
# IMPORT MENU TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestMenuImport:
    """Test interactive menu import functionality."""

    def test_do_import_prompts_for_file_path(self, menu, temp_import_file, monkeypatch, capsys):
        """Import prompts user for file path."""
        # Create import file
        data = [
            {
                "id": "task-1",
                "title": "Imported",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(temp_import_file, "w") as f:
            json.dump(data, f)

        # Mock inputs: file path, then strategy choice (1 = skip), then press enter to continue
        inputs = [temp_import_file, "1", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()
        captured = capsys.readouterr()

        assert "Import" in captured.out

    def test_do_import_asks_for_strategy(self, menu, temp_import_file, monkeypatch, capsys):
        """Import asks user to select duplicate strategy."""
        # Create import file
        data = [
            {
                "id": "task-1",
                "title": "Task",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(temp_import_file, "w") as f:
            json.dump(data, f)

        # Mock inputs: file path, strategy, then press enter
        inputs = [temp_import_file, "1", ""]  # 1 = skip
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()
        captured = capsys.readouterr()

        # Should show strategy selection
        assert "skip" in captured.out.lower() or "replace" in captured.out.lower()

    def test_do_import_skip_strategy(self, menu, temp_import_file, monkeypatch, capsys):
        """Import with skip strategy (option 1) keeps existing tasks."""
        # Add existing task
        existing = menu._service.add_task("Original")

        # Create import file with duplicate
        data = [
            {
                "id": existing.id,
                "title": "Replacement",
                "status": "done",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(temp_import_file, "w") as f:
            json.dump(data, f)

        # Mock inputs: path, then strategy 1 (skip)
        inputs = [temp_import_file, "1", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()

        # Verify original is unchanged
        task = menu._service.get_task(existing.id)
        assert task.title == "Original"

    def test_do_import_replace_strategy(self, menu, temp_import_file, monkeypatch, capsys):
        """Import with replace strategy (option 2) overwrites existing tasks."""
        # Add existing task
        existing = menu._service.add_task("Original")

        # Create import file with duplicate
        data = [
            {
                "id": existing.id,
                "title": "Replacement",
                "status": "done",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": "New description",
                "due_date": None,
                "comments": []
            }
        ]

        with open(temp_import_file, "w") as f:
            json.dump(data, f)

        # Mock inputs: path, then strategy 2 (replace)
        inputs = [temp_import_file, "2", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()

        # Verify task was replaced
        task = menu._service.get_task(existing.id)
        assert task.title == "Replacement"

    def test_do_import_cancel_on_empty_path(self, menu, monkeypatch, capsys):
        """Import cancels when user enters empty file path."""
        # One input for empty path, one for "Press Enter" after error message
        inputs = ["", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda prompt: next(input_iter))

        menu._do_import()
        captured = capsys.readouterr()

        # Verify we're back to the main menu (no more output after the error)
        assert "Import Tasks" in captured.out

    def test_do_import_cancel_on_strategy_cancel(self, menu, temp_import_file, monkeypatch, capsys):
        """Import cancels when user cancels strategy selection."""
        # Create import file
        data = [
            {
                "id": "task-1",
                "title": "Task",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(temp_import_file, "w") as f:
            json.dump(data, f)

        # Mock inputs: path, then strategy cancel (0)
        inputs = [temp_import_file, "0", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()

        # No task should be imported
        assert len(menu._service.list_tasks()) == 0

    def test_do_import_shows_result_summary(self, menu, temp_import_file, monkeypatch, capsys):
        """Import shows result summary with counts."""
        # Create import file
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

        with open(temp_import_file, "w") as f:
            json.dump(data, f)

        # Mock inputs
        inputs = [temp_import_file, "1", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()
        captured = capsys.readouterr()

        assert "Import Result" in captured.out
        assert "Imported:" in captured.out
        assert "Skipped:" in captured.out

    def test_do_import_shows_error_count(self, menu, temp_import_file, monkeypatch, capsys):
        """Import shows error count when validation fails."""
        # Create import file with invalid entry
        data = [
            {
                "id": "bad",
                "title": "Task",
                "status": "invalid_status",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(temp_import_file, "w") as f:
            json.dump(data, f)

        # Mock inputs
        inputs = [temp_import_file, "1", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()
        captured = capsys.readouterr()

        assert "Errors:" in captured.out

    def test_do_import_shows_error_details(self, menu, temp_import_file, monkeypatch, capsys):
        """Import shows first 5 error details."""
        # Create import file with invalid entry
        data = [
            {
                "id": "bad",
                "title": "Task",
                "status": "invalid_status",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(temp_import_file, "w") as f:
            json.dump(data, f)

        # Mock inputs
        inputs = [temp_import_file, "1", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()
        captured = capsys.readouterr()

        # Should show error message
        assert "status" in captured.out.lower() or "-" in captured.out

    def test_do_import_shows_no_errors_message_when_clean(self, menu, temp_import_file, monkeypatch, capsys):
        """Import shows 'No errors' when import is clean."""
        # Create import file
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

        with open(temp_import_file, "w") as f:
            json.dump(data, f)

        # Mock inputs
        inputs = [temp_import_file, "1", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()
        captured = capsys.readouterr()

        assert "No errors" in captured.out

    def test_do_import_handles_file_not_found_gracefully(self, menu, monkeypatch, capsys):
        """Import handles nonexistent file gracefully."""
        nonexistent = "/path/to/nonexistent/file.json"

        # Mock inputs
        inputs = [nonexistent, "1", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()
        captured = capsys.readouterr()

        # Should show error message
        assert "Error" in captured.out

    def test_do_import_handles_invalid_json_gracefully(self, menu, tmp_path, monkeypatch, capsys):
        """Import handles invalid JSON gracefully."""
        bad_file = tmp_path / "invalid.json"
        bad_file.write_text("{invalid json}")

        # Mock inputs
        inputs = [str(bad_file), "1", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()
        captured = capsys.readouterr()

        # Should show error message
        assert "Error" in captured.out

    def test_do_import_with_comments(self, menu, temp_import_file, monkeypatch, capsys):
        """Import preserves task comments."""
        # Create import file with comments
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
                        "content": "Good task",
                        "author": "Alice",
                        "created_at": "2026-05-01T11:00:00+00:00",
                        "updated_at": None
                    }
                ]
            }
        ]

        with open(temp_import_file, "w") as f:
            json.dump(data, f)

        # Mock inputs
        inputs = [temp_import_file, "1", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()

        # Verify comment was imported
        comments = menu._service.get_comments("task-1")
        assert len(comments) == 1
        assert comments[0].content == "Good task"

    def test_do_import_persists_to_storage(self, menu, tmp_path, monkeypatch, capsys):
        """Import persists changes to storage."""
        # Create import file
        data = [
            {
                "id": "persistent",
                "title": "Will persist",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        import_file = str(tmp_path / "import.json")
        with open(import_file, "w") as f:
            json.dump(data, f)

        # Mock inputs: file path, strategy, press enter
        inputs = [import_file, "1", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()

        # Create new menu with same storage
        menu2 = InteractiveMenu(str(tmp_path / "tasks.json"))

        # Task should still exist
        task = menu2._service.get_task("persistent")
        assert task.title == "Will persist"

    def test_do_import_roundtrip_via_menu(self, menu, tmp_path, monkeypatch, capsys):
        """Menu export then import preserves data."""
        # Create tasks
        menu._service.add_task("Task 1")
        menu._service.add_task("Task 2")

        export_file = str(tmp_path / "export.json")

        # Mock input for export (file path + press enter)
        inputs_export = [export_file, ""]
        export_iter = iter(inputs_export)
        monkeypatch.setattr("builtins.input", lambda _: next(export_iter))
        menu._do_export()

        # Create new menu
        menu2 = InteractiveMenu(str(tmp_path / "tasks2.json"))

        # Mock inputs for import: path, strategy, press enter
        inputs_import = [export_file, "1", ""]
        import_iter = iter(inputs_import)
        monkeypatch.setattr("builtins.input", lambda _: next(import_iter))
        menu2._do_import()

        # Verify
        tasks = menu2._service.list_tasks()
        assert len(tasks) == 2
        titles = {t.title for t in tasks}
        assert titles == {"Task 1", "Task 2"}


# ─────────────────────────────────────────────────────────────────────────────
# USER FEEDBACK TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestMenuUserExperience:
    """Test user experience and message quality."""

    def test_export_message_is_user_friendly(self, menu, temp_export_file, monkeypatch, capsys):
        """Export messages are user-friendly."""
        menu._service.add_task("Important task")

        monkeypatch.setattr("builtins.input", lambda _: temp_export_file)
        menu._do_export()

        captured = capsys.readouterr()

        # Should contain:
        # - Success indication
        # - Task count (human-readable plural)
        # - File path
        assert "Exported" in captured.out or "Success" in captured.out
        assert "1 task" in captured.out or "1 tasks" in captured.out

    def test_import_message_shows_summary(self, menu, temp_import_file, monkeypatch, capsys):
        """Import messages show clear summary."""
        # Create import file
        data = [
            {
                "id": "task-1",
                "title": "Task",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
        ]

        with open(temp_import_file, "w") as f:
            json.dump(data, f)

        # Mock inputs
        inputs = [temp_import_file, "1", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()
        captured = capsys.readouterr()

        # Should show:
        # - Section heading
        # - Imported count
        # - Skipped count
        # - No errors (or error count)
        assert "Import Result" in captured.out
        assert "Imported:" in captured.out
        assert "Skipped:" in captured.out

    def test_error_message_on_bad_file_path(self, menu, monkeypatch, capsys):
        """Error message shown for bad file path."""
        # Mock inputs: file path, strategy, press enter
        inputs = ["/nonexistent/path/file.json", "1", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()
        captured = capsys.readouterr()

        # Should show error, not crash
        assert "Error" in captured.out

    def test_menu_continues_after_export_error(self, menu, tmp_path, monkeypatch, capsys):
        """Menu allows user to continue after export error."""
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)

        try:
            bad_path = str(readonly_dir / "export.json")
            # Input for file path, then press enter to continue
            monkeypatch.setattr("builtins.input", lambda _: bad_path)

            menu._do_export()
            captured = capsys.readouterr()

            assert "Error" in captured.out
            # Function should complete without crashing
        finally:
            readonly_dir.chmod(0o755)

    def test_menu_continues_after_import_error(self, menu, monkeypatch, capsys):
        """Menu allows user to continue after import error."""
        # Mock inputs for nonexistent file, strategy, and press enter
        inputs = ["/nonexistent/path.json", "1", ""]
        input_iter = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_iter))

        menu._do_import()
        captured = capsys.readouterr()

        # Should show error
        assert "Error" in captured.out
