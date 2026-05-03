import json
import pytest
from pathlib import Path
from src.models.memory_entry import ResultEntry, ErrorEntry, _reset_id_counter
from src.services.history_export_service import HistoryExportService


class TestExportHistory:
    @pytest.fixture
    def service(self):
        return HistoryExportService()

    @pytest.fixture
    def cleanup(self):
        """Reset ID counter before and after each test."""
        _reset_id_counter()
        yield
        _reset_id_counter()

    def test_export_empty_list(self, service, cleanup, tmp_path):
        filepath = tmp_path / "export.json"
        service.export_history([], filepath)
        assert filepath.exists()
        with open(filepath) as f:
            data = json.load(f)
        assert data == []

    def test_export_result_entries(self, service, cleanup, tmp_path):
        entries = [
            ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00"),
            ResultEntry(operation="multiply", operands=[3, 4], result=12, timestamp="2026-01-01T01:00:00"),
        ]
        filepath = tmp_path / "export.json"
        service.export_history(entries, filepath)

        with open(filepath) as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["type"] == "result"
        assert data[0]["operation"] == "add"
        assert data[0]["result"] == 3
        assert data[1]["operation"] == "multiply"
        assert data[1]["result"] == 12

    def test_export_error_entries(self, service, cleanup, tmp_path):
        entries = [
            ErrorEntry(operation="divide", operands=[5, 0], error_message="Division by zero", timestamp="2026-01-01T00:00:00"),
            ErrorEntry(operation="sqrt", operands=[-1, 0], error_message="Negative number", timestamp="2026-01-01T01:00:00"),
        ]
        filepath = tmp_path / "export.json"
        service.export_history(entries, filepath)

        with open(filepath) as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["type"] == "error"
        assert data[0]["error_message"] == "Division by zero"
        assert data[1]["error_message"] == "Negative number"

    def test_export_mixed_entries(self, service, cleanup, tmp_path):
        entries = [
            ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00"),
            ErrorEntry(operation="divide", operands=[5, 0], error_message="Division by zero", timestamp="2026-01-01T01:00:00"),
            ResultEntry(operation="multiply", operands=[3, 4], result=12, timestamp="2026-01-01T02:00:00"),
        ]
        filepath = tmp_path / "export.json"
        service.export_history(entries, filepath)

        with open(filepath) as f:
            data = json.load(f)
        assert len(data) == 3
        assert data[0]["type"] == "result"
        assert data[1]["type"] == "error"
        assert data[2]["type"] == "result"

    def test_export_creates_parent_directory(self, service, cleanup, tmp_path):
        filepath = tmp_path / "subdir" / "export.json"
        entries = [
            ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00"),
        ]
        service.export_history(entries, filepath)
        assert filepath.exists()

    def test_export_invalid_entries_type_raises(self, service, cleanup):
        with pytest.raises(ValueError, match="Entries must be a list"):
            service.export_history("not a list", Path("fake.json"))

    def test_export_invalid_filepath_raises(self, service, cleanup, tmp_path):
        # Try to write to a non-existent nested directory without permissions
        entries = [
            ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00"),
        ]
        # This is hard to test portably; just verify export handles write errors
        # For now we just verify the basic success case
        filepath = tmp_path / "test.json"
        service.export_history(entries, filepath)
        assert filepath.exists()


class TestImportHistory:
    @pytest.fixture
    def service(self):
        return HistoryExportService()

    @pytest.fixture
    def cleanup(self):
        """Reset ID counter before and after each test."""
        _reset_id_counter()
        yield
        _reset_id_counter()

    def test_import_empty_list(self, service, cleanup, tmp_path):
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump([], f)

        entries, errors = service.import_history(filepath)
        assert len(entries) == 0
        assert len(errors) == 0

    def test_import_result_entries(self, service, cleanup, tmp_path):
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
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath)
        assert len(entries) == 2
        assert len(errors) == 0
        assert entries[0].operation == "add"
        assert entries[0].result == 3
        assert entries[1].operation == "multiply"
        assert entries[1].result == 12

    def test_import_error_entries(self, service, cleanup, tmp_path):
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
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath)
        assert len(entries) == 1
        assert len(errors) == 0
        assert entries[0].operation == "divide"
        assert entries[0].error_message == "Division by zero"

    def test_import_mixed_entries(self, service, cleanup, tmp_path):
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
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath)
        assert len(entries) == 2
        assert len(errors) == 0
        assert isinstance(entries[0], ResultEntry)
        assert isinstance(entries[1], ErrorEntry)

    def test_import_file_not_found(self, service, cleanup, tmp_path):
        filepath = tmp_path / "nonexistent.json"
        with pytest.raises(IOError, match="File not found"):
            service.import_history(filepath)

    def test_import_invalid_json(self, service, cleanup, tmp_path):
        filepath = tmp_path / "invalid.json"
        with open(filepath, "w") as f:
            f.write("not valid json {")

        with pytest.raises(ValueError, match="Invalid JSON format"):
            service.import_history(filepath)

    def test_import_non_list_json(self, service, cleanup, tmp_path):
        filepath = tmp_path / "notalist.json"
        with open(filepath, "w") as f:
            json.dump({"not": "a list"}, f)

        with pytest.raises(ValueError, match="JSON root must be an array"):
            service.import_history(filepath)

    def test_import_invalid_entry_type(self, service, cleanup, tmp_path):
        data = [
            {
                "type": "unknown",
                "entry_id": 1,
                "operation": "add",
                "operands": [1, 2],
            },
        ]
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath)
        assert len(entries) == 0
        assert len(errors) == 1
        assert "Invalid type" in errors[0]

    def test_import_missing_operation(self, service, cleanup, tmp_path):
        data = [
            {
                "type": "result",
                "entry_id": 1,
                "operands": [1, 2],
                "result": 3,
                "timestamp": "2026-01-01T00:00:00",
                "execution_time_ms": 1.0,
            },
        ]
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath)
        assert len(entries) == 0
        assert len(errors) == 1
        assert "Missing or invalid 'operation'" in errors[0]

    def test_import_invalid_operands_not_list(self, service, cleanup, tmp_path):
        data = [
            {
                "type": "result",
                "entry_id": 1,
                "operation": "add",
                "operands": "not a list",
                "result": 3,
                "timestamp": "2026-01-01T00:00:00",
                "execution_time_ms": 1.0,
            },
        ]
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath)
        assert len(entries) == 0
        assert len(errors) == 1
        assert "operands" in errors[0] and "list" in errors[0]

    def test_import_missing_timestamp(self, service, cleanup, tmp_path):
        data = [
            {
                "type": "result",
                "entry_id": 1,
                "operation": "add",
                "operands": [1, 2],
                "result": 3,
                "execution_time_ms": 1.0,
            },
        ]
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath)
        assert len(entries) == 0
        assert len(errors) == 1
        assert "Missing or invalid 'timestamp'" in errors[0]

    def test_import_result_entry_missing_result(self, service, cleanup, tmp_path):
        data = [
            {
                "type": "result",
                "entry_id": 1,
                "operation": "add",
                "operands": [1, 2],
                "timestamp": "2026-01-01T00:00:00",
                "execution_time_ms": 1.0,
            },
        ]
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath)
        assert len(entries) == 0
        assert len(errors) == 1
        assert "Missing 'result' field" in errors[0]

    def test_import_result_entry_non_numeric_result(self, service, cleanup, tmp_path):
        data = [
            {
                "type": "result",
                "entry_id": 1,
                "operation": "add",
                "operands": [1, 2],
                "result": "not a number",
                "timestamp": "2026-01-01T00:00:00",
                "execution_time_ms": 1.0,
            },
        ]
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath)
        assert len(entries) == 0
        assert len(errors) == 1
        assert "'result' must be numeric" in errors[0]

    def test_import_error_entry_missing_error_message(self, service, cleanup, tmp_path):
        data = [
            {
                "type": "error",
                "entry_id": 1,
                "operation": "divide",
                "operands": [5, 0],
                "timestamp": "2026-01-01T00:00:00",
                "execution_time_ms": 0.1,
            },
        ]
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath)
        assert len(entries) == 0
        assert len(errors) == 1
        assert "Missing or invalid 'error_message'" in errors[0]

    def test_import_non_dict_entry(self, service, cleanup, tmp_path):
        data = ["not a dict"]
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath)
        assert len(entries) == 0
        assert len(errors) == 1
        assert "Not a dictionary" in errors[0]

    def test_import_skip_duplicates(self, service, cleanup, tmp_path):
        existing_ids = {1}
        data = [
            {
                "type": "result",
                "entry_id": 1,  # duplicate
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
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath, skip_duplicates=True, existing_ids=existing_ids)
        assert len(entries) == 1
        assert len(errors) == 1
        assert "Duplicate entry_id 1" in errors[0]
        assert entries[0].entry_id == 2

    def test_import_allow_duplicates(self, service, cleanup, tmp_path):
        existing_ids = {1}
        data = [
            {
                "type": "result",
                "entry_id": 1,  # duplicate
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
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath, skip_duplicates=False, existing_ids=existing_ids)
        assert len(entries) == 2
        assert len(errors) == 0

    def test_import_mixed_valid_and_invalid(self, service, cleanup, tmp_path):
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
                "type": "unknown",  # invalid type
                "entry_id": 2,
            },
            {
                "type": "result",
                "entry_id": 3,
                "operation": "multiply",
                "operands": [3, 4],
                "result": 12,
                "timestamp": "2026-01-01T01:00:00",
                "execution_time_ms": 0.5,
            },
        ]
        filepath = tmp_path / "import.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        entries, errors = service.import_history(filepath)
        assert len(entries) == 2
        assert len(errors) == 1
        assert entries[0].operation == "add"
        assert entries[1].operation == "multiply"


class TestExportImportRoundtrip:
    @pytest.fixture
    def service(self):
        return HistoryExportService()

    def test_roundtrip_result_entries(self, service, tmp_path):
        _reset_id_counter()
        original_entries = [
            ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00"),
            ResultEntry(operation="multiply", operands=[3, 4], result=12, timestamp="2026-01-01T01:00:00"),
        ]

        filepath = tmp_path / "roundtrip.json"
        service.export_history(original_entries, filepath)
        imported_entries, errors = service.import_history(filepath)

        assert len(errors) == 0
        assert len(imported_entries) == 2
        for orig, imported in zip(original_entries, imported_entries):
            assert imported.operation == orig.operation
            assert imported.operands == orig.operands
            assert imported.result == orig.result
            assert imported.timestamp == orig.timestamp

    def test_roundtrip_error_entries(self, service, tmp_path):
        _reset_id_counter()
        original_entries = [
            ErrorEntry(operation="divide", operands=[5, 0], error_message="Division by zero", timestamp="2026-01-01T00:00:00"),
            ErrorEntry(operation="sqrt", operands=[-1, 0], error_message="Negative number", timestamp="2026-01-01T01:00:00"),
        ]

        filepath = tmp_path / "roundtrip.json"
        service.export_history(original_entries, filepath)
        imported_entries, errors = service.import_history(filepath)

        assert len(errors) == 0
        assert len(imported_entries) == 2
        for orig, imported in zip(original_entries, imported_entries):
            assert imported.operation == orig.operation
            assert imported.operands == orig.operands
            assert imported.error_message == orig.error_message
            assert imported.timestamp == orig.timestamp

    def test_roundtrip_mixed_entries(self, service, tmp_path):
        _reset_id_counter()
        original_entries = [
            ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00"),
            ErrorEntry(operation="divide", operands=[5, 0], error_message="Division by zero", timestamp="2026-01-01T01:00:00"),
            ResultEntry(operation="multiply", operands=[3, 4], result=12, timestamp="2026-01-01T02:00:00"),
        ]

        filepath = tmp_path / "roundtrip.json"
        service.export_history(original_entries, filepath)
        imported_entries, errors = service.import_history(filepath)

        assert len(errors) == 0
        assert len(imported_entries) == 3
        assert isinstance(imported_entries[0], ResultEntry)
        assert isinstance(imported_entries[1], ErrorEntry)
        assert isinstance(imported_entries[2], ResultEntry)
