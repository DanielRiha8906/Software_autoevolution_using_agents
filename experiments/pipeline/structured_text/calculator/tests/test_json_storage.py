import json
import pytest
from src.models.calculation_result import CalculationResult
from src.storage.json_storage import JsonStorage

_TS = "2026-01-01T00:00:00"


class TestJsonStorage:
    @pytest.fixture
    def storage(self, tmp_path):
        return JsonStorage(tmp_path / "calc.json")

    def test_load_empty_when_file_missing(self, storage):
        assert storage.load_all() == []

    def test_save_then_load(self, storage):
        r = CalculationResult("add", 3, 5, 8, _TS)
        storage.save(r)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].operation == "add"
        assert loaded[0].result == 8

    def test_multiple_saves_accumulate(self, storage):
        storage.save(CalculationResult("add",      1, 2, 3,  _TS))
        storage.save(CalculationResult("multiply", 3, 4, 12, _TS))
        assert len(storage.load_all()) == 2

    def test_data_survives_reload(self, tmp_path):
        path = tmp_path / "calc.json"
        s1 = JsonStorage(path)
        s1.save(CalculationResult("divide", 10, 2, 5.0, _TS))

        s2 = JsonStorage(path)
        loaded = s2.load_all()
        assert loaded[0].operation == "divide"
        assert loaded[0].result == 5.0

    def test_persisted_as_valid_json(self, storage):
        storage.save(CalculationResult("subtract", 9, 3, 6, _TS))
        with open(storage.filepath) as f:
            data = json.load(f)
        assert data[0]["operation"] == "subtract"

    def test_corrupted_file_returns_empty(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{{not valid json")
        assert JsonStorage(bad).load_all() == []

    def test_creates_parent_dirs(self, tmp_path):
        deep = tmp_path / "a" / "b" / "c" / "calc.json"
        s = JsonStorage(deep)
        s.save(CalculationResult("add", 1, 1, 2, _TS))
        assert deep.exists()


class TestJsonStorageExecutionTime:
    """Test that JsonStorage preserves execution_time_ms field."""

    @pytest.fixture
    def storage(self, tmp_path):
        return JsonStorage(tmp_path / "calc.json")

    def test_save_and_load_preserves_execution_time_ms(self, storage):
        """Test 9: Save and load round-trip preserves execution_time_ms."""
        original = CalculationResult("add", 5, 3, 8, _TS, execution_time_ms=2.5)
        storage.save(original)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].execution_time_ms == 2.5

    def test_multiple_saves_with_different_execution_times(self, storage):
        """Test 9b: Multiple saves preserve different execution times."""
        storage.save(CalculationResult("add", 1, 2, 3, _TS, execution_time_ms=1.1))
        storage.save(CalculationResult("multiply", 3, 4, 12, _TS, execution_time_ms=2.2))
        loaded = storage.load_all()
        assert len(loaded) == 2
        assert loaded[0].execution_time_ms == 1.1
        assert loaded[1].execution_time_ms == 2.2

    def test_backward_compatibility_old_records_without_execution_time(self, storage):
        """Test 3b: Loading old records without execution_time_ms defaults to 0.0."""
        import json
        old_record = {
            "operation": "subtract",
            "operand_a": 10.0,
            "operand_b": 3.0,
            "result": 7.0,
            "timestamp": _TS
        }
        with open(storage.filepath, "w") as f:
            json.dump([old_record], f)

        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].execution_time_ms == 0.0
        assert loaded[0].operation == "subtract"

    def test_mixed_old_and_new_records(self, storage):
        """Test 3c: Mixed old records (no execution_time_ms) and new records work together."""
        import json
        old_record = {
            "operation": "add",
            "operand_a": 1.0,
            "operand_b": 2.0,
            "result": 3.0,
            "timestamp": _TS
        }
        with open(storage.filepath, "w") as f:
            json.dump([old_record], f)

        new_record = CalculationResult("divide", 10, 2, 5.0, _TS, execution_time_ms=1.5)
        storage.save(new_record)

        loaded = storage.load_all()
        assert len(loaded) == 2
        assert loaded[0].execution_time_ms == 0.0
        assert loaded[1].execution_time_ms == 1.5

    def test_persisted_execution_time_ms_survives_reload(self, tmp_path):
        """Test 9c: execution_time_ms survives file reload."""
        path = tmp_path / "calc.json"
        s1 = JsonStorage(path)
        s1.save(CalculationResult("multiply", 6, 7, 42, _TS, execution_time_ms=3.7))

        s2 = JsonStorage(path)
        loaded = s2.load_all()
        assert loaded[0].execution_time_ms == 3.7
