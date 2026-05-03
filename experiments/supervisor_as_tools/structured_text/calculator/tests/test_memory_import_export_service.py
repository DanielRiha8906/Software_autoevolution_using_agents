import json
import pytest
from pathlib import Path
from src.models.memory_entry import MemoryEntry
from src.services.memory_import_export_service import MemoryImportExportService


@pytest.fixture
def service():
    return MemoryImportExportService()


@pytest.fixture
def sample_entries():
    """Create sample MemoryEntry objects for testing."""
    return [
        MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            success=True,
            result=8,
            error_message=None,
            timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.5,
            id="entry-1"
        ),
        MemoryEntry(
            operation="divide",
            operand_a=10,
            operand_b=0,
            success=False,
            result=None,
            error_message="Division by zero",
            timestamp="2026-05-03T10:01:00",
            execution_time_ms=0.8,
            id="entry-2"
        ),
        MemoryEntry(
            operation="multiply",
            operand_a=4,
            operand_b=5,
            success=True,
            result=20,
            error_message=None,
            timestamp="2026-05-03T10:02:00",
            execution_time_ms=1.2,
            id="entry-3"
        ),
    ]


class TestValidateEntry:
    """Test the validate_entry method."""

    def test_valid_entry_minimal(self, service):
        """Valid entry with only required fields."""
        entry = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "success": True
        }
        assert service.validate_entry(entry) is True

    def test_valid_entry_full(self, service):
        """Valid entry with all fields."""
        entry = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "success": True,
            "result": 8,
            "error_message": None,
            "timestamp": "2026-05-03T10:00:00",
            "execution_time_ms": 1.5,
            "id": "entry-1"
        }
        assert service.validate_entry(entry) is True

    def test_missing_required_field_operation(self, service):
        """Missing required 'operation' field."""
        entry = {
            "operand_a": 3,
            "operand_b": 5,
            "success": True
        }
        assert service.validate_entry(entry) is False

    def test_missing_required_field_operand_a(self, service):
        """Missing required 'operand_a' field."""
        entry = {
            "operation": "add",
            "operand_b": 5,
            "success": True
        }
        assert service.validate_entry(entry) is False

    def test_missing_required_field_operand_b(self, service):
        """Missing required 'operand_b' field."""
        entry = {
            "operation": "add",
            "operand_a": 3,
            "success": True
        }
        assert service.validate_entry(entry) is False

    def test_missing_required_field_success(self, service):
        """Missing required 'success' field."""
        entry = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5
        }
        assert service.validate_entry(entry) is False

    def test_invalid_operation_not_string(self, service):
        """'operation' field is not a string."""
        entry = {
            "operation": 123,
            "operand_a": 3,
            "operand_b": 5,
            "success": True
        }
        assert service.validate_entry(entry) is False

    def test_invalid_operand_a_not_numeric(self, service):
        """'operand_a' is not numeric."""
        entry = {
            "operation": "add",
            "operand_a": "abc",
            "operand_b": 5,
            "success": True
        }
        assert service.validate_entry(entry) is False

    def test_invalid_operand_b_not_numeric(self, service):
        """'operand_b' is not numeric."""
        entry = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": "xyz",
            "success": True
        }
        assert service.validate_entry(entry) is False

    def test_invalid_success_not_boolean(self, service):
        """'success' is not a boolean."""
        entry = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "success": "yes"
        }
        assert service.validate_entry(entry) is False

    def test_operand_a_float_valid(self, service):
        """'operand_a' can be a float."""
        entry = {
            "operation": "divide",
            "operand_a": 3.5,
            "operand_b": 2,
            "success": True
        }
        assert service.validate_entry(entry) is True

    def test_operand_b_float_valid(self, service):
        """'operand_b' can be a float."""
        entry = {
            "operation": "divide",
            "operand_a": 7,
            "operand_b": 2.5,
            "success": True
        }
        assert service.validate_entry(entry) is True

    def test_extra_fields_allowed(self, service):
        """Entry with extra fields still validates."""
        entry = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "success": True,
            "extra_field": "ignored"
        }
        assert service.validate_entry(entry) is True


class TestFindDuplicates:
    """Test the find_duplicates method."""

    def test_no_duplicates(self, service):
        """No duplicates found."""
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=3,
                operand_b=5,
                success=True,
                timestamp="2026-05-03T10:00:00"
            ),
        ]
        existing = [
            MemoryEntry(
                operation="add",
                operand_a=10,
                operand_b=20,
                success=True,
                timestamp="2026-05-03T10:01:00"
            ),
        ]
        duplicates = service.find_duplicates(entries, existing)
        assert len(duplicates) == 0

    def test_exact_duplicate(self, service):
        """Duplicate with same operation, operands, and timestamp."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            success=True,
            timestamp="2026-05-03T10:00:00",
            id="entry-1"
        )
        entries = [entry]
        existing = [entry]
        duplicates = service.find_duplicates(entries, existing)
        assert "entry-1" in duplicates

    def test_multiple_duplicates(self, service):
        """Multiple duplicates detected."""
        entry1 = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            success=True,
            timestamp="2026-05-03T10:00:00",
            id="entry-1"
        )
        entry2 = MemoryEntry(
            operation="multiply",
            operand_a=4,
            operand_b=5,
            success=True,
            timestamp="2026-05-03T10:01:00",
            id="entry-2"
        )
        duplicates = service.find_duplicates([entry1, entry2], [entry1, entry2])
        assert "entry-1" in duplicates
        assert "entry-2" in duplicates

    def test_same_operands_different_timestamp_not_duplicate(self, service):
        """Same operands but different timestamp is not a duplicate."""
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=3,
                operand_b=5,
                success=True,
                timestamp="2026-05-03T10:00:00",
                id="entry-1"
            ),
        ]
        existing = [
            MemoryEntry(
                operation="add",
                operand_a=3,
                operand_b=5,
                success=True,
                timestamp="2026-05-03T10:01:00",
                id="entry-2"
            ),
        ]
        duplicates = service.find_duplicates(entries, existing)
        assert len(duplicates) == 0

    def test_empty_entries_list(self, service):
        """Empty entries list produces no duplicates."""
        existing = [
            MemoryEntry(
                operation="add",
                operand_a=3,
                operand_b=5,
                success=True,
                timestamp="2026-05-03T10:00:00"
            ),
        ]
        duplicates = service.find_duplicates([], existing)
        assert len(duplicates) == 0

    def test_empty_existing_list(self, service):
        """Empty existing list produces no duplicates."""
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=3,
                operand_b=5,
                success=True,
                timestamp="2026-05-03T10:00:00",
                id="entry-1"
            ),
        ]
        duplicates = service.find_duplicates(entries, [])
        assert len(duplicates) == 0


class TestExportMemory:
    """Test the export_memory method."""

    def test_export_single_entry(self, service, tmp_path, sample_entries):
        """Export a single entry to JSON file."""
        filepath = tmp_path / "export.json"
        count = service.export_memory(filepath, sample_entries[:1])
        assert count == 1
        assert filepath.exists()

    def test_export_multiple_entries(self, service, tmp_path, sample_entries):
        """Export multiple entries to JSON file."""
        filepath = tmp_path / "export.json"
        count = service.export_memory(filepath, sample_entries)
        assert count == 3
        assert filepath.exists()

    def test_export_empty_list(self, service, tmp_path):
        """Export empty list produces empty JSON array."""
        filepath = tmp_path / "export.json"
        count = service.export_memory(filepath, [])
        assert count == 0
        with open(filepath) as f:
            data = json.load(f)
        assert data == []

    def test_export_json_format(self, service, tmp_path, sample_entries):
        """Exported JSON is valid and contains expected fields."""
        filepath = tmp_path / "export.json"
        service.export_memory(filepath, sample_entries[:1])
        with open(filepath) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["operation"] == "add"
        assert data[0]["operand_a"] == 3
        assert data[0]["operand_b"] == 5
        assert data[0]["result"] == 8
        assert data[0]["success"] is True

    def test_export_preserves_all_fields(self, service, tmp_path, sample_entries):
        """All fields are preserved in export."""
        filepath = tmp_path / "export.json"
        service.export_memory(filepath, sample_entries)
        with open(filepath) as f:
            data = json.load(f)
        # Check second entry (failure case)
        entry = data[1]
        assert entry["operation"] == "divide"
        assert entry["operand_a"] == 10
        assert entry["operand_b"] == 0
        assert entry["success"] is False
        assert entry["error_message"] == "Division by zero"
        assert entry["execution_time_ms"] == 0.8

    def test_export_creates_parent_directories(self, service, tmp_path):
        """Export creates parent directories if they don't exist."""
        filepath = tmp_path / "deep" / "nested" / "path" / "export.json"
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            success=True,
            result=3,
            timestamp="2026-05-03T10:00:00"
        )
        service.export_memory(filepath, [entry])
        assert filepath.exists()

    def test_export_overwrites_existing_file(self, service, tmp_path):
        """Export overwrites existing file."""
        filepath = tmp_path / "export.json"
        entry1 = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            success=True,
            result=3,
            timestamp="2026-05-03T10:00:00"
        )
        entry2 = MemoryEntry(
            operation="subtract",
            operand_a=5,
            operand_b=3,
            success=True,
            result=2,
            timestamp="2026-05-03T10:01:00"
        )
        service.export_memory(filepath, [entry1])
        service.export_memory(filepath, [entry2])
        with open(filepath) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["operation"] == "subtract"


class TestImportFromFile:
    """Test the import_from_file method."""

    def test_import_single_valid_entry(self, service, tmp_path):
        """Import a single valid entry from JSON file."""
        filepath = tmp_path / "import.json"
        data = [{
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "success": True,
            "result": 8,
            "timestamp": "2026-05-03T10:00:00",
            "id": "entry-1"
        }]
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, skipped, duplicates = service.import_from_file(filepath)
        assert len(entries) == 1
        assert entries[0].operation == "add"
        assert skipped == 0
        assert duplicates == 0

    def test_import_multiple_valid_entries(self, service, tmp_path, sample_entries):
        """Import multiple valid entries."""
        filepath = tmp_path / "import.json"
        records = [entry.to_dict() for entry in sample_entries]
        with open(filepath, "w") as f:
            json.dump(records, f)

        entries, skipped, duplicates = service.import_from_file(filepath)
        assert len(entries) == 3
        assert skipped == 0
        assert duplicates == 0

    def test_import_preserves_all_fields(self, service, tmp_path):
        """All fields are preserved during import."""
        filepath = tmp_path / "import.json"
        data = [{
            "operation": "divide",
            "operand_a": 10,
            "operand_b": 0,
            "success": False,
            "error_message": "Division by zero",
            "result": None,
            "timestamp": "2026-05-03T10:00:00",
            "execution_time_ms": 0.8,
            "id": "entry-1"
        }]
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, _, _ = service.import_from_file(filepath)
        entry = entries[0]
        assert entry.operation == "divide"
        assert entry.operand_a == 10
        assert entry.operand_b == 0
        assert entry.success is False
        assert entry.error_message == "Division by zero"
        assert entry.execution_time_ms == 0.8

    def test_import_skips_invalid_entries(self, service, tmp_path):
        """Invalid entries are skipped."""
        filepath = tmp_path / "import.json"
        data = [
            {
                "operation": "add",
                "operand_a": 3,
                "operand_b": 5,
                "success": True
            },
            {
                "operation": "invalid",
                "operand_a": "not_numeric",
                "operand_b": 5,
                "success": True
            },
            {
                "operation": "multiply",
                "operand_a": 4,
                "operand_b": 5,
                "success": True
            }
        ]
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, skipped, _ = service.import_from_file(filepath)
        assert len(entries) == 2
        assert skipped == 1

    def test_import_missing_file_raises(self, service, tmp_path):
        """Missing file raises FileNotFoundError."""
        filepath = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError, match="File not found"):
            service.import_from_file(filepath)

    def test_import_invalid_json_raises(self, service, tmp_path):
        """Invalid JSON raises ValueError."""
        filepath = tmp_path / "bad.json"
        filepath.write_text("{ invalid json }")
        with pytest.raises(ValueError, match="Invalid JSON"):
            service.import_from_file(filepath)

    def test_import_non_list_json_raises(self, service, tmp_path):
        """JSON that is not a list raises ValueError."""
        filepath = tmp_path / "object.json"
        with open(filepath, "w") as f:
            json.dump({"key": "value"}, f)
        with pytest.raises(ValueError, match="JSON root must be a list"):
            service.import_from_file(filepath)

    def test_import_non_dict_entries_skipped(self, service, tmp_path):
        """Non-dict entries in list are skipped."""
        filepath = tmp_path / "mixed.json"
        data = [
            {
                "operation": "add",
                "operand_a": 3,
                "operand_b": 5,
                "success": True
            },
            "string_entry",
            123,
            {
                "operation": "subtract",
                "operand_a": 10,
                "operand_b": 5,
                "success": True
            }
        ]
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, skipped, _ = service.import_from_file(filepath)
        assert len(entries) == 2
        assert skipped == 2

    def test_import_missing_required_field_skipped(self, service, tmp_path):
        """Entry missing required field is skipped."""
        filepath = tmp_path / "incomplete.json"
        data = [
            {
                "operation": "add",
                "operand_a": 3,
                "success": True
            },
            {
                "operation": "multiply",
                "operand_a": 4,
                "operand_b": 5,
                "success": True
            }
        ]
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, skipped, _ = service.import_from_file(filepath)
        assert len(entries) == 1
        assert skipped == 1

    def test_import_empty_file(self, service, tmp_path):
        """Importing empty JSON array returns empty list."""
        filepath = tmp_path / "empty.json"
        with open(filepath, "w") as f:
            json.dump([], f)

        entries, skipped, duplicates = service.import_from_file(filepath)
        assert len(entries) == 0
        assert skipped == 0
        assert duplicates == 0

    def test_import_returns_tuple(self, service, tmp_path):
        """Import returns tuple with 3 elements."""
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump([], f)

        result = service.import_from_file(filepath)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_import_entry_has_correct_type(self, service, tmp_path):
        """Imported entries are MemoryEntry instances."""
        filepath = tmp_path / "import.json"
        data = [{
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "success": True,
            "result": 8,
            "timestamp": "2026-05-03T10:00:00"
        }]
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, _, _ = service.import_from_file(filepath)
        assert len(entries) == 1
        assert isinstance(entries[0], MemoryEntry)


class TestRoundTrip:
    """Test exporting and then importing data."""

    def test_round_trip_preserves_data(self, service, tmp_path, sample_entries):
        """Data exported and re-imported matches original."""
        export_path = tmp_path / "export.json"
        service.export_memory(export_path, sample_entries)

        imported, skipped, duplicates = service.import_from_file(export_path)
        assert len(imported) == len(sample_entries)
        assert skipped == 0
        assert duplicates == 0

        for original, imported_entry in zip(sample_entries, imported):
            assert imported_entry.operation == original.operation
            assert imported_entry.operand_a == original.operand_a
            assert imported_entry.operand_b == original.operand_b
            assert imported_entry.success == original.success
            assert imported_entry.result == original.result
            assert imported_entry.error_message == original.error_message

    def test_round_trip_with_empty_list(self, service, tmp_path):
        """Round trip with empty list."""
        export_path = tmp_path / "export.json"
        service.export_memory(export_path, [])

        imported, skipped, duplicates = service.import_from_file(export_path)
        assert len(imported) == 0
        assert skipped == 0
        assert duplicates == 0
