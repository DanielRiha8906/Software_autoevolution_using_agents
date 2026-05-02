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

    def test_load_legacy_record_without_execution_time(self, tmp_path):
        path = tmp_path / "calc.json"
        # Write a legacy record without execution_time_ms field
        legacy_data = [
            {
                "operation": "add",
                "operand_a": 3.0,
                "operand_b": 5.0,
                "result": 8.0,
                "timestamp": _TS
            }
        ]
        with open(path, "w") as f:
            json.dump(legacy_data, f)

        # Load should succeed with default execution_time_ms=0.0
        storage = JsonStorage(path)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].execution_time_ms == 0.0
        assert loaded[0].operation == "add"

    def test_save_and_load_with_execution_time(self, storage):
        r = CalculationResult("add", 3, 5, 8, _TS, execution_time_ms=12.345)
        storage.save(r)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].execution_time_ms == 12.345

    def test_persisted_execution_time_as_json_number(self, storage):
        storage.save(CalculationResult("subtract", 9, 3, 6, _TS, execution_time_ms=5.678))
        with open(storage.filepath) as f:
            data = json.load(f)
        assert data[0]["execution_time_ms"] == 5.678
        assert isinstance(data[0]["execution_time_ms"], float)

    def test_save_and_load_new_operations(self, storage):
        square = CalculationResult("square", 5, 0, 25, _TS)
        sqrt = CalculationResult("sqrt", 9, 0, 3.0, _TS)
        power = CalculationResult("power", 2, 3, 8, _TS)
        modulo = CalculationResult("modulo", 10, 3, 1, _TS)

        storage.save(square)
        storage.save(sqrt)
        storage.save(power)
        storage.save(modulo)

        loaded = storage.load_all()
        assert len(loaded) == 4
        assert loaded[0].operation == "square"
        assert loaded[0].result == 25
        assert loaded[1].operation == "sqrt"
        assert loaded[1].result == 3.0
        assert loaded[2].operation == "power"
        assert loaded[2].result == 8
        assert loaded[3].operation == "modulo"
        assert loaded[3].result == 1
