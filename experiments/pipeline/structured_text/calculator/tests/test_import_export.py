"""
Comprehensive tests for import/export functionality.

Covers MemoryService.export_to_file(), MemoryService.import_from_file(),
CalculatorCLI.export_memory(), CalculatorCLI.import_memory(),
and CLI flag handling for --export, --import, and --skip-invalid.
"""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.storage.memory_json_storage import MemoryJsonStorage
from src.cli.calculator_cli import CalculatorCLI
from src import __main__


# ============================================================================
# Fixtures for sample data
# ============================================================================

@pytest.fixture
def sample_entries():
    """Sample MemoryEntry objects for testing."""
    return [
        MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.5,
            memory_entry_id="id-1"
        ),
        MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero",
            execution_timestamp="2026-05-03T10:01:00",
            execution_time_ms=0.5,
            memory_entry_id="id-2"
        ),
        MemoryEntry(
            operation="multiply",
            operand_a=4.0,
            operand_b=5.0,
            result=20.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:02:00",
            execution_time_ms=2.0,
            memory_entry_id="id-3"
        ),
    ]


@pytest.fixture
def memory_service(tmp_path):
    """Fresh MemoryService with temporary storage."""
    storage = MemoryJsonStorage(tmp_path / "memory.json")
    return MemoryService(storage)


@pytest.fixture
def cli_with_memory_service(tmp_path):
    """CalculatorCLI with memory service enabled."""
    service = MagicMock()
    memory_storage = MemoryJsonStorage(tmp_path / "memory.json")
    memory_service = MemoryService(memory_storage)
    return CalculatorCLI(service, memory_service), memory_service, tmp_path


# ============================================================================
# MemoryService.export_to_file() Tests
# ============================================================================

class TestMemoryServiceExportToFile:
    """Test MemoryService.export_to_file() method."""

    def test_export_creates_file(self, memory_service, sample_entries, tmp_path):
        """Test 1: export_to_file creates file at specified path."""
        for entry in sample_entries:
            memory_service.store(entry)

        export_path = tmp_path / "export.json"
        count = memory_service.export_to_file(export_path)

        assert export_path.exists()
        assert export_path.is_file()
        assert count == 3

    def test_export_returns_correct_count(self, memory_service, sample_entries, tmp_path):
        """Test 2: export_to_file returns count of exported entries."""
        for entry in sample_entries[:2]:
            memory_service.store(entry)

        export_path = tmp_path / "export.json"
        count = memory_service.export_to_file(export_path)

        assert count == 2

    def test_export_empty_storage_returns_zero(self, memory_service, tmp_path):
        """Test 3: export_to_file with empty storage returns 0."""
        export_path = tmp_path / "export.json"
        count = memory_service.export_to_file(export_path)

        assert count == 0
        assert export_path.exists()

    def test_export_creates_parent_directories(self, memory_service, sample_entries, tmp_path):
        """Test 4: export_to_file creates parent directories if needed."""
        for entry in sample_entries:
            memory_service.store(entry)

        deep_path = tmp_path / "a" / "b" / "c" / "export.json"
        count = memory_service.export_to_file(deep_path)

        assert deep_path.exists()
        assert count == 3
        assert deep_path.parent.exists()

    def test_export_preserves_all_fields(self, memory_service, sample_entries, tmp_path):
        """Test 5: export_to_file preserves all MemoryEntry fields."""
        for entry in sample_entries:
            memory_service.store(entry)

        export_path = tmp_path / "export.json"
        memory_service.export_to_file(export_path)

        with open(export_path) as f:
            data = json.load(f)

        # Check first entry (successful add)
        assert data[0]["operation"] == "add"
        assert data[0]["operand_a"] == 1.0
        assert data[0]["operand_b"] == 2.0
        assert data[0]["result"] == 3.0
        assert data[0]["success"] is True
        assert data[0]["error_message"] is None
        assert data[0]["execution_timestamp"] == "2026-05-03T10:00:00"
        assert data[0]["execution_time_ms"] == 1.5
        assert data[0]["memory_entry_id"] == "id-1"

        # Check second entry (failed divide)
        assert data[1]["operation"] == "divide"
        assert data[1]["success"] is False
        assert data[1]["error_message"] == "Division by zero"
        assert data[1]["result"] is None

    def test_export_valid_json_format(self, memory_service, sample_entries, tmp_path):
        """Test 6: exported file contains valid JSON array."""
        for entry in sample_entries:
            memory_service.store(entry)

        export_path = tmp_path / "export.json"
        memory_service.export_to_file(export_path)

        with open(export_path) as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 3
        assert all(isinstance(item, dict) for item in data)

    def test_export_overwrites_existing_file(self, memory_service, sample_entries, tmp_path):
        """Test 7: export_to_file overwrites existing file."""
        # Create file with old data
        export_path = tmp_path / "export.json"
        export_path.write_text('{"old": "data"}')

        # Store and export new data
        for entry in sample_entries:
            memory_service.store(entry)

        count = memory_service.export_to_file(export_path)

        # Verify file was overwritten
        with open(export_path) as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert count == 3

    def test_export_with_invalid_path_raises_ioerror(self, memory_service, sample_entries):
        """Test 8: export_to_file raises IOError with invalid path."""
        for entry in sample_entries:
            memory_service.store(entry)

        # Use a path with a non-existent parent that cannot be created
        # (on Unix, /dev/null/bad is invalid; on Windows, use similar approach)
        invalid_path = Path("/dev/null/impossible/path.json")

        with pytest.raises(OSError):
            memory_service.export_to_file(invalid_path)

    def test_export_path_as_string(self, memory_service, sample_entries, tmp_path):
        """Test 9: export_to_file accepts filepath as string."""
        for entry in sample_entries:
            memory_service.store(entry)

        export_path = str(tmp_path / "export.json")
        count = memory_service.export_to_file(export_path)

        assert Path(export_path).exists()
        assert count == 3

    def test_export_path_as_pathlib(self, memory_service, sample_entries, tmp_path):
        """Test 10: export_to_file accepts filepath as Path object."""
        for entry in sample_entries:
            memory_service.store(entry)

        export_path = tmp_path / "export.json"
        count = memory_service.export_to_file(export_path)

        assert export_path.exists()
        assert count == 3


# ============================================================================
# MemoryService.import_from_file() Tests
# ============================================================================

class TestMemoryServiceImportFromFile:
    """Test MemoryService.import_from_file() method."""

    def test_import_loads_entries_correctly(self, memory_service, sample_entries, tmp_path):
        """Test 1: import_from_file loads entries correctly."""
        # Export entries first
        export_path = tmp_path / "export.json"
        for entry in sample_entries:
            memory_service.store(entry)
        memory_service.export_to_file(export_path)

        # Create new service and import
        fresh_storage = MemoryJsonStorage(tmp_path / "fresh.json")
        fresh_service = MemoryService(fresh_storage)
        imported_count, skipped = fresh_service.import_from_file(export_path)

        assert imported_count == 3
        assert skipped == []

        loaded = fresh_service.retrieve_all()
        assert len(loaded) == 3
        assert loaded[0].operation == "add"
        assert loaded[1].operation == "divide"
        assert loaded[2].operation == "multiply"

    def test_import_appends_to_existing_storage(self, memory_service, sample_entries, tmp_path):
        """Test 2: import appends to existing entries (doesn't replace)."""
        # Store initial entries
        initial_entry = MemoryEntry(
            operation="subtract",
            operand_a=10.0,
            operand_b=3.0,
            result=7.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T09:00:00",
            execution_time_ms=1.0,
            memory_entry_id="initial-id"
        )
        memory_service.store(initial_entry)

        # Export sample entries to a file
        export_path = tmp_path / "export.json"
        temp_service = MemoryService(MemoryJsonStorage(tmp_path / "temp.json"))
        for entry in sample_entries:
            temp_service.store(entry)
        temp_service.export_to_file(export_path)

        # Import into service that already has 1 entry
        imported_count, skipped = memory_service.import_from_file(export_path)

        assert imported_count == 3
        loaded = memory_service.retrieve_all()
        assert len(loaded) == 4  # 1 initial + 3 imported

    def test_import_returns_count_and_skipped_list(self, memory_service, sample_entries, tmp_path):
        """Test 3: import_from_file returns (count, skipped_list) tuple."""
        export_path = tmp_path / "export.json"
        temp_service = MemoryService(MemoryJsonStorage(tmp_path / "temp.json"))
        for entry in sample_entries:
            temp_service.store(entry)
        temp_service.export_to_file(export_path)

        imported_count, skipped = memory_service.import_from_file(export_path)

        assert isinstance(imported_count, int)
        assert isinstance(skipped, list)
        assert imported_count == 3
        assert skipped == []

    def test_import_filenotfound_raises_error(self, memory_service):
        """Test 4: import_from_file raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            memory_service.import_from_file("/nonexistent/path/file.json")

    def test_import_invalid_json_raises_error(self, memory_service, tmp_path):
        """Test 5: import_from_file raises JSONDecodeError for invalid JSON."""
        bad_json_path = tmp_path / "bad.json"
        bad_json_path.write_text("{not valid json")

        with pytest.raises(json.JSONDecodeError):
            memory_service.import_from_file(bad_json_path)

    def test_import_non_array_raises_valueerror(self, memory_service, tmp_path):
        """Test 6: import_from_file raises ValueError if JSON is not an array."""
        non_array_path = tmp_path / "non_array.json"
        non_array_path.write_text('{"operation": "add"}')

        with pytest.raises(ValueError, match="must be an array"):
            memory_service.import_from_file(non_array_path)

    def test_import_empty_array(self, memory_service, tmp_path):
        """Test 7: import_from_file handles empty array."""
        empty_array_path = tmp_path / "empty.json"
        empty_array_path.write_text("[]")

        imported_count, skipped = memory_service.import_from_file(empty_array_path)

        assert imported_count == 0
        assert skipped == []

    def test_import_skip_invalid_true_skips_bad_entries(self, memory_service, tmp_path):
        """Test 8: import_from_file with skip_invalid=True skips malformed entries."""
        import_path = tmp_path / "mixed.json"
        with open(import_path, "w") as f:
            json.dump([
                {
                    "operation": "add",
                    "operand_a": 1.0,
                    "operand_b": 2.0,
                    "result": 3.0,
                    "success": True,
                    "error_message": None,
                    "execution_timestamp": "2026-05-03T10:00:00",
                    "execution_time_ms": 1.0,
                    "memory_entry_id": "id-1"
                },
                {
                    "operation": "invalid_op",
                    "operand_a": "not_a_number",
                },
                {
                    "operation": "multiply",
                    "operand_a": 4.0,
                    "operand_b": 5.0,
                    "result": 20.0,
                    "success": True,
                    "error_message": None,
                    "execution_timestamp": "2026-05-03T10:02:00",
                    "execution_time_ms": 2.0,
                    "memory_entry_id": "id-3"
                },
            ], f)

        imported_count, skipped = memory_service.import_from_file(import_path, skip_invalid=True)

        assert imported_count == 2
        assert len(skipped) == 1
        assert "error" in skipped[0]

    def test_import_skip_invalid_false_fails_on_bad_entry(self, memory_service, tmp_path):
        """Test 9: import_from_file with skip_invalid=False raises on first bad entry."""
        import_path = tmp_path / "mixed.json"
        with open(import_path, "w") as f:
            json.dump([
                {
                    "operation": "add",
                    "operand_a": 1.0,
                    "operand_b": 2.0,
                    "result": 3.0,
                    "success": True,
                    "error_message": None,
                    "execution_timestamp": "2026-05-03T10:00:00",
                    "execution_time_ms": 1.0,
                    "memory_entry_id": "id-1"
                },
                {
                    "operand_a": "bad",
                },
            ], f)

        with pytest.raises(ValueError):
            memory_service.import_from_file(import_path, skip_invalid=False)

    def test_import_non_dict_entry_skip_invalid(self, memory_service, tmp_path):
        """Test 10: import_from_file handles non-dict entries with skip_invalid=True."""
        import_path = tmp_path / "non_dict.json"
        with open(import_path, "w") as f:
            json.dump([
                {
                    "operation": "add",
                    "operand_a": 1.0,
                    "operand_b": 2.0,
                    "result": 3.0,
                    "success": True,
                    "error_message": None,
                    "execution_timestamp": "2026-05-03T10:00:00",
                    "execution_time_ms": 1.0,
                    "memory_entry_id": "id-1"
                },
                "not a dict",
                {
                    "operation": "multiply",
                    "operand_a": 4.0,
                    "operand_b": 5.0,
                    "result": 20.0,
                    "success": True,
                    "error_message": None,
                    "execution_timestamp": "2026-05-03T10:02:00",
                    "execution_time_ms": 2.0,
                    "memory_entry_id": "id-3"
                },
            ], f)

        imported_count, skipped = memory_service.import_from_file(import_path, skip_invalid=True)

        assert imported_count == 2
        assert len(skipped) == 1

    def test_import_skipped_entry_has_data_and_error(self, memory_service, tmp_path):
        """Test 11: skipped entries include both 'data' and 'error' keys."""
        import_path = tmp_path / "bad.json"
        with open(import_path, "w") as f:
            json.dump([
                {
                    "operation": "add",
                    "operand_a": 1.0,
                    "operand_b": 2.0,
                    "result": 3.0,
                    "success": True,
                    "error_message": None,
                    "execution_timestamp": "2026-05-03T10:00:00",
                    "execution_time_ms": 1.0,
                    "memory_entry_id": "id-1"
                },
                {"bad": "entry"},
            ], f)

        imported_count, skipped = memory_service.import_from_file(import_path, skip_invalid=True)

        assert len(skipped) == 1
        assert "data" in skipped[0]
        assert "error" in skipped[0]

    def test_import_round_trip_preserves_data(self, memory_service, sample_entries, tmp_path):
        """Test 12: round-trip export then import preserves all data."""
        # Export
        for entry in sample_entries:
            memory_service.store(entry)

        export_path = tmp_path / "export.json"
        memory_service.export_to_file(export_path)

        # Import into fresh service
        fresh_storage = MemoryJsonStorage(tmp_path / "fresh.json")
        fresh_service = MemoryService(fresh_storage)
        imported_count, skipped = fresh_service.import_from_file(export_path)

        loaded = fresh_service.retrieve_all()

        # Verify all fields preserved
        for original, imported in zip(sample_entries, loaded):
            assert imported.operation == original.operation
            assert imported.operand_a == original.operand_a
            assert imported.operand_b == original.operand_b
            assert imported.result == original.result
            assert imported.success == original.success
            assert imported.error_message == original.error_message
            assert imported.execution_timestamp == original.execution_timestamp
            assert imported.execution_time_ms == original.execution_time_ms
            assert imported.memory_entry_id == original.memory_entry_id

    def test_import_backward_compatibility_old_format(self, memory_service, tmp_path):
        """Test 13: import handles old MemoryEntry format with 'timestamp' field."""
        import_path = tmp_path / "old_format.json"
        with open(import_path, "w") as f:
            json.dump([
                {
                    "operation": "add",
                    "operand_a": 1.0,
                    "operand_b": 2.0,
                    "result": 3.0,
                    "timestamp": "2026-05-03T10:00:00"
                },
            ], f)

        imported_count, skipped = memory_service.import_from_file(import_path)

        assert imported_count == 1
        loaded = memory_service.retrieve_all()
        assert loaded[0].execution_timestamp == "2026-05-03T10:00:00"

    def test_import_missing_optional_fields(self, memory_service, tmp_path):
        """Test 14: import handles entries with missing optional fields."""
        import_path = tmp_path / "minimal.json"
        with open(import_path, "w") as f:
            json.dump([
                {
                    "operation": "add",
                    "operand_a": 1.0,
                    "operand_b": 2.0,
                    "result": 3.0,
                },
            ], f)

        imported_count, skipped = memory_service.import_from_file(import_path)

        assert imported_count == 1
        loaded = memory_service.retrieve_all()
        assert loaded[0].operation == "add"
        assert loaded[0].success is True  # Default inferred
        assert loaded[0].error_message is None  # Default

    def test_import_duplicate_ids_warns(self, memory_service, sample_entries, tmp_path):
        """Test 15: import with duplicate memory_entry_ids still imports both."""
        # Store first entry
        memory_service.store(sample_entries[0])

        # Export duplicate ID
        export_path = tmp_path / "duplicate.json"
        duplicate_entry = MemoryEntry(
            operation="add",
            operand_a=5.0,
            operand_b=6.0,
            result=11.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:03:00",
            execution_time_ms=1.5,
            memory_entry_id="id-1"  # Same ID as sample_entries[0]
        )
        with open(export_path, "w") as f:
            json.dump([duplicate_entry.to_dict()], f)

        # Import should still work (no explicit duplicate checking)
        imported_count, skipped = memory_service.import_from_file(export_path)

        assert imported_count == 1
        # Both entries should be stored (in-memory service doesn't enforce uniqueness)
        loaded = memory_service.retrieve_all()
        assert len(loaded) == 2


# ============================================================================
# CalculatorCLI.export_memory() Tests
# ============================================================================

class TestCalculatorCLIExportMemory:
    """Test CalculatorCLI.export_memory() method."""

    def test_export_memory_with_filepath(self, cli_with_memory_service, sample_entries, capsys):
        """Test 1: export_memory with filepath works."""
        cli, memory_service, tmp_path = cli_with_memory_service

        # Store entries
        for entry in sample_entries:
            memory_service.store(entry)

        export_path = tmp_path / "export.json"
        cli.export_memory(str(export_path))

        captured = capsys.readouterr()
        assert "Successfully exported" in captured.out
        assert "3" in captured.out
        assert export_path.exists()

    def test_export_memory_with_none_prompts_user(self, cli_with_memory_service, sample_entries, capsys):
        """Test 2: export_memory with None filepath prompts user."""
        cli, memory_service, tmp_path = cli_with_memory_service

        for entry in sample_entries:
            memory_service.store(entry)

        export_path = tmp_path / "export.json"

        with patch("builtins.input", return_value=str(export_path)):
            cli.export_memory(None)

        captured = capsys.readouterr()
        assert "Successfully exported" in captured.out
        assert export_path.exists()

    def test_export_memory_prompt_cancelled(self, cli_with_memory_service, capsys):
        """Test 3: export_memory user can cancel by entering empty path."""
        cli, memory_service, tmp_path = cli_with_memory_service

        with patch("builtins.input", return_value=""):
            cli.export_memory(None)

        captured = capsys.readouterr()
        assert "cancelled" in captured.out.lower()

    def test_export_memory_handles_errors_gracefully(self, cli_with_memory_service, capsys):
        """Test 4: export_memory handles errors gracefully."""
        cli, memory_service, tmp_path = cli_with_memory_service

        # Try to export to an invalid path
        cli.export_memory("/dev/null/impossible/path.json")

        captured = capsys.readouterr()
        assert "Error" in captured.out or "error" in captured.out.lower()

    def test_export_memory_without_memory_service(self, capsys):
        """Test 5: export_memory gracefully handles missing memory service."""
        calculator_service = MagicMock()
        cli = CalculatorCLI(calculator_service, memory_service=None)

        cli.export_memory("/some/path.json")

        captured = capsys.readouterr()
        assert "Memory service not available" in captured.out

    def test_export_memory_empty_storage(self, cli_with_memory_service, tmp_path, capsys):
        """Test 6: export_memory with empty storage exports 0 entries."""
        cli, memory_service, _ = cli_with_memory_service

        export_path = tmp_path / "empty.json"
        cli.export_memory(str(export_path))

        captured = capsys.readouterr()
        assert "Successfully exported 0 entries" in captured.out


# ============================================================================
# CalculatorCLI.import_memory() Tests
# ============================================================================

class TestCalculatorCLIImportMemory:
    """Test CalculatorCLI.import_memory() method."""

    def test_import_memory_with_filepath(self, cli_with_memory_service, sample_entries, tmp_path, capsys):
        """Test 1: import_memory with filepath works."""
        cli, memory_service, _ = cli_with_memory_service

        # Create export file
        temp_service = MemoryService(MemoryJsonStorage(tmp_path / "temp.json"))
        for entry in sample_entries:
            temp_service.store(entry)
        export_path = tmp_path / "export.json"
        temp_service.export_to_file(export_path)

        # Import
        cli.import_memory(str(export_path))

        captured = capsys.readouterr()
        assert "Successfully imported 3 entries" in captured.out

    def test_import_memory_with_none_prompts_user(self, cli_with_memory_service, sample_entries, tmp_path, capsys):
        """Test 2: import_memory with None filepath prompts user."""
        cli, memory_service, _ = cli_with_memory_service

        # Create export file
        temp_service = MemoryService(MemoryJsonStorage(tmp_path / "temp.json"))
        for entry in sample_entries:
            temp_service.store(entry)
        export_path = tmp_path / "export.json"
        temp_service.export_to_file(export_path)

        # Import with prompt
        with patch("builtins.input", return_value=str(export_path)):
            cli.import_memory(None)

        captured = capsys.readouterr()
        assert "Successfully imported" in captured.out

    def test_import_memory_prompt_cancelled(self, cli_with_memory_service, capsys):
        """Test 3: import_memory user can cancel by entering empty path."""
        cli, memory_service, _ = cli_with_memory_service

        with patch("builtins.input", return_value=""):
            cli.import_memory(None)

        captured = capsys.readouterr()
        assert "cancelled" in captured.out.lower()

    def test_import_memory_file_not_found(self, cli_with_memory_service, capsys):
        """Test 4: import_memory handles FileNotFoundError."""
        cli, memory_service, _ = cli_with_memory_service

        cli.import_memory("/nonexistent/path.json")

        captured = capsys.readouterr()
        assert "File not found" in captured.out or "Error" in captured.out

    def test_import_memory_invalid_json(self, cli_with_memory_service, tmp_path, capsys):
        """Test 5: import_memory handles invalid JSON."""
        cli, memory_service, _ = cli_with_memory_service

        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{not valid")

        cli.import_memory(str(bad_json))

        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_import_memory_skip_invalid_shows_skipped(self, cli_with_memory_service, tmp_path, capsys):
        """Test 6: import_memory with skip_invalid=True shows skipped entries."""
        cli, memory_service, _ = cli_with_memory_service

        # Create file with mixed entries
        import_path = tmp_path / "mixed.json"
        with open(import_path, "w") as f:
            json.dump([
                {
                    "operation": "add",
                    "operand_a": 1.0,
                    "operand_b": 2.0,
                    "result": 3.0,
                    "success": True,
                    "error_message": None,
                    "execution_timestamp": "2026-05-03T10:00:00",
                    "execution_time_ms": 1.0,
                    "memory_entry_id": "id-1"
                },
                {"bad": "entry"},
            ], f)

        cli.import_memory(str(import_path), skip_invalid=True)

        captured = capsys.readouterr()
        assert "Successfully imported 1 entries" in captured.out
        assert "Skipped 1 invalid entries" in captured.out

    def test_import_memory_without_memory_service(self, capsys):
        """Test 7: import_memory gracefully handles missing memory service."""
        calculator_service = MagicMock()
        cli = CalculatorCLI(calculator_service, memory_service=None)

        cli.import_memory("/some/path.json")

        captured = capsys.readouterr()
        assert "Memory service not available" in captured.out


# ============================================================================
# CLI Flag Tests (--export, --import, --skip-invalid)
# ============================================================================

class TestCLIExportFlag:
    """Test --export CLI flag."""

    def test_export_flag_with_path(self, tmp_path, monkeypatch, capsys):
        """Test 1: --export flag with filepath works."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        # Store test entry
        entry = MemoryEntry(
            operation="add", operand_a=1.0, operand_b=2.0, result=3.0,
            success=True, error_message=None,
            execution_timestamp="2026-05-03T10:00:00", execution_time_ms=1.0,
            memory_entry_id="id-1"
        )
        memory_service.store(entry)

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        export_path = tmp_path / "export.json"
        sys.argv = ["src", "--export", str(export_path)]

        try:
            __main__.main()
        except SystemExit:
            pass

        assert export_path.exists()

    def test_export_flag_without_path_prompts(self, tmp_path, monkeypatch, capsys):
        """Test 2: --export flag without path prompts user."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        entry = MemoryEntry(
            operation="add", operand_a=1.0, operand_b=2.0, result=3.0,
            success=True, error_message=None,
            execution_timestamp="2026-05-03T10:00:00", execution_time_ms=1.0,
            memory_entry_id="id-1"
        )
        memory_service.store(entry)

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        export_path = tmp_path / "export.json"

        with patch("builtins.input", return_value=str(export_path)):
            sys.argv = ["src", "--export"]
            try:
                __main__.main()
            except SystemExit:
                pass

        assert export_path.exists()

    def test_export_flag_creates_file(self, tmp_path, monkeypatch, capsys):
        """Test 3: --export flag creates file with entries."""
        memory_path = tmp_path / "memory.json"
        memory_service = MemoryService(MemoryJsonStorage(memory_path))

        for i in range(2):
            entry = MemoryEntry(
                operation="add", operand_a=float(i), operand_b=float(i+1),
                result=float(2*i+1), success=True, error_message=None,
                execution_timestamp="2026-05-03T10:00:00", execution_time_ms=1.0,
                memory_entry_id=f"id-{i}"
            )
            memory_service.store(entry)

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        export_path = tmp_path / "export.json"
        sys.argv = ["src", "--export", str(export_path)]

        try:
            __main__.main()
        except SystemExit:
            pass

        with open(export_path) as f:
            data = json.load(f)
        assert len(data) == 2


class TestCLIImportFlag:
    """Test --import CLI flag."""

    def test_import_flag_with_path(self, tmp_path, monkeypatch, capsys):
        """Test 1: --import flag with filepath works."""
        memory_path = tmp_path / "memory.json"

        # Create import file
        import_path = tmp_path / "import.json"
        with open(import_path, "w") as f:
            json.dump([
                {
                    "operation": "add", "operand_a": 1.0, "operand_b": 2.0,
                    "result": 3.0, "success": True, "error_message": None,
                    "execution_timestamp": "2026-05-03T10:00:00",
                    "execution_time_ms": 1.0, "memory_entry_id": "id-1"
                },
            ], f)

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--import", str(import_path)]

        try:
            __main__.main()
        except SystemExit:
            pass

        captured = capsys.readouterr()
        assert "Successfully imported 1 entries" in captured.out

    def test_import_flag_without_path_prompts(self, tmp_path, monkeypatch, capsys):
        """Test 2: --import flag without path prompts user."""
        memory_path = tmp_path / "memory.json"

        import_path = tmp_path / "import.json"
        with open(import_path, "w") as f:
            json.dump([
                {
                    "operation": "add", "operand_a": 1.0, "operand_b": 2.0,
                    "result": 3.0, "success": True, "error_message": None,
                    "execution_timestamp": "2026-05-03T10:00:00",
                    "execution_time_ms": 1.0, "memory_entry_id": "id-1"
                },
            ], f)

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        with patch("builtins.input", return_value=str(import_path)):
            sys.argv = ["src", "--import"]
            try:
                __main__.main()
            except SystemExit:
                pass

        captured = capsys.readouterr()
        assert "Successfully imported" in captured.out

    def test_import_flag_with_skip_invalid(self, tmp_path, monkeypatch, capsys):
        """Test 3: --import flag with --skip-invalid skips bad entries."""
        memory_path = tmp_path / "memory.json"

        import_path = tmp_path / "mixed.json"
        with open(import_path, "w") as f:
            json.dump([
                {
                    "operation": "add", "operand_a": 1.0, "operand_b": 2.0,
                    "result": 3.0, "success": True, "error_message": None,
                    "execution_timestamp": "2026-05-03T10:00:00",
                    "execution_time_ms": 1.0, "memory_entry_id": "id-1"
                },
                {"bad": "entry"},
            ], f)

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--import", str(import_path), "--skip-invalid"]

        try:
            __main__.main()
        except SystemExit:
            pass

        captured = capsys.readouterr()
        assert "Successfully imported 1 entries" in captured.out
        assert "Skipped 1 invalid entries" in captured.out

    def test_import_flag_without_skip_invalid_fails(self, tmp_path, monkeypatch, capsys):
        """Test 4: --import flag without --skip-invalid shows error on bad entry."""
        memory_path = tmp_path / "memory.json"

        import_path = tmp_path / "bad.json"
        with open(import_path, "w") as f:
            json.dump([
                {
                    "operation": "add", "operand_a": 1.0, "operand_b": 2.0,
                    "result": 3.0, "success": True, "error_message": None,
                    "execution_timestamp": "2026-05-03T10:00:00",
                    "execution_time_ms": 1.0, "memory_entry_id": "id-1"
                },
                {"incomplete": "entry"},
            ], f)

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--import", str(import_path)]

        try:
            __main__.main()
        except SystemExit:
            pass

        captured = capsys.readouterr()
        assert "Error" in captured.out or "Invalid entry" in captured.out

    def test_import_flag_file_not_found(self, tmp_path, monkeypatch, capsys):
        """Test 5: --import flag handles FileNotFoundError."""
        memory_path = tmp_path / "memory.json"

        def mock_build_memory_service():
            return MemoryService(MemoryJsonStorage(memory_path))

        def mock_build_service():
            return MagicMock()

        monkeypatch.setattr(__main__, "_build_memory_service", mock_build_memory_service)
        monkeypatch.setattr(__main__, "_build_service", mock_build_service)

        sys.argv = ["src", "--import", "/nonexistent/path.json"]

        try:
            __main__.main()
        except SystemExit:
            pass

        captured = capsys.readouterr()
        assert "Error" in captured.out or "not found" in captured.out.lower()


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestImportExportEdgeCases:
    """Test edge cases for import/export functionality."""

    def test_export_import_preserves_precision(self, memory_service, tmp_path):
        """Test: export/import preserves floating point precision."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=3.0,
            result=3.3333333333,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.23456789,
            memory_entry_id="id-1"
        )
        memory_service.store(entry)

        export_path = tmp_path / "export.json"
        memory_service.export_to_file(export_path)

        fresh_storage = MemoryJsonStorage(tmp_path / "fresh.json")
        fresh_service = MemoryService(fresh_storage)
        fresh_service.import_from_file(export_path)

        loaded = fresh_service.retrieve_all()[0]
        assert abs(loaded.result - 3.3333333333) < 0.0001
        assert abs(loaded.execution_time_ms - 1.23456789) < 0.0000001

    def test_export_import_special_characters_in_messages(self, memory_service, tmp_path):
        """Test: export/import handles special characters in error messages."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Error: division by zero! \"quotes\" and 'apostrophes'",
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=0.5,
            memory_entry_id="id-1"
        )
        memory_service.store(entry)

        export_path = tmp_path / "export.json"
        memory_service.export_to_file(export_path)

        fresh_storage = MemoryJsonStorage(tmp_path / "fresh.json")
        fresh_service = MemoryService(fresh_storage)
        fresh_service.import_from_file(export_path)

        loaded = fresh_service.retrieve_all()[0]
        assert loaded.error_message == "Error: division by zero! \"quotes\" and 'apostrophes'"

    def test_export_import_unicode_characters(self, memory_service, tmp_path):
        """Test: export/import handles unicode characters."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00 (日本語)",
            execution_time_ms=1.0,
            memory_entry_id="id-🔥"
        )
        memory_service.store(entry)

        export_path = tmp_path / "export.json"
        memory_service.export_to_file(export_path)

        fresh_storage = MemoryJsonStorage(tmp_path / "fresh.json")
        fresh_service = MemoryService(fresh_storage)
        fresh_service.import_from_file(export_path)

        loaded = fresh_service.retrieve_all()[0]
        assert "日本語" in loaded.execution_timestamp
        assert "🔥" in loaded.memory_entry_id

    def test_export_large_dataset(self, memory_service, tmp_path):
        """Test: export handles large number of entries."""
        # Create 100 entries
        for i in range(100):
            entry = MemoryEntry(
                operation="add",
                operand_a=float(i),
                operand_b=float(i+1),
                result=float(2*i+1),
                success=True,
                error_message=None,
                execution_timestamp="2026-05-03T10:00:00",
                execution_time_ms=0.1 * i,
                memory_entry_id=f"id-{i}"
            )
            memory_service.store(entry)

        export_path = tmp_path / "large.json"
        count = memory_service.export_to_file(export_path)

        assert count == 100
        assert export_path.exists()

        with open(export_path) as f:
            data = json.load(f)
        assert len(data) == 100

    def test_import_large_dataset(self, memory_service, tmp_path):
        """Test: import handles large number of entries."""
        import_path = tmp_path / "large.json"
        large_data = [
            {
                "operation": "add",
                "operand_a": float(i),
                "operand_b": float(i+1),
                "result": float(2*i+1),
                "success": True,
                "error_message": None,
                "execution_timestamp": "2026-05-03T10:00:00",
                "execution_time_ms": 0.1 * i,
                "memory_entry_id": f"id-{i}"
            }
            for i in range(100)
        ]

        with open(import_path, "w") as f:
            json.dump(large_data, f)

        imported_count, skipped = memory_service.import_from_file(import_path)

        assert imported_count == 100
        assert skipped == []
        assert len(memory_service.retrieve_all()) == 100

    def test_export_with_null_values(self, memory_service, tmp_path):
        """Test: export correctly handles null values in optional fields."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=0.5,
            memory_entry_id="id-1"
        )
        memory_service.store(entry)

        export_path = tmp_path / "export.json"
        memory_service.export_to_file(export_path)

        with open(export_path) as f:
            data = json.load(f)

        assert data[0]["result"] is None
        assert data[0]["error_message"] is None
