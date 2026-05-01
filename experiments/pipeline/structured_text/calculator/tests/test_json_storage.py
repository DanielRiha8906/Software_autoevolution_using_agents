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
        r = CalculationResult("add", 3, 5, 8, _TS, 0.0)
        storage.save(r)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].operation == "add"
        assert loaded[0].result == 8

    def test_multiple_saves_accumulate(self, storage):
        storage.save(CalculationResult("add",      1, 2, 3,  _TS, 0.0))
        storage.save(CalculationResult("multiply", 3, 4, 12, _TS, 0.0))
        assert len(storage.load_all()) == 2

    def test_data_survives_reload(self, tmp_path):
        path = tmp_path / "calc.json"
        s1 = JsonStorage(path)
        s1.save(CalculationResult("divide", 10, 2, 5.0, _TS, 0.0))

        s2 = JsonStorage(path)
        loaded = s2.load_all()
        assert loaded[0].operation == "divide"
        assert loaded[0].result == 5.0

    def test_persisted_as_valid_json(self, storage):
        storage.save(CalculationResult("subtract", 9, 3, 6, _TS, 0.0))
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
        s.save(CalculationResult("add", 1, 1, 2, _TS, 0.0))
        assert deep.exists()

    def test_execution_time_ms_persisted_and_loaded(self, storage):
        r = CalculationResult("add", 3, 5, 8, _TS, 1.234)
        storage.save(r)
        loaded = storage.load_all()
        assert loaded[0].execution_time_ms == 1.234

    def test_backward_compatibility_old_json_without_execution_time_ms(self, storage):
        # Manually write old-format JSON without execution_time_ms field
        old_json = [
            {
                "operation": "add",
                "operand_a": 1.0,
                "operand_b": 2.0,
                "result": 3.0,
                "timestamp": "2026-01-01T00:00:00"
            }
        ]
        with open(storage.filepath, "w") as f:
            json.dump(old_json, f)

        # Load and verify it gets default execution_time_ms
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].execution_time_ms == 0.0
        assert loaded[0].operation == "add"
