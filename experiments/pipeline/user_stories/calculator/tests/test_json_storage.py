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
