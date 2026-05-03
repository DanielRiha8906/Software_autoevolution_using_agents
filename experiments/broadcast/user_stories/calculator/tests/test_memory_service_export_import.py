import pytest
from pathlib import Path
from src.models.memory_entry import ResultEntry, ErrorEntry, _reset_id_counter
from src.services.memory_service import MemoryService
from src.storage.json_storage import JsonStorage


class TestMemoryServiceExport:
    @pytest.fixture
    def memory_service(self, tmp_path):
        _reset_id_counter()
        storage_path = tmp_path / "storage.json"
        return MemoryService(JsonStorage(storage_path))

    def test_export_empty_history(self, memory_service, tmp_path):
        export_path = tmp_path / "export.json"
        memory_service.export_history(export_path)
        assert export_path.exists()
        # Check file is valid JSON with empty list
        import json
        with open(export_path) as f:
            data = json.load(f)
        assert data == []

    def test_export_with_entries(self, memory_service, tmp_path):
        # Add entries to storage
        e1 = ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00")
        e2 = ErrorEntry(operation="divide", operands=[5, 0], error_message="Division by zero", timestamp="2026-01-01T01:00:00")
        memory_service.store(e1)
        memory_service.store(e2)

        # Export
        export_path = tmp_path / "export.json"
        memory_service.export_history(export_path)
        assert export_path.exists()

        # Verify exported content
        import json
        with open(export_path) as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["type"] == "result"
        assert data[1]["type"] == "error"


class TestMemoryServiceImport:
    @pytest.fixture
    def memory_service(self, tmp_path):
        _reset_id_counter()
        storage_path = tmp_path / "storage.json"
        return MemoryService(JsonStorage(storage_path))

    def test_import_empty_file(self, memory_service, tmp_path):
        import json
        import_path = tmp_path / "import.json"
        with open(import_path, "w") as f:
            json.dump([], f)

        count, errors = memory_service.import_history(import_path)
        assert count == 0
        assert len(errors) == 0

    def test_import_result_entries(self, memory_service, tmp_path):
        import json
        import_path = tmp_path / "import.json"
        data = [
            {
                "type": "result",
                "entry_id": 1,
                "operation": "add",
                "operands": [1, 2],
                "result": 3,
                "timestamp": "2026-01-01T00:00:00",
                "execution_time_ms": 1.0,
            },
            {
                "type": "result",
                "entry_id": 2,
                "operation": "multiply",
                "operands": [3, 4],
                "result": 12,
                "timestamp": "2026-01-01T01:00:00",
                "execution_time_ms": 0.5,
            },
        ]
        with open(import_path, "w") as f:
            json.dump(data, f)

        count, errors = memory_service.import_history(import_path)
        assert count == 2
        assert len(errors) == 0

        # Verify entries are stored
        entries = memory_service.retrieve()
        assert len(entries) == 2
        assert entries[0].operation == "add"
        assert entries[1].operation == "multiply"

    def test_import_error_entries(self, memory_service, tmp_path):
        import json
        import_path = tmp_path / "import.json"
        data = [
            {
                "type": "error",
                "entry_id": 1,
                "operation": "divide",
                "operands": [5, 0],
                "error_message": "Division by zero",
                "timestamp": "2026-01-01T00:00:00",
                "execution_time_ms": 0.1,
            },
        ]
        with open(import_path, "w") as f:
            json.dump(data, f)

        count, errors = memory_service.import_history(import_path)
        assert count == 1
        assert len(errors) == 0

        # Verify entry is stored
        entries = memory_service.retrieve()
        assert len(entries) == 1
        assert entries[0].operation == "divide"
        assert isinstance(entries[0], ErrorEntry)

    def test_import_mixed_entries(self, memory_service, tmp_path):
        import json
        import_path = tmp_path / "import.json"
        data = [
            {
                "type": "result",
                "entry_id": 1,
                "operation": "add",
                "operands": [1, 2],
                "result": 3,
                "timestamp": "2026-01-01T00:00:00",
                "execution_time_ms": 1.0,
            },
            {
                "type": "error",
                "entry_id": 2,
                "operation": "divide",
                "operands": [5, 0],
                "error_message": "Division by zero",
                "timestamp": "2026-01-01T01:00:00",
                "execution_time_ms": 0.1,
            },
        ]
        with open(import_path, "w") as f:
            json.dump(data, f)

        count, errors = memory_service.import_history(import_path)
        assert count == 2
        assert len(errors) == 0

        # Verify entries are stored
        entries = memory_service.retrieve()
        assert len(entries) == 2
        assert isinstance(entries[0], ResultEntry)
        assert isinstance(entries[1], ErrorEntry)

    def test_import_skip_duplicates(self, memory_service, tmp_path):
        import json

        # Add initial entries
        e1 = ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00", entry_id=1)
        memory_service.store(e1)

        # Try to import with duplicate ID
        import_path = tmp_path / "import.json"
        data = [
            {
                "type": "result",
                "entry_id": 1,  # duplicate
                "operation": "multiply",
                "operands": [3, 4],
                "result": 12,
                "timestamp": "2026-01-01T01:00:00",
                "execution_time_ms": 0.5,
            },
            {
                "type": "result",
                "entry_id": 2,
                "operation": "divide",
                "operands": [10, 2],
                "result": 5,
                "timestamp": "2026-01-01T02:00:00",
                "execution_time_ms": 0.2,
            },
        ]
        with open(import_path, "w") as f:
            json.dump(data, f)

        count, errors = memory_service.import_history(import_path, overwrite=False)
        assert count == 1  # Only one entry imported (the non-duplicate)
        assert len(errors) == 1  # One duplicate skipped
        assert "Duplicate" in errors[0]

        # Verify only new entry is stored
        entries = memory_service.retrieve()
        assert len(entries) == 2  # Original + new
        assert entries[0].operation == "add"
        assert entries[1].operation == "divide"

    def test_import_overwrite_duplicates(self, memory_service, tmp_path):
        import json

        # Add initial entries
        e1 = ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00", entry_id=1)
        memory_service.store(e1)

        # Try to import with duplicate ID but overwrite enabled
        import_path = tmp_path / "import.json"
        data = [
            {
                "type": "result",
                "entry_id": 1,  # duplicate
                "operation": "multiply",
                "operands": [3, 4],
                "result": 12,
                "timestamp": "2026-01-01T01:00:00",
                "execution_time_ms": 0.5,
            },
            {
                "type": "result",
                "entry_id": 2,
                "operation": "divide",
                "operands": [10, 2],
                "result": 5,
                "timestamp": "2026-01-01T02:00:00",
                "execution_time_ms": 0.2,
            },
        ]
        with open(import_path, "w") as f:
            json.dump(data, f)

        count, errors = memory_service.import_history(import_path, overwrite=True)
        assert count == 2  # Both entries imported
        assert len(errors) == 0  # No errors

        # Verify both entries are stored
        entries = memory_service.retrieve()
        assert len(entries) == 3  # Original + 2 new

    def test_import_invalid_entries_partially_skipped(self, memory_service, tmp_path):
        import json

        import_path = tmp_path / "import.json"
        data = [
            {
                "type": "result",
                "entry_id": 1,
                "operation": "add",
                "operands": [1, 2],
                "result": 3,
                "timestamp": "2026-01-01T00:00:00",
                "execution_time_ms": 1.0,
            },
            {
                "type": "unknown",  # invalid
                "entry_id": 2,
            },
            {
                "type": "result",
                "entry_id": 3,
                "operation": "multiply",
                "operands": [3, 4],
                "result": 12,
                "timestamp": "2026-01-01T02:00:00",
                "execution_time_ms": 0.5,
            },
        ]
        with open(import_path, "w") as f:
            json.dump(data, f)

        count, errors = memory_service.import_history(import_path)
        assert count == 2  # Valid entries imported
        assert len(errors) == 1  # Invalid entry skipped

        # Verify valid entries are stored
        entries = memory_service.retrieve()
        assert len(entries) == 2
        assert entries[0].operation == "add"
        assert entries[1].operation == "multiply"

    def test_import_file_not_found(self, memory_service, tmp_path):
        with pytest.raises(IOError, match="File not found"):
            memory_service.import_history(tmp_path / "nonexistent.json")

    def test_import_invalid_json(self, memory_service, tmp_path):
        import_path = tmp_path / "invalid.json"
        with open(import_path, "w") as f:
            f.write("not valid json {")

        with pytest.raises(ValueError, match="Invalid JSON format"):
            memory_service.import_history(import_path)


class TestMemoryServiceExportImportRoundtrip:
    @pytest.fixture
    def memory_service(self, tmp_path):
        _reset_id_counter()
        storage_path = tmp_path / "storage.json"
        return MemoryService(JsonStorage(storage_path))

    def test_export_import_roundtrip(self, memory_service, tmp_path):
        # Add entries to service
        e1 = ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00")
        e2 = ErrorEntry(operation="divide", operands=[5, 0], error_message="Division by zero", timestamp="2026-01-01T01:00:00")
        e3 = ResultEntry(operation="multiply", operands=[3, 4], result=12, timestamp="2026-01-01T02:00:00")
        memory_service.store(e1)
        memory_service.store(e2)
        memory_service.store(e3)

        # Export
        export_path = tmp_path / "export.json"
        memory_service.export_history(export_path)

        # Create new service with fresh storage
        _reset_id_counter()
        storage_path2 = tmp_path / "storage2.json"
        memory_service2 = MemoryService(JsonStorage(storage_path2))

        # Import from export
        count, errors = memory_service2.import_history(export_path)
        assert count == 3
        assert len(errors) == 0

        # Verify entries match
        imported = memory_service2.retrieve()
        assert len(imported) == 3
        assert imported[0].operation == "add"
        assert imported[1].operation == "divide"
        assert imported[2].operation == "multiply"
        assert isinstance(imported[0], ResultEntry)
        assert isinstance(imported[1], ErrorEntry)
        assert isinstance(imported[2], ResultEntry)
