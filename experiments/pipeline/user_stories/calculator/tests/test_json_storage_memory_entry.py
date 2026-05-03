import json
import pytest
from pathlib import Path
from src.models.memory_entry import MemoryEntry
from src.storage.json_storage import JsonStorage


_TS = "2026-05-03T14:30:00"
_UUID = "550e8400-e29b-41d4-a716-446655440000"


class TestJsonStorageWithMemoryEntry:
    """Test JsonStorage with MemoryEntry (success and error cases)."""

    @pytest.fixture
    def storage(self, tmp_path):
        return JsonStorage(tmp_path / "calc.json")

    def test_save_memory_entry_success(self, storage):
        """Save successful MemoryEntry."""
        entry = MemoryEntry("add", 3, 5, 8, None, None, _TS, _UUID)
        storage.save(entry)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].operation == "add"
        assert loaded[0].result == 8

    def test_save_memory_entry_error(self, storage):
        """Save error MemoryEntry."""
        entry = MemoryEntry(
            "divide", 5, 0, None, "Division by zero is not allowed", "ValueError", _TS, _UUID
        )
        storage.save(entry)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].error == "Division by zero is not allowed"
        assert loaded[0].error_type == "ValueError"

    def test_load_all_returns_memory_entries(self, storage):
        """Loaded entries are MemoryEntry objects."""
        entry = MemoryEntry("add", 1, 2, 3, None, None, _TS, _UUID)
        storage.save(entry)
        loaded = storage.load_all()
        assert all(isinstance(e, MemoryEntry) for e in loaded)

    def test_multiple_saves_accumulate(self, storage):
        """Multiple saves accumulate in storage."""
        entry1 = MemoryEntry("add", 1, 2, 3, None, None, _TS, "uuid1")
        entry2 = MemoryEntry("multiply", 3, 4, 12, None, None, _TS, "uuid2")
        storage.save(entry1)
        storage.save(entry2)
        loaded = storage.load_all()
        assert len(loaded) == 2

    def test_save_mixed_success_and_error(self, storage):
        """Mix of successful and error entries."""
        success = MemoryEntry("add", 1, 2, 3, None, None, _TS, "uuid1")
        error = MemoryEntry("divide", 5, 0, None, "error", "ValueError", _TS, "uuid2")
        storage.save(success)
        storage.save(error)
        loaded = storage.load_all()
        assert len(loaded) == 2
        assert loaded[0].error is None
        assert loaded[1].error is not None

    def test_persisted_as_valid_json(self, storage):
        """Saved MemoryEntry is valid JSON."""
        entry = MemoryEntry("add", 3, 5, 8, None, None, _TS, _UUID)
        storage.save(entry)
        with open(storage.filepath) as f:
            data = json.load(f)
        assert data[0]["operation"] == "add"
        assert data[0]["result"] == 8

    def test_load_empty_when_file_missing(self, storage):
        """Empty list when file doesn't exist."""
        assert storage.load_all() == []

    def test_corrupted_file_returns_empty(self, tmp_path):
        """Corrupted JSON returns empty list."""
        bad = tmp_path / "bad.json"
        bad.write_text("{{not valid json")
        assert JsonStorage(bad).load_all() == []

    def test_creates_parent_dirs(self, tmp_path):
        """Parent directories are created."""
        deep = tmp_path / "a" / "b" / "c" / "calc.json"
        s = JsonStorage(deep)
        entry = MemoryEntry("add", 1, 1, 2, None, None, _TS, _UUID)
        s.save(entry)
        assert deep.exists()

    def test_data_survives_reload(self, tmp_path):
        """Data persists across separate storage instances."""
        path = tmp_path / "calc.json"
        entry1 = MemoryEntry("divide", 10, 2, 5.0, None, None, _TS, _UUID)
        JsonStorage(path).save(entry1)

        storage2 = JsonStorage(path)
        loaded = storage2.load_all()
        assert loaded[0].operation == "divide"
        assert loaded[0].result == 5.0


class TestJsonStorageBackwardCompatibility:
    """Test loading old CalculationResult JSON format."""

    @pytest.fixture
    def storage(self, tmp_path):
        return JsonStorage(tmp_path / "calc.json")

    def test_load_old_format_without_error_fields(self, storage):
        """Load old format that lacks error and error_type fields."""
        old_data = [
            {
                "operation": "add",
                "operand_a": 3,
                "operand_b": 5,
                "result": 8,
                "timestamp": _TS,
                "uuid": _UUID,
            }
        ]
        with open(storage.filepath, "w") as f:
            json.dump(old_data, f)

        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].operation == "add"
        assert loaded[0].error is None
        assert loaded[0].error_type is None

    def test_load_old_format_with_execution_time_ms(self, storage):
        """Load old format with execution_time_ms field."""
        old_data = [
            {
                "operation": "multiply",
                "operand_a": 4,
                "operand_b": 5,
                "result": 20,
                "timestamp": _TS,
                "uuid": _UUID,
                "execution_time_ms": 5.5,
            }
        ]
        with open(storage.filepath, "w") as f:
            json.dump(old_data, f)

        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].operation == "multiply"
        assert loaded[0].result == 20
        # execution_time_ms should be discarded during from_dict
        assert not hasattr(loaded[0], "execution_time_ms")

    def test_load_old_format_missing_uuid(self, storage):
        """Load old format missing UUID (generates new one)."""
        old_data = [
            {
                "operation": "add",
                "operand_a": 1,
                "operand_b": 2,
                "result": 3,
                "timestamp": _TS,
            }
        ]
        with open(storage.filepath, "w") as f:
            json.dump(old_data, f)

        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].uuid != ""

    def test_load_mixed_old_and_new_format(self, storage):
        """Load a mix of old and new format entries."""
        mixed_data = [
            {
                "operation": "add",
                "operand_a": 1,
                "operand_b": 2,
                "result": 3,
                "timestamp": _TS,
                "uuid": "uuid1",
                "execution_time_ms": 1.0,
            },
            {
                "operation": "divide",
                "operand_a": 5,
                "operand_b": 0,
                "result": None,
                "error": "Division by zero is not allowed",
                "error_type": "ValueError",
                "timestamp": _TS,
                "uuid": "uuid2",
            },
        ]
        with open(storage.filepath, "w") as f:
            json.dump(mixed_data, f)

        loaded = storage.load_all()
        assert len(loaded) == 2
        assert loaded[0].error is None
        assert loaded[1].error is not None

    def test_load_very_old_format_minimal_fields(self, storage):
        """Load very old format with only essential fields."""
        very_old_data = [
            {
                "operation": "subtract",
                "operand_a": 10,
                "operand_b": 3,
                "result": 7,
                "timestamp": _TS,
            }
        ]
        with open(storage.filepath, "w") as f:
            json.dump(very_old_data, f)

        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].operation == "subtract"
        assert loaded[0].result == 7
        assert loaded[0].error is None

    def test_new_format_save_roundtrip(self, storage):
        """Save and load new format with error fields."""
        original = MemoryEntry(
            "sqrt",
            -5,
            0,
            None,
            "Cannot take square root of negative number",
            "ValueError",
            _TS,
            _UUID,
        )
        storage.save(original)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].error == original.error
        assert loaded[0].error_type == original.error_type

    def test_backward_compat_preserves_uuid(self, storage):
        """UUID from old format is preserved."""
        old_uuid = "12345678-1234-1234-1234-123456789012"
        old_data = [
            {
                "operation": "add",
                "operand_a": 1,
                "operand_b": 2,
                "result": 3,
                "timestamp": _TS,
                "uuid": old_uuid,
            }
        ]
        with open(storage.filepath, "w") as f:
            json.dump(old_data, f)

        loaded = storage.load_all()
        assert loaded[0].uuid == old_uuid

    def test_backward_compat_preserves_timestamp(self, storage):
        """Timestamp from old format is preserved."""
        old_ts = "2026-01-01T12:00:00"
        old_data = [
            {
                "operation": "add",
                "operand_a": 1,
                "operand_b": 2,
                "result": 3,
                "timestamp": old_ts,
                "uuid": _UUID,
            }
        ]
        with open(storage.filepath, "w") as f:
            json.dump(old_data, f)

        loaded = storage.load_all()
        assert loaded[0].timestamp == old_ts


class TestJsonStorageRoundTrip:
    """Test comprehensive round-trip scenarios."""

    @pytest.fixture
    def storage(self, tmp_path):
        return JsonStorage(tmp_path / "calc.json")

    def test_roundtrip_successful_calculation(self, storage):
        """Success entry survives save/load cycle."""
        original = MemoryEntry("multiply", 7, 8, 56, None, None, _TS, _UUID)
        storage.save(original)
        loaded = storage.load_all()
        assert loaded[0].operation == original.operation
        assert loaded[0].operand_a == original.operand_a
        assert loaded[0].operand_b == original.operand_b
        assert loaded[0].result == original.result
        assert loaded[0].error == original.error
        assert loaded[0].error_type == original.error_type
        assert loaded[0].timestamp == original.timestamp
        assert loaded[0].uuid == original.uuid

    def test_roundtrip_error_calculation(self, storage):
        """Error entry survives save/load cycle."""
        original = MemoryEntry(
            "divide", 10, 0, None, "Division by zero is not allowed", "ValueError", _TS, _UUID
        )
        storage.save(original)
        loaded = storage.load_all()
        assert loaded[0].error == original.error
        assert loaded[0].error_type == original.error_type
        assert loaded[0].result is None

    def test_roundtrip_multiple_entries(self, storage):
        """Multiple entries survive save/load cycles."""
        entries = [
            MemoryEntry("add", 1, 2, 3, None, None, _TS, "uuid1"),
            MemoryEntry("divide", 5, 0, None, "error", "ValueError", _TS, "uuid2"),
            MemoryEntry("multiply", 3, 4, 12, None, None, _TS, "uuid3"),
        ]
        for entry in entries:
            storage.save(entry)

        loaded = storage.load_all()
        assert len(loaded) == 3
        assert [e.uuid for e in loaded] == ["uuid1", "uuid2", "uuid3"]

    def test_roundtrip_preserves_float_precision(self, storage):
        """Float values preserve precision through save/load."""
        original = MemoryEntry("divide", 10.5, 2.5, 4.2, None, None, _TS, _UUID)
        storage.save(original)
        loaded = storage.load_all()
        assert loaded[0].operand_a == 10.5
        assert loaded[0].operand_b == 2.5
        assert loaded[0].result == 4.2

    def test_roundtrip_preserves_all_operations(self, storage):
        """All operation types roundtrip correctly."""
        operations = ["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"]
        for i, op in enumerate(operations):
            entry = MemoryEntry(op, i, i + 1, i * 2, None, None, _TS, f"uuid{i}")
            storage.save(entry)

        loaded = storage.load_all()
        assert len(loaded) == len(operations)
        assert [e.operation for e in loaded] == operations
