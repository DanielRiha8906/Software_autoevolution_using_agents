"""Comprehensive tests for ImportExportService."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.services.import_export_service import ImportExportService
from src.storage.json_storage import JsonStorage


_TS = "2026-01-01T00:00:00"
_UUID = "c4ebe8ef-ada9-435b-8cca-b60c868586c6"

# Valid UUIDs for testing
_UUID1 = "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
_UUID2 = "a1b2c3d4-e5f6-4789-0123-456789abcdef"
_UUID3 = "12345678-abcd-ef01-2345-6789abcdef01"
_UUID4 = "f47ac10b-58cc-4372-a567-0e02b2c3d479"


class TestExportHistory:
    """Tests for ImportExportService.export_history()"""

    def test_export_valid_entries(self):
        """Test exporting valid entries to a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            # Create sample entries
            entry1 = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.5, timestamp=_TS, uuid=_UUID)
            entry2 = MemoryEntry("subtract", 10, 4, 6, None, None, execution_time_ms=0.3, timestamp=_TS, uuid="uuid2")
            memory_service.store(entry1)
            memory_service.store(entry2)

            # Export
            export_path = Path(tmpdir) / "export.json"
            result = service.export_history(export_path)

            # Verify result dict
            assert result["exported_count"] == 2
            assert str(export_path) == result["file_path"]

            # Verify file contents
            assert export_path.exists()
            with open(export_path) as f:
                data = json.load(f)
            assert len(data) == 2
            assert data[0]["operation"] == "add"
            assert data[0]["operand_a"] == 3
            assert data[0]["operand_b"] == 5
            assert data[0]["result"] == 8
            assert data[1]["operation"] == "subtract"

    def test_export_empty_history(self):
        """Test exporting when no entries exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            export_path = Path(tmpdir) / "export.json"
            result = service.export_history(export_path)

            assert result["exported_count"] == 0
            assert export_path.exists()
            with open(export_path) as f:
                data = json.load(f)
            assert data == []

    def test_export_with_provided_entries(self):
        """Test exporting specific provided entries (not from memory_service)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            # Create entries but don't store them
            entry1 = MemoryEntry("add", 1, 2, 3, None, None, execution_time_ms=0.1, timestamp=_TS, uuid="uuid1")
            entry2 = MemoryEntry("multiply", 5, 6, 30, None, None, execution_time_ms=0.2, timestamp=_TS, uuid="uuid2")

            # Export the provided entries
            export_path = Path(tmpdir) / "export.json"
            result = service.export_history(export_path, entries=[entry1, entry2])

            assert result["exported_count"] == 2
            with open(export_path) as f:
                data = json.load(f)
            assert len(data) == 2
            assert data[0]["operation"] == "add"

    def test_export_non_json_extension_raises_error(self):
        """Test that exporting to non-.json file raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            export_path = Path(tmpdir) / "export.txt"
            with pytest.raises(ValueError, match="Export file must have .json extension"):
                service.export_history(export_path)

    def test_export_creates_parent_directories(self):
        """Test that export creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            entry = MemoryEntry("add", 1, 2, 3, None, None, execution_time_ms=0.1, timestamp=_TS, uuid="uuid1")
            memory_service.store(entry)

            # Export to nested path that doesn't exist
            export_path = Path(tmpdir) / "subdir" / "nested" / "export.json"
            result = service.export_history(export_path)

            assert export_path.exists()
            assert result["exported_count"] == 1

    def test_export_with_error_entries(self):
        """Test exporting entries with error state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            entry_success = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.1, timestamp=_TS, uuid="uuid1")
            entry_error = MemoryEntry("divide", 5, 0, None, "Division by zero", "ZeroDivisionError",
                                     execution_time_ms=0.1, timestamp=_TS, uuid="uuid2")
            memory_service.store(entry_success)
            memory_service.store(entry_error)

            export_path = Path(tmpdir) / "export.json"
            result = service.export_history(export_path)

            assert result["exported_count"] == 2
            with open(export_path) as f:
                data = json.load(f)
            assert data[0]["error"] is None
            assert data[1]["error"] == "Division by zero"
            assert data[1]["error_type"] == "ZeroDivisionError"

    def test_export_preserves_execution_time(self):
        """Test that export preserves execution_time_ms field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            entry = MemoryEntry("add", 1, 2, 3, None, None, execution_time_ms=1.23, timestamp=_TS, uuid="uuid1")
            memory_service.store(entry)

            export_path = Path(tmpdir) / "export.json"
            service.export_history(export_path)

            with open(export_path) as f:
                data = json.load(f)
            assert data[0]["execution_time_ms"] == 1.23


class TestValidateEntry:
    """Tests for ImportExportService._validate_entry()"""

    def setup_method(self):
        """Set up a service instance for each test."""
        storage = JsonStorage(Path("/tmp/fake.json"))
        memory_service = MemoryService(storage)
        self.service = ImportExportService(memory_service)

    def test_valid_entry(self):
        """Test validation of a valid entry."""
        data = {
            "operation": "add",
            "operand_a": 3.0,
            "operand_b": 5.0,
            "result": 8.0,
            "error": None,
            "error_type": None,
            "execution_time_ms": 0.5,
            "timestamp": "2026-01-01T00:00:00",
            "uuid": "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
        }
        is_valid, error_msg = self.service._validate_entry(data)
        assert is_valid is True
        assert error_msg is None

    def test_missing_required_field(self):
        """Test validation fails when required field is missing."""
        data = {
            "operation": "add",
            "operand_a": 3.0,
            "operand_b": 5.0,
            "result": 8.0,
            "error": None,
            "error_type": None,
            "execution_time_ms": 0.5,
            # missing timestamp
            "uuid": "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
        }
        is_valid, error_msg = self.service._validate_entry(data)
        assert is_valid is False
        assert "timestamp" in error_msg.lower()

    def test_invalid_operation(self):
        """Test validation fails with invalid operation name."""
        data = {
            "operation": "invalid_op",
            "operand_a": 3.0,
            "operand_b": 5.0,
            "result": 8.0,
            "error": None,
            "error_type": None,
            "execution_time_ms": 0.5,
            "timestamp": "2026-01-01T00:00:00",
            "uuid": "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
        }
        is_valid, error_msg = self.service._validate_entry(data)
        assert is_valid is False
        assert "invalid operation" in error_msg.lower()

    def test_non_numeric_operand_a(self):
        """Test validation fails with non-numeric operand_a."""
        data = {
            "operation": "add",
            "operand_a": "not_a_number",
            "operand_b": 5.0,
            "result": 8.0,
            "error": None,
            "error_type": None,
            "execution_time_ms": 0.5,
            "timestamp": "2026-01-01T00:00:00",
            "uuid": "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
        }
        is_valid, error_msg = self.service._validate_entry(data)
        assert is_valid is False
        assert "numeric" in error_msg.lower()

    def test_invalid_result_type(self):
        """Test validation fails when result is not numeric or null."""
        data = {
            "operation": "add",
            "operand_a": 3.0,
            "operand_b": 5.0,
            "result": "not_numeric",
            "error": None,
            "error_type": None,
            "execution_time_ms": 0.5,
            "timestamp": "2026-01-01T00:00:00",
            "uuid": "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
        }
        is_valid, error_msg = self.service._validate_entry(data)
        assert is_valid is False
        assert "result" in error_msg.lower()

    def test_result_none_is_valid(self):
        """Test that result=None (for error cases) is valid."""
        data = {
            "operation": "divide",
            "operand_a": 5.0,
            "operand_b": 0.0,
            "result": None,
            "error": "Division by zero",
            "error_type": "ZeroDivisionError",
            "execution_time_ms": 0.5,
            "timestamp": "2026-01-01T00:00:00",
            "uuid": "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
        }
        is_valid, error_msg = self.service._validate_entry(data)
        assert is_valid is True
        assert error_msg is None

    def test_invalid_execution_time_negative(self):
        """Test validation fails when execution_time_ms is negative."""
        data = {
            "operation": "add",
            "operand_a": 3.0,
            "operand_b": 5.0,
            "result": 8.0,
            "error": None,
            "error_type": None,
            "execution_time_ms": -1.0,
            "timestamp": "2026-01-01T00:00:00",
            "uuid": "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
        }
        is_valid, error_msg = self.service._validate_entry(data)
        assert is_valid is False
        assert "execution_time_ms" in error_msg.lower()

    def test_invalid_timestamp_format(self):
        """Test validation fails with invalid ISO 8601 timestamp."""
        data = {
            "operation": "add",
            "operand_a": 3.0,
            "operand_b": 5.0,
            "result": 8.0,
            "error": None,
            "error_type": None,
            "execution_time_ms": 0.5,
            "timestamp": "not-a-valid-timestamp",
            "uuid": "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
        }
        is_valid, error_msg = self.service._validate_entry(data)
        assert is_valid is False
        assert "timestamp" in error_msg.lower()

    def test_invalid_uuid_format(self):
        """Test validation fails with invalid UUID format."""
        data = {
            "operation": "add",
            "operand_a": 3.0,
            "operand_b": 5.0,
            "result": 8.0,
            "error": None,
            "error_type": None,
            "execution_time_ms": 0.5,
            "timestamp": "2026-01-01T00:00:00",
            "uuid": "not-a-valid-uuid"
        }
        is_valid, error_msg = self.service._validate_entry(data)
        assert is_valid is False
        assert "uuid" in error_msg.lower()

    def test_invalid_error_field_type(self):
        """Test validation fails when error is not string or null."""
        data = {
            "operation": "add",
            "operand_a": 3.0,
            "operand_b": 5.0,
            "result": 8.0,
            "error": 123,  # should be string or None
            "error_type": None,
            "execution_time_ms": 0.5,
            "timestamp": "2026-01-01T00:00:00",
            "uuid": "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
        }
        is_valid, error_msg = self.service._validate_entry(data)
        assert is_valid is False
        assert "error" in error_msg.lower()

    def test_not_a_dict(self):
        """Test validation fails when entry is not a dict."""
        is_valid, error_msg = self.service._validate_entry("not_a_dict")
        assert is_valid is False
        assert "dictionary" in error_msg.lower()

    def test_all_valid_operations(self):
        """Test that all valid operations pass validation."""
        for op in ["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"]:
            data = {
                "operation": op,
                "operand_a": 3.0,
                "operand_b": 5.0,
                "result": 8.0,
                "error": None,
                "error_type": None,
                "execution_time_ms": 0.5,
                "timestamp": "2026-01-01T00:00:00",
                "uuid": "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
            }
            is_valid, error_msg = self.service._validate_entry(data)
            assert is_valid is True, f"Operation {op} should be valid but got error: {error_msg}"


class TestDetectDuplicate:
    """Tests for ImportExportService._detect_duplicate()"""

    def setup_method(self):
        """Set up a service instance for each test."""
        storage = JsonStorage(Path("/tmp/fake.json"))
        memory_service = MemoryService(storage)
        self.service = ImportExportService(memory_service)

    def test_duplicate_by_uuid(self):
        """Test duplicate detection by UUID."""
        uuid = "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
        entry1 = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.1, timestamp="2026-01-01T00:00:00", uuid=uuid)
        entry2 = MemoryEntry("subtract", 10, 4, 6, None, None, execution_time_ms=0.1, timestamp="2026-01-02T00:00:00", uuid=uuid)

        is_dup = self.service._detect_duplicate(entry2, [entry1])
        assert is_dup is True

    def test_duplicate_by_tuple(self):
        """Test duplicate detection by (operation, operand_a, operand_b, timestamp)."""
        ts = "2026-01-01T00:00:00"
        entry1 = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.1, timestamp=ts, uuid="uuid1")
        entry2 = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.1, timestamp=ts, uuid="uuid2")

        is_dup = self.service._detect_duplicate(entry2, [entry1])
        assert is_dup is True

    def test_not_duplicate_different_operands(self):
        """Test that entries with different operands are not duplicates."""
        entry1 = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.1, timestamp="2026-01-01T00:00:00", uuid="uuid1")
        entry2 = MemoryEntry("add", 3, 6, 9, None, None, execution_time_ms=0.1, timestamp="2026-01-01T00:00:00", uuid="uuid2")

        is_dup = self.service._detect_duplicate(entry2, [entry1])
        assert is_dup is False

    def test_not_duplicate_different_operation(self):
        """Test that entries with different operations are not duplicates."""
        ts = "2026-01-01T00:00:00"
        entry1 = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.1, timestamp=ts, uuid="uuid1")
        entry2 = MemoryEntry("subtract", 3, 5, 8, None, None, execution_time_ms=0.1, timestamp=ts, uuid="uuid2")

        is_dup = self.service._detect_duplicate(entry2, [entry1])
        assert is_dup is False

    def test_not_duplicate_different_timestamp(self):
        """Test that entries with different timestamps are not duplicates."""
        entry1 = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.1, timestamp="2026-01-01T00:00:00", uuid="uuid1")
        entry2 = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.1, timestamp="2026-01-02T00:00:00", uuid="uuid2")

        is_dup = self.service._detect_duplicate(entry2, [entry1])
        assert is_dup is False

    def test_duplicate_empty_existing_list(self):
        """Test that entry is not duplicate when existing list is empty."""
        entry = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.1, timestamp="2026-01-01T00:00:00", uuid="uuid1")
        is_dup = self.service._detect_duplicate(entry, [])
        assert is_dup is False

    def test_duplicate_against_multiple_entries(self):
        """Test duplicate detection against multiple existing entries."""
        entry1 = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.1, timestamp="2026-01-01T00:00:00", uuid="uuid1")
        entry2 = MemoryEntry("subtract", 10, 4, 6, None, None, execution_time_ms=0.1, timestamp="2026-01-02T00:00:00", uuid="uuid2")
        entry3 = MemoryEntry("multiply", 2, 3, 6, None, None, execution_time_ms=0.1, timestamp="2026-01-03T00:00:00", uuid="uuid3")

        # Check against entry that matches entry2
        test_entry = MemoryEntry("subtract", 10, 4, 6, None, None, execution_time_ms=0.1, timestamp="2026-01-02T00:00:00", uuid="uuid4")
        is_dup = self.service._detect_duplicate(test_entry, [entry1, entry2, entry3])
        assert is_dup is True


class TestImportHistory:
    """Tests for ImportExportService.import_history()"""

    def test_import_valid_entries_merge_mode(self):
        """Test importing valid entries in merge mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            # Create initial entry
            entry_initial = MemoryEntry("add", 1, 2, 3, None, None, execution_time_ms=0.1, timestamp="2026-01-01T00:00:00", uuid=_UUID1)
            memory_service.store(entry_initial)

            # Create import file
            import_data = [
                {
                    "operation": "subtract",
                    "operand_a": 10.0,
                    "operand_b": 4.0,
                    "result": 6.0,
                    "error": None,
                    "error_type": None,
                    "execution_time_ms": 0.2,
                    "timestamp": "2026-01-02T00:00:00",
                    "uuid": _UUID2
                }
            ]
            import_path = Path(tmpdir) / "import.json"
            with open(import_path, "w") as f:
                json.dump(import_data, f)

            # Import
            result = service.import_history(import_path, mode="merge")

            # Verify result
            assert result["imported_count"] == 1
            assert result["skipped_count"] == 0
            assert result["duplicates_count"] == 0
            assert result["invalid_count"] == 0

            # Verify all entries are in storage
            all_entries = memory_service.retrieve()
            assert len(all_entries) == 2
            assert all_entries[0].operation == "add"
            assert all_entries[1].operation == "subtract"

    def test_import_valid_entries_replace_mode(self):
        """Test importing valid entries in replace mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            # Create initial entries
            entry1 = MemoryEntry("add", 1, 2, 3, None, None, execution_time_ms=0.1, timestamp="2026-01-01T00:00:00", uuid=_UUID1)
            entry2 = MemoryEntry("subtract", 10, 4, 6, None, None, execution_time_ms=0.1, timestamp="2026-01-02T00:00:00", uuid=_UUID2)
            memory_service.store(entry1)
            memory_service.store(entry2)

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

            # Import in replace mode
            result = service.import_history(import_path, mode="replace")

            # Verify result
            assert result["imported_count"] == 1

            # Verify only new entries are in storage
            all_entries = memory_service.retrieve()
            assert len(all_entries) == 1
            assert all_entries[0].operation == "multiply"

    def test_import_skips_invalid_entries(self):
        """Test that invalid entries are skipped and reported."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            # Create import file with mix of valid and invalid entries
            import_data = [
                {
                    "operation": "add",
                    "operand_a": 3.0,
                    "operand_b": 5.0,
                    "result": 8.0,
                    "error": None,
                    "error_type": None,
                    "execution_time_ms": 0.1,
                    "timestamp": "2026-01-01T00:00:00",
                    "uuid": _UUID1
                },
                {
                    "operation": "invalid_op",
                    "operand_a": 3.0,
                    "operand_b": 5.0,
                    "result": 8.0,
                    "error": None,
                    "error_type": None,
                    "execution_time_ms": 0.1,
                    "timestamp": "2026-01-02T00:00:00",
                    "uuid": _UUID2
                },
                {
                    "operation": "subtract",
                    "operand_a": 10.0,
                    "operand_b": 4.0,
                    "result": 6.0,
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

            # Import
            result = service.import_history(import_path, mode="merge")

            # Verify result
            assert result["imported_count"] == 2
            assert result["skipped_count"] == 1
            assert result["invalid_count"] == 1
            assert result["duplicates_count"] == 0
            assert len(result["skipped_entries"]) == 1
            assert result["skipped_entries"][0]["operation"] == "invalid_op"

            # Verify only valid entries are stored
            all_entries = memory_service.retrieve()
            assert len(all_entries) == 2
            assert all_entries[0].operation == "add"
            assert all_entries[1].operation == "subtract"

    def test_import_skips_duplicates(self):
        """Test that duplicate entries are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            # Create initial entry
            uuid = "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
            entry = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.1, timestamp="2026-01-01T00:00:00", uuid=uuid)
            memory_service.store(entry)

            # Create import file with duplicate
            import_data = [
                {
                    "operation": "add",
                    "operand_a": 3.0,
                    "operand_b": 5.0,
                    "result": 8.0,
                    "error": None,
                    "error_type": None,
                    "execution_time_ms": 0.1,
                    "timestamp": "2026-01-01T00:00:00",
                    "uuid": uuid
                }
            ]
            import_path = Path(tmpdir) / "import.json"
            with open(import_path, "w") as f:
                json.dump(import_data, f)

            # Import
            result = service.import_history(import_path, mode="merge")

            # Verify result
            assert result["imported_count"] == 0
            assert result["skipped_count"] == 1
            assert result["duplicates_count"] == 1
            assert result["invalid_count"] == 0

            # Verify only one entry is in storage
            all_entries = memory_service.retrieve()
            assert len(all_entries) == 1

    def test_import_non_json_extension_raises_error(self):
        """Test that importing from non-.json file raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            import_path = Path(tmpdir) / "import.txt"
            with pytest.raises(ValueError, match="Import file must have .json extension"):
                service.import_history(import_path)

    def test_import_missing_file_raises_error(self):
        """Test that importing from missing file raises OSError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            import_path = Path(tmpdir) / "nonexistent.json"
            with pytest.raises(OSError, match="Import file not found"):
                service.import_history(import_path)

    def test_import_invalid_json_raises_error(self):
        """Test that importing malformed JSON raises JSONDecodeError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            import_path = Path(tmpdir) / "import.json"
            with open(import_path, "w") as f:
                f.write("{invalid json")

            with pytest.raises(Exception):  # JSONDecodeError
                service.import_history(import_path)

    def test_import_not_array_raises_error(self):
        """Test that importing non-array JSON raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            import_path = Path(tmpdir) / "import.json"
            with open(import_path, "w") as f:
                json.dump({"not": "an array"}, f)

            with pytest.raises(ValueError, match="must contain a JSON array"):
                service.import_history(import_path)

    def test_import_empty_file(self):
        """Test importing from empty JSON array."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            import_path = Path(tmpdir) / "import.json"
            with open(import_path, "w") as f:
                json.dump([], f)

            result = service.import_history(import_path, mode="merge")

            assert result["imported_count"] == 0
            assert result["skipped_count"] == 0

    def test_import_round_trip(self):
        """Test that export followed by import preserves data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create original data
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            entry1 = MemoryEntry("add", 3, 5, 8, None, None, execution_time_ms=0.5, timestamp="2026-01-01T00:00:00", uuid=_UUID1)
            entry2 = MemoryEntry("divide", 10, 2, 5, None, None, execution_time_ms=0.3, timestamp="2026-01-02T00:00:00", uuid=_UUID2)
            memory_service.store(entry1)
            memory_service.store(entry2)

            # Export
            export_path = Path(tmpdir) / "export.json"
            service.export_history(export_path)

            # Clear storage and import
            storage._write_raw([])
            import_result = service.import_history(export_path, mode="merge")

            # Verify
            assert import_result["imported_count"] == 2
            all_entries = memory_service.retrieve()
            assert len(all_entries) == 2
            assert all_entries[0].operation == "add"
            assert all_entries[0].operand_a == 3
            assert all_entries[0].operand_b == 5
            assert all_entries[0].result == 8
            assert all_entries[0].execution_time_ms == 0.5

    def test_import_mixed_valid_invalid_duplicates(self):
        """Test import with mix of valid, invalid, and duplicate entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            # Create initial entry
            entry_initial = MemoryEntry("add", 1, 2, 3, None, None, execution_time_ms=0.1, timestamp="2026-01-01T00:00:00", uuid=_UUID1)
            memory_service.store(entry_initial)

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
                },
                {
                    "operation": "invalid_op",
                    "operand_a": 5.0,
                    "operand_b": 3.0,
                    "result": 8.0,
                    "error": None,
                    "error_type": None,
                    "execution_time_ms": 0.1,
                    "timestamp": "2026-01-03T00:00:00",
                    "uuid": _UUID3
                },
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
                },
                {
                    "operation": "multiply",
                    "operand_a": 5.0,
                    "operand_b": 3.0,
                    "result": 15.0,
                    "error": None,
                    "error_type": None,
                    "execution_time_ms": 0.1,
                    "timestamp": "2026-01-04T00:00:00",
                    "uuid": _UUID4
                }
            ]
            import_path = Path(tmpdir) / "import.json"
            with open(import_path, "w") as f:
                json.dump(import_data, f)

            # Import
            result = service.import_history(import_path, mode="merge")

            # Verify result
            assert result["imported_count"] == 2  # subtract and multiply
            assert result["skipped_count"] == 2  # invalid_op and duplicate add
            assert result["duplicates_count"] == 1
            assert result["invalid_count"] == 1

            # Verify storage
            all_entries = memory_service.retrieve()
            assert len(all_entries) == 3  # initial + 2 imported

    def test_import_backward_compatibility_missing_optional_fields(self):
        """Test that import handles entries with missing optional fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(storage_path)
            memory_service = MemoryService(storage)
            service = ImportExportService(memory_service)

            # Create import file with old format (missing some optional fields)
            import_data = [
                {
                    "operation": "add",
                    "operand_a": 3.0,
                    "operand_b": 5.0,
                    "result": 8.0,
                    "error": None,
                    "error_type": None,
                    "execution_time_ms": 0.0,
                    "timestamp": "2026-01-01T00:00:00",
                    "uuid": "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
                }
            ]
            import_path = Path(tmpdir) / "import.json"
            with open(import_path, "w") as f:
                json.dump(import_data, f)

            # Import should succeed
            result = service.import_history(import_path, mode="merge")

            assert result["imported_count"] == 1
            assert result["skipped_count"] == 0
