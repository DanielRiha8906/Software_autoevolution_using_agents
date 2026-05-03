"""Tests for CLI export and import commands."""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from src.cli.todo_cli import TodoCLI
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage
from src.models.task_status import TaskStatus


@pytest.fixture
def cli(tmp_path):
    """CLI with isolated storage."""
    return TodoCLI(str(tmp_path / "tasks.json"))


@pytest.fixture
def temp_export_file(tmp_path):
    """Temporary export file."""
    return str(tmp_path / "export.json")


@pytest.fixture
def populated_cli(tmp_path):
    """CLI with pre-populated tasks."""
    cli = TodoCLI(str(tmp_path / "tasks.json"))
    cli._service.add_task("Task 1", description="Description 1")
    cli._service.add_task("Task 2")
    t3 = cli._service.add_task("Task 3")
    cli._service.start_task(t3.id)
    return cli


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT CLI TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestExportCLI:
    """Test CLI export command."""

    def test_export_no_file_uses_default_path(self, cli, capsys):
        """Export without --file uses default path."""
        cli._service.add_task("Test")

        exit_code = cli.run(["export"])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "Exported" in captured.out
        assert "1 task" in captured.out

        # Check default path
        default_path = Path.home() / ".todo_export.json"
        assert default_path.exists()
        default_path.unlink()

    def test_export_with_file_argument(self, cli, temp_export_file, capsys):
        """Export with --file saves to specified path."""
        cli._service.add_task("Test")

        exit_code = cli.run(["export", "--file", temp_export_file])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "Exported" in captured.out
        assert "1 task" in captured.out
        assert temp_export_file in captured.out

        assert Path(temp_export_file).exists()

    def test_export_success_returns_exit_code_0(self, cli, temp_export_file):
        """Successful export returns exit code 0."""
        cli._service.add_task("Test")

        exit_code = cli.run(["export", "--file", temp_export_file])
        assert exit_code == 0

    def test_export_creates_parent_directories(self, cli, tmp_path, capsys):
        """Export creates parent directories as needed."""
        cli._service.add_task("Test")
        nested_path = str(tmp_path / "deep" / "nested" / "export.json")

        exit_code = cli.run(["export", "--file", nested_path])
        assert exit_code == 0

        assert Path(nested_path).exists()

    def test_export_empty_task_list(self, cli, temp_export_file, capsys):
        """Export with no tasks exports empty array."""
        exit_code = cli.run(["export", "--file", temp_export_file])
        assert exit_code == 0

        with open(temp_export_file) as f:
            data = json.load(f)
        assert data == []

    def test_export_multiple_tasks(self, cli, temp_export_file, capsys):
        """Export with multiple tasks."""
        cli._service.add_task("A")
        cli._service.add_task("B")
        cli._service.add_task("C")

        exit_code = cli.run(["export", "--file", temp_export_file])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "3 task" in captured.out

    def test_export_unwritable_directory_returns_error_code(self, cli, tmp_path, capsys):
        """Export to unwritable directory returns exit code 1."""
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)

        try:
            bad_path = str(readonly_dir / "export.json")
            exit_code = cli.run(["export", "--file", bad_path])
            assert exit_code == 1

            captured = capsys.readouterr()
            assert "Error" in captured.err
        finally:
            readonly_dir.chmod(0o755)

    def test_export_message_format(self, cli, temp_export_file, capsys):
        """Export message has correct format."""
        cli._service.add_task("Task 1")
        cli._service.add_task("Task 2")

        cli.run(["export", "--file", temp_export_file])
        captured = capsys.readouterr()

        # Should show count and path
        assert "Exported" in captured.out
        assert "2" in captured.out
        assert temp_export_file in captured.out


class TestImportCLI:
    """Test CLI import command."""

    def test_import_valid_file(self, cli, tmp_path, capsys):
        """Import from valid file."""
        import_file = tmp_path / "import.json"

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

        with open(import_file, "w") as f:
            json.dump(data, f)

        exit_code = cli.run(["import", "--file", str(import_file)])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "Import complete" in captured.out
        assert "Imported: 1" in captured.out

    def test_import_required_file_argument(self, cli):
        """Import requires --file argument."""
        # argparse will raise SystemExit if required arg missing
        with pytest.raises(SystemExit):
            cli.run(["import"])

    def test_import_missing_file_shows_error(self, cli, tmp_path, capsys):
        """Import from nonexistent file shows error."""
        missing = str(tmp_path / "missing.json")

        exit_code = cli.run(["import", "--file", missing])
        assert exit_code == 0  # Import completes but with error in output

        captured = capsys.readouterr()
        assert "Import complete" in captured.out
        assert "Errors" in captured.out

    def test_import_skip_strategy_default(self, cli, tmp_path, capsys):
        """Import uses skip strategy by default."""
        # Add existing task
        existing = cli._service.add_task("Original")

        # Create import file with duplicate
        import_file = tmp_path / "import.json"
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

        with open(import_file, "w") as f:
            json.dump(data, f)

        exit_code = cli.run(["import", "--file", str(import_file)])
        assert exit_code == 0

        # Original should be unchanged
        task = cli._service.get_task(existing.id)
        assert task.title == "Original"

    def test_import_replace_strategy(self, cli, tmp_path, capsys):
        """Import with --strategy replace overwrites duplicates."""
        # Add existing task
        existing = cli._service.add_task("Original")

        # Create import file with duplicate
        import_file = tmp_path / "import.json"
        data = [
            {
                "id": existing.id,
                "title": "Replacement",
                "status": "done",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": "New desc",
                "due_date": None,
                "comments": []
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        exit_code = cli.run(["import", "--file", str(import_file), "--strategy", "replace"])
        assert exit_code == 0

        # Task should be replaced
        task = cli._service.get_task(existing.id)
        assert task.title == "Replacement"
        assert task.description == "New desc"
        assert task.status == TaskStatus.DONE

    def test_import_skip_strategy_explicit(self, cli, tmp_path, capsys):
        """Import with --strategy skip keeps existing."""
        # Add existing task
        existing = cli._service.add_task("Original")

        # Create import file with duplicate
        import_file = tmp_path / "import.json"
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

        with open(import_file, "w") as f:
            json.dump(data, f)

        exit_code = cli.run(["import", "--file", str(import_file), "--strategy", "skip"])
        assert exit_code == 0

        # Original should be unchanged
        task = cli._service.get_task(existing.id)
        assert task.title == "Original"

    def test_import_message_format(self, cli, tmp_path, capsys):
        """Import message has correct format."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "valid-1",
                "title": "Valid 1",
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
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        cli.run(["import", "--file", str(import_file)])
        captured = capsys.readouterr()

        assert "Import complete" in captured.out
        assert "Imported: 1" in captured.out
        assert "Skipped:" in captured.out
        assert "Errors:" in captured.out

    def test_import_shows_error_details(self, cli, tmp_path, capsys):
        """Import shows first 5 error details."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "bad-1",
                "title": "Task",
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

        cli.run(["import", "--file", str(import_file)])
        captured = capsys.readouterr()

        assert "Invalid status" in captured.out or "status" in captured.out.lower()

    def test_import_no_errors_shows_no_errors_message(self, cli, tmp_path, capsys):
        """Import with no errors doesn't show error section."""
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

        cli.run(["import", "--file", str(import_file)])
        captured = capsys.readouterr()

        assert "Imported: 1" in captured.out
        # When no errors, errors line should not be present or should show 0
        assert "Errors:" not in captured.out or "0" not in captured.out

    def test_import_summary_imported_count(self, cli, tmp_path, capsys):
        """Import summary shows correct imported count."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": f"task-{i}",
                "title": f"Task {i}",
                "status": "pending",
                "created_at": "2026-05-01T10:00:00+00:00",
                "updated_at": "2026-05-01T10:00:00+00:00",
                "description": None,
                "due_date": None,
                "comments": []
            }
            for i in range(3)
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        cli.run(["import", "--file", str(import_file)])
        captured = capsys.readouterr()

        assert "Imported: 3" in captured.out

    def test_import_summary_skipped_count(self, cli, tmp_path, capsys):
        """Import summary shows correct skipped count for duplicates."""
        # Add existing task
        existing = cli._service.add_task("Existing")

        import_file = tmp_path / "import.json"
        data = [
            {
                "id": existing.id,
                "title": "Different",
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

        cli.run(["import", "--file", str(import_file)])
        captured = capsys.readouterr()

        assert "Skipped:" in captured.out
        assert "1" in captured.out  # Should show skipped count

    def test_import_roundtrip_cli(self, cli, tmp_path, capsys):
        """CLI export then import preserves data."""
        # Create tasks
        cli._service.add_task("Task 1")
        cli._service.add_task("Task 2")

        # Export
        export_file = str(tmp_path / "export.json")
        cli.run(["export", "--file", export_file])

        # Create new CLI and import
        cli2 = TodoCLI(str(tmp_path / "tasks2.json"))
        cli2.run(["import", "--file", export_file])

        # Verify
        tasks = cli2._service.list_tasks()
        assert len(tasks) == 2
        titles = {t.title for t in tasks}
        assert titles == {"Task 1", "Task 2"}

    def test_import_with_comments_via_cli(self, cli, tmp_path, capsys):
        """CLI import preserves comments."""
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
                        "content": "Imported comment",
                        "author": "Bot",
                        "created_at": "2026-05-01T11:00:00+00:00",
                        "updated_at": None
                    }
                ]
            }
        ]

        with open(import_file, "w") as f:
            json.dump(data, f)

        cli.run(["import", "--file", str(import_file)])

        comments = cli._service.get_comments("task-1")
        assert len(comments) == 1
        assert comments[0].content == "Imported comment"

    def test_import_persists_to_storage(self, cli, tmp_path):
        """CLI import persists changes to storage file."""
        import_file = tmp_path / "import.json"

        data = [
            {
                "id": "task-1",
                "title": "Persistent",
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

        cli.run(["import", "--file", str(import_file)])

        # Create new CLI with same storage file
        cli2 = TodoCLI(str(tmp_path / "tasks.json"))

        # Task should still be there
        task = cli2._service.get_task("task-1")
        assert task.title == "Persistent"
