import json
import pytest
from src.models.memory_entry import ResultEntry, ErrorEntry, _reset_id_counter
from src.storage.json_storage import JsonStorage


class TestJsonStorageMemory:
    @pytest.fixture
    def storage(self, tmp_path):
        _reset_id_counter()
        return JsonStorage(tmp_path / "calc.json")

    def test_save_result_entry(self, storage):
        entry = ResultEntry(
            operation="add",
            operands=[3, 5],
            result=8,
            timestamp="2026-01-01T00:00:00",
        )
        storage.save(entry)
        assert storage._memory_filepath.exists()

    def test_load_result_entries(self, storage):
        e1 = ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00")
        e2 = ResultEntry(operation="multiply", operands=[3, 4], result=12, timestamp="2026-01-01T00:00:00")
        storage.save(e1)
        storage.save(e2)
        loaded = storage.load_memory_all()
        assert len(loaded) == 2
        assert loaded[0].operation == "add"
        assert loaded[1].operation == "multiply"

    def test_save_error_entry(self, storage):
        entry = ErrorEntry(
            operation="divide",
            operands=[5, 0],
            error_message="Division by zero",
            timestamp="2026-01-01T00:00:00",
        )
        storage.save(entry)
        assert storage._memory_filepath.exists()

    def test_load_error_entries(self, storage):
        e1 = ErrorEntry(
            operation="divide", operands=[5, 0], error_message="div by zero", timestamp="2026-01-01T00:00:00"
        )
        e2 = ErrorEntry(
            operation="sqrt", operands=[-1, 0], error_message="negative", timestamp="2026-01-01T00:00:00"
        )
        storage.save(e1)
        storage.save(e2)
        loaded = storage.load_memory_all()
        assert len(loaded) == 2
        assert loaded[0].error_message == "div by zero"
        assert loaded[1].error_message == "negative"

    def test_load_mixed_entries(self, storage):
        r1 = ResultEntry(operation="add", operands=[1, 1], result=2, timestamp="2026-01-01T00:00:00")
        e1 = ErrorEntry(
            operation="divide", operands=[1, 0], error_message="error", timestamp="2026-01-01T00:00:00"
        )
        r2 = ResultEntry(operation="multiply", operands=[2, 3], result=6, timestamp="2026-01-01T00:00:00")
        storage.save(r1)
        storage.save(e1)
        storage.save(r2)
        loaded = storage.load_memory_all()
        assert len(loaded) == 3
        assert loaded[0].is_error() is False
        assert loaded[1].is_error() is True
        assert loaded[2].is_error() is False

    def test_memory_entries_persist_across_loads(self, tmp_path):
        path = tmp_path / "calc.json"
        storage1 = JsonStorage(path)
        entry = ResultEntry(
            operation="power", operands=[2, 8], result=256, timestamp="2026-01-01T00:00:00"
        )
        storage1.save(entry)

        storage2 = JsonStorage(path)
        loaded = storage2.load_memory_all()
        assert len(loaded) == 1
        assert loaded[0].result == 256

    def test_memory_file_separate_from_calculation_file(self, storage):
        # Save calculation result
        from src.models.calculation_result import CalculationResult

        calc = CalculationResult("add", 1, 2, 3, "2026-01-01T00:00:00")
        storage.save(calc)

        # Save memory entry
        entry = ResultEntry(operation="subtract", operands=[5, 2], result=3, timestamp="2026-01-01T00:00:00")
        storage.save(entry)

        # Verify separate files exist
        assert storage.filepath.exists()
        assert storage._memory_filepath.exists()

        # Verify separate content
        calc_data = storage.load_all()
        memory_data = storage.load_memory_all()
        assert len(calc_data) == 1
        assert len(memory_data) == 1
        assert calc_data[0].operation == "add"
        assert memory_data[0].operation == "subtract"

    def test_memory_empty_when_file_missing(self, storage):
        assert storage.load_memory_all() == []

    def test_memory_json_format(self, storage):
        entry = ResultEntry(
            operation="divide", operands=[10, 2], result=5.0, timestamp="2026-01-01T00:00:00"
        )
        storage.save(entry)
        with open(storage._memory_filepath) as f:
            data = json.load(f)
        assert data[0]["type"] == "result"
        assert data[0]["operation"] == "divide"
        assert data[0]["result"] == 5.0

    def test_corrupted_memory_file_returns_empty(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{{not valid json")
        storage = JsonStorage(bad)
        assert storage.load_memory_all() == []

    def test_memory_creates_parent_dirs(self, tmp_path):
        deep = tmp_path / "a" / "b" / "c" / "calc.json"
        storage = JsonStorage(deep)
        entry = ResultEntry(operation="add", operands=[1, 1], result=2)
        storage.save(entry)
        assert storage._memory_filepath.exists()

    def test_entry_ids_preserved_on_load(self, storage):
        e1 = ResultEntry(entry_id=42, operation="add", operands=[1, 1], result=2)
        e2 = ErrorEntry(entry_id=99, operation="divide", operands=[1, 0], error_message="error")
        storage.save(e1)
        storage.save(e2)
        loaded = storage.load_memory_all()
        assert loaded[0].entry_id == 42
        assert loaded[1].entry_id == 99

    def test_all_fields_preserved_roundtrip(self, storage):
        original = ResultEntry(
            entry_id=100,
            operation="power",
            operands=[2, 10],
            result=1024.0,
            timestamp="2026-02-01T10:30:00",
            execution_time_ms=5.5,
        )
        storage.save(original)
        loaded = storage.load_memory_all()[0]
        assert loaded.entry_id == original.entry_id
        assert loaded.operation == original.operation
        assert loaded.operands == original.operands
        assert loaded.result == original.result
        assert loaded.timestamp == original.timestamp
        assert loaded.execution_time_ms == original.execution_time_ms
