"""Integration tests for import/export CLI functionality."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.services.calculator_service import CalculatorService
from src.services.statistics_service import StatisticsService
from src.services.import_export_service import ImportExportService
from src.services.calculator import Calculator
from src.storage.json_storage import JsonStorage
from src.cli.calculator_cli import CalculatorCLI


_TS = "2026-01-01T00:00:00"
_UUID = "c4ebe8ef-ada9-435b-8cca-b60c868586c6"

# Valid UUIDs for testing
_UUID1 = "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
_UUID2 = "a1b2c3d4-e5f6-4789-0123-456789abcdef"
_UUID3 = "12345678-abcd-ef01-2345-6789abcdef01"
_UUID4 = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
_UUID5 = "87654321-dcba-ef10-5432-1087654321fe"


def _make_full_cli(storage_path):
    """Create a fully initialized CLI with all services."""
    storage = JsonStorage(storage_path)
    memory_service = MemoryService(storage)
    calculator_service = CalculatorService(Calculator(), memory_service)
    statistics_service = StatisticsService(memory_service)
    import_export_service = ImportExportService(memory_service)
    cli = CalculatorCLI(calculator_service, statistics_service, import_export_service)
    return cli, calculator_service, memory_service


class TestCLIExportHistory:
    """Tests for CLI export functionality."""

    def test_export_history_interactive(self):
        """Test interactive export from menu."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, calc_service, mem_service = _make_full_cli(storage_path)

            # Add some history
            entry = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.1, timestamp=_TS, uuid=_UUID)
            mem_service.store(entry)

            # Mock input for export path
            export_path = Path(tmpdir) / "export.json"
            with patch("builtins.input", return_value=str(export_path)):
                cli._export_history()

            # Verify export file exists and contains data
            assert export_path.exists()
            with open(export_path) as f:
                data = json.load(f)
            assert len(data) == 1
            assert data[0]["operation"] == "add"

    def test_export_history_interactive_no_service(self, capsys):
        """Test export when service is not available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            calculator_service = CalculatorService(Calculator(), memory_service)
            statistics_service = StatisticsService(memory_service)
            cli = CalculatorCLI(calculator_service, statistics_service, None)

            cli._export_history()
            assert "not available" in capsys.readouterr().out.lower()

    def test_export_history_interactive_cancelled(self, capsys):
        """Test export when user cancels (empty path)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, _, _ = _make_full_cli(storage_path)

            with patch("builtins.input", return_value=""):
                cli._export_history()

            assert "cancelled" in capsys.readouterr().out.lower()

    def test_export_history_interactive_invalid_extension(self, capsys):
        """Test export with invalid file extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, _, _ = _make_full_cli(storage_path)

            export_path = Path(tmpdir) / "export.txt"
            with patch("builtins.input", return_value=str(export_path)):
                cli._export_history()

            assert "error" in capsys.readouterr().out.lower()

    def test_export_history_success_message(self, capsys):
        """Test that successful export shows count and path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, calc_service, mem_service = _make_full_cli(storage_path)

            # Add entries
            for i in range(3):
                entry = MemoryEntry("add", i, i+1, 2*i+1, None, None, execution_time_ms=0.1,
                                   timestamp=f"2026-01-0{i+1}T00:00:00", uuid=[_UUID1, _UUID2, _UUID3, _UUID4, _UUID5][i])
                mem_service.store(entry)

            export_path = Path(tmpdir) / "export.json"
            with patch("builtins.input", return_value=str(export_path)):
                cli._export_history()

            output = capsys.readouterr().out
            assert "3" in output
            assert "export" in output.lower()


class TestCLIImportHistory:
    """Tests for CLI import functionality."""

    def test_import_history_interactive_merge_mode(self):
        """Test interactive import with merge mode (default)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, calc_service, mem_service = _make_full_cli(storage_path)

            # Create initial entry
            entry_initial = MemoryEntry("add", 1, 2, 3, None, None, execution_time_ms=0.1,
                                       timestamp="2026-01-01T00:00:00", uuid=_UUID1)
            mem_service.store(entry_initial)

            # Create import file
            import_data = [
                {
                    "operation": "subtract",
                    "operand_a": 10.0,
                    "operand_b": 4.0,
                    "result": 6.0,
                    "error": None,
                    "error_type": None,
                    "execution_time_ms": 0.1,
                    "timestamp": "2026-01-02T00:00:00",
                    "uuid": _UUID2
                }
            ]
            import_path = Path(tmpdir) / "import.json"
            with open(import_path, "w") as f:
                json.dump(import_data, f)

            # Mock input: filepath, then choose merge (option 1)
            with patch("builtins.input", side_effect=[str(import_path), "1"]):
                cli._import_history()

            # Verify both entries are now in storage
            all_entries = mem_service.retrieve()
            assert len(all_entries) == 2

    def test_import_history_interactive_replace_mode(self):
        """Test interactive import with replace mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, calc_service, mem_service = _make_full_cli(storage_path)

            # Create initial entries
            entry1 = MemoryEntry("add", 1, 2, 3, None, None, execution_time_ms=0.1,
                                timestamp="2026-01-01T00:00:00", uuid=_UUID1)
            entry2 = MemoryEntry("subtract", 10, 4, 6, None, None, execution_time_ms=0.1,
                                timestamp="2026-01-02T00:00:00", uuid=_UUID2)
            mem_service.store(entry1)
            mem_service.store(entry2)

            # Create import file with different data
            import_data = [
                {
                    "operation": "multiply",
                    "operand_a": 5.0,
                    "operand_b": 3.0,
                    "result": 15.0,
                    "error": None,
                    "error_type": None,
                    "execution_time_ms": 0.1,
                    "timestamp": "2026-01-03T00:00:00",
                    "uuid": _UUID3
                }
            ]
            import_path = Path(tmpdir) / "import.json"
            with open(import_path, "w") as f:
                json.dump(import_data, f)

            # Mock input: filepath, then choose replace (option 2)
            with patch("builtins.input", side_effect=[str(import_path), "2"]):
                cli._import_history()

            # Verify only new entry is in storage
            all_entries = mem_service.retrieve()
            assert len(all_entries) == 1
            assert all_entries[0].operation == "multiply"

    def test_import_history_interactive_cancelled(self, capsys):
        """Test import when user cancels (empty path)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, _, _ = _make_full_cli(storage_path)

            with patch("builtins.input", return_value=""):
                cli._import_history()

            assert "cancelled" in capsys.readouterr().out.lower()

    def test_import_history_interactive_no_service(self, capsys):
        """Test import when service is not available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            calculator_service = CalculatorService(Calculator(), memory_service)
            statistics_service = StatisticsService(memory_service)
            cli = CalculatorCLI(calculator_service, statistics_service, None)

            cli._import_history()
            assert "not available" in capsys.readouterr().out.lower()

    def test_import_history_programmatic_with_mode(self):
        """Test import called programmatically with filepath and mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, calc_service, mem_service = _make_full_cli(storage_path)

            # Create import file
            import_data = [
                {
                    "operation": "add",
                    "operand_a": 1.0,
                    "operand_b": 2.0,
                    "result": 3.0,
                    "error": None,
                    "error_type": None,
                    "execution_time_ms": 0.1,
                    "timestamp": "2026-01-01T00:00:00",
                    "uuid": _UUID1
                }
            ]
            import_path = Path(tmpdir) / "import.json"
            with open(import_path, "w") as f:
                json.dump(import_data, f)

            # Import programmatically (no user input needed)
            cli._import_history(filepath=str(import_path), mode="merge")

            # Verify entry is in storage
            all_entries = mem_service.retrieve()
            assert len(all_entries) == 1
            assert all_entries[0].operation == "add"

    def test_import_history_invalid_file(self, capsys):
        """Test import with missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, _, _ = _make_full_cli(storage_path)

            import_path = Path(tmpdir) / "nonexistent.json"
            cli._import_history(filepath=str(import_path), mode="merge")

            assert "error" in capsys.readouterr().out.lower()


class TestShowImportResult:
    """Tests for ImportExportService._show_import_result()"""

    def test_show_import_result_all_imported(self, capsys):
        """Test showing results when all entries imported successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, _, _ = _make_full_cli(storage_path)

            result = {
                "imported_count": 5,
                "skipped_count": 0,
                "skipped_entries": [],
                "duplicates_count": 0,
                "invalid_count": 0
            }

            cli._show_import_result(result)
            output = capsys.readouterr().out
            assert "5" in output
            assert "imported" in output.lower()

    def test_show_import_result_with_skipped(self, capsys):
        """Test showing results with skipped entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, _, _ = _make_full_cli(storage_path)

            result = {
                "imported_count": 3,
                "skipped_count": 2,
                "skipped_entries": [{}, {}],
                "duplicates_count": 1,
                "invalid_count": 1
            }

            cli._show_import_result(result)
            output = capsys.readouterr().out
            assert "3" in output
            assert "2" in output
            assert "1" in output
            assert "duplicate" in output.lower()
            assert "invalid" in output.lower()

    def test_show_import_result_all_skipped(self, capsys):
        """Test showing results when all entries skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, _, _ = _make_full_cli(storage_path)

            result = {
                "imported_count": 0,
                "skipped_count": 5,
                "skipped_entries": [{}, {}, {}, {}, {}],
                "duplicates_count": 3,
                "invalid_count": 2
            }

            cli._show_import_result(result)
            output = capsys.readouterr().out
            assert "0" in output
            assert "5" in output


class TestExportImportIntegration:
    """Integration tests for export/import combined operations."""

    def test_export_then_import_preserves_data(self):
        """Test that export then import to new storage preserves all data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create first storage and add entries
            storage1_path = Path(tmpdir) / "storage1.json"
            cli1, _, mem_service1 = _make_full_cli(storage1_path)

            entry1 = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.5,
                                timestamp="2026-01-01T00:00:00", uuid=_UUID1)
            entry2 = MemoryEntry("divide", 10, 2, 5, None, None, execution_time_ms=0.3,
                                timestamp="2026-01-02T00:00:00", uuid=_UUID2)
            mem_service1.store(entry1)
            mem_service1.store(entry2)

            # Export
            export_path = Path(tmpdir) / "export.json"
            with patch("builtins.input", return_value=str(export_path)):
                cli1._export_history()

            # Create second storage and import
            storage2_path = Path(tmpdir) / "storage2.json"
            cli2, _, mem_service2 = _make_full_cli(storage2_path)

            cli2._import_history(filepath=str(export_path), mode="merge")

            # Verify data is identical
            entries1 = mem_service1.retrieve()
            entries2 = mem_service2.retrieve()

            assert len(entries1) == len(entries2)
            for e1, e2 in zip(entries1, entries2):
                assert e1.operation == e2.operation
                assert e1.operand_a == e2.operand_a
                assert e1.operand_b == e2.operand_b
                assert e1.result == e2.result
                assert e1.uuid == e2.uuid

    def test_export_import_merge_appends_data(self):
        """Test that merge import appends to existing data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create storage with initial data
            storage_path = Path(tmpdir) / "storage.json"
            cli, _, mem_service = _make_full_cli(storage_path)

            entry_initial = MemoryEntry("add", 1, 2, 3, None, None, execution_time_ms=0.1,
                                       timestamp="2026-01-01T00:00:00", uuid=_UUID1)
            mem_service.store(entry_initial)

            # Create export file with different data
            export_data = [
                {
                    "operation": "subtract",
                    "operand_a": 10.0,
                    "operand_b": 4.0,
                    "result": 6.0,
                    "error": None,
                    "error_type": None,
                    "execution_time_ms": 0.1,
                    "timestamp": "2026-01-02T00:00:00",
                    "uuid": _UUID2
                }
            ]
            export_path = Path(tmpdir) / "export.json"
            with open(export_path, "w") as f:
                json.dump(export_data, f)

            # Import in merge mode
            cli._import_history(filepath=str(export_path), mode="merge")

            # Verify both entries are present
            all_entries = mem_service.retrieve()
            assert len(all_entries) == 2
            assert all_entries[0].operation == "add"
            assert all_entries[1].operation == "subtract"

    def test_export_import_replace_clears_then_adds(self):
        """Test that replace import clears existing data first."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create storage with initial data
            storage_path = Path(tmpdir) / "storage.json"
            cli, _, mem_service = _make_full_cli(storage_path)

            # Add multiple initial entries
            for i in range(3):
                entry = MemoryEntry("add", i, i+1, 2*i+1, None, None, execution_time_ms=0.1,
                                   timestamp=f"2026-01-0{i+1}T00:00:00", uuid=[_UUID1, _UUID2, _UUID3, _UUID4, _UUID5][i])
                mem_service.store(entry)

            # Create export file with different data
            export_data = [
                {
                    "operation": "multiply",
                    "operand_a": 5.0,
                    "operand_b": 3.0,
                    "result": 15.0,
                    "error": None,
                    "error_type": None,
                    "execution_time_ms": 0.1,
                    "timestamp": "2026-01-10T00:00:00",
                    "uuid": _UUID5
                }
            ]
            export_path = Path(tmpdir) / "export.json"
            with open(export_path, "w") as f:
                json.dump(export_data, f)

            # Import in replace mode
            cli._import_history(filepath=str(export_path), mode="replace")

            # Verify only new entry is present
            all_entries = mem_service.retrieve()
            assert len(all_entries) == 1
            assert all_entries[0].operation == "multiply"


class TestMenuIntegration:
    """Tests for export/import menu options in interactive mode."""

    def test_menu_shows_export_option(self, capsys):
        """Test that export option appears in menu."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, _, _ = _make_full_cli(storage_path)

            cli._print_menu()
            output = capsys.readouterr().out
            assert "export" in output.lower()

    def test_menu_shows_import_option(self, capsys):
        """Test that import option appears in menu."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, _, _ = _make_full_cli(storage_path)

            cli._print_menu()
            output = capsys.readouterr().out
            assert "import" in output.lower()

    def test_interactive_export_option_number(self, capsys):
        """Test that export option has correct menu number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, _, _ = _make_full_cli(storage_path)

            # Menu should have: 8 operations + 6 utilities (history, filter, statistics, export, import, exit)
            # Export should be option 18 (8 + 6 utilities, second to last)
            cli._print_menu()
            output = capsys.readouterr().out
            lines = output.split('\n')
            # Find the export line
            export_line = [l for l in lines if "export" in l.lower()]
            assert len(export_line) > 0
            assert "18" in export_line[0]

    def test_interactive_import_option_number(self, capsys):
        """Test that import option has correct menu number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "storage.json"
            cli, _, _ = _make_full_cli(storage_path)

            cli._print_menu()
            output = capsys.readouterr().out
            lines = output.split('\n')
            # Find the import line
            import_line = [l for l in lines if "import" in l.lower()]
            assert len(import_line) > 0
            assert "19" in import_line[0]
