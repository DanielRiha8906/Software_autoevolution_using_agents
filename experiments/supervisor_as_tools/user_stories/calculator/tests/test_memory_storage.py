import json
import pytest
from src.models.memory_entry import MemoryEntry
from src.models.calculation_result import CalculationResult
from src.storage.json_storage import JsonStorage


_TS = "2026-01-01T00:00:00"


class TestMemoryStorageSaveLoad:
    """Test MemoryEntry save and load round-trip."""

    @pytest.fixture
    def storage(self, tmp_path):
        return JsonStorage(tmp_path / "storage.json")

    def test_save_and_load_memory_entry_round_trip(self, storage):
        """Test save and load MemoryEntry round-trip preserves all fields."""
        entry_orig = MemoryEntry(
            operation_name="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            entry_id="test-id-123",
            error_message=None,
            timestamp="2026-01-01T12:00:00",
            execution_time_ms=2.5,
        )
        storage.save(entry_orig)
        loaded = storage.load_all()
        assert len(loaded) == 1
        entry_loaded = loaded[0]
        assert entry_loaded.operation_name == entry_orig.operation_name
        assert entry_loaded.operand_a == entry_orig.operand_a
        assert entry_loaded.operand_b == entry_orig.operand_b
        assert entry_loaded.result == entry_orig.result
        assert entry_loaded.success == entry_orig.success
        assert entry_loaded.entry_id == entry_orig.entry_id
        assert entry_loaded.error_message == entry_orig.error_message
        assert entry_loaded.timestamp == entry_orig.timestamp
        assert entry_loaded.execution_time_ms == entry_orig.execution_time_ms

    def test_save_and_load_failed_entry(self, storage):
        """Test save and load failed MemoryEntry with error_message."""
        entry_orig = MemoryEntry(
            operation_name="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            success=False,
            entry_id="failed-id-456",
            error_message="Division by zero",
            timestamp="2026-01-01T12:00:01",
            execution_time_ms=1.0,
        )
        storage.save(entry_orig)
        loaded = storage.load_all()
        assert len(loaded) == 1
        entry_loaded = loaded[0]
        assert entry_loaded.success is False
        assert entry_loaded.result is None
        assert entry_loaded.error_message == "Division by zero"

    def test_multiple_entries_accumulate(self, storage):
        """Test multiple MemoryEntry saves accumulate."""
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True, "id1", None, _TS)
        entry2 = MemoryEntry("subtract", 5.0, 3.0, 2.0, True, "id2", None, _TS)
        entry3 = MemoryEntry("multiply", 3.0, 4.0, 12.0, True, "id3", None, _TS)
        storage.save(entry1)
        storage.save(entry2)
        storage.save(entry3)
        loaded = storage.load_all()
        assert len(loaded) == 3
        assert all(isinstance(e, MemoryEntry) for e in loaded)

    def test_entries_survive_reload(self, tmp_path):
        """Test MemoryEntry persists across different storage instances."""
        path = tmp_path / "persist.json"
        storage1 = JsonStorage(path)
        entry1 = MemoryEntry("add", 10.0, 20.0, 30.0, True, "persist-id", None, _TS, 5.5)
        storage1.save(entry1)

        storage2 = JsonStorage(path)
        loaded = storage2.load_all()
        assert len(loaded) == 1
        entry_loaded = loaded[0]
        assert entry_loaded.operation_name == "add"
        assert entry_loaded.operand_a == 10.0
        assert entry_loaded.operand_b == 20.0
        assert entry_loaded.result == 30.0
        assert entry_loaded.execution_time_ms == 5.5


class TestMemoryStorageDetection:
    """Test detection of MemoryEntry vs CalculationResult."""

    @pytest.fixture
    def storage(self, tmp_path):
        return JsonStorage(tmp_path / "detect.json")

    def test_deserialize_detects_memory_entry_by_entry_id_key(self, storage):
        """Test load_all() detects MemoryEntry by presence of 'entry_id' key."""
        # Manually create a JSON with entry_id
        entry_dict = {
            "operation_name": "add",
            "operand_a": 1.0,
            "operand_b": 2.0,
            "result": 3.0,
            "success": True,
            "entry_id": "test-entry-id",
            "error_message": None,
            "timestamp": _TS,
            "execution_time_ms": 1.0,
        }
        storage._write_raw([entry_dict])
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert isinstance(loaded[0], MemoryEntry)
        assert loaded[0].entry_id == "test-entry-id"

    def test_deserialize_detects_calculation_result_without_entry_id(self, storage):
        """Test load_all() detects CalculationResult by absence of 'entry_id' key."""
        # Manually create a JSON without entry_id (old CalculationResult format)
        result_dict = {
            "operation": "add",
            "operand_a": 1.0,
            "operand_b": 2.0,
            "result": 3.0,
            "timestamp": _TS,
            "execution_time_ms": 1.0,
        }
        storage._write_raw([result_dict])
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert isinstance(loaded[0], CalculationResult)
        assert loaded[0].operation == "add"

    def test_mixed_storage_both_types(self, storage):
        """Test storage with both MemoryEntry and CalculationResult."""
        memory_entry = MemoryEntry("add", 1.0, 2.0, 3.0, True, "mem-id", None, _TS)
        calc_result = CalculationResult("subtract", 5.0, 3.0, 2.0, _TS)
        storage.save(memory_entry)
        storage.save(calc_result)
        loaded = storage.load_all()
        assert len(loaded) == 2
        assert isinstance(loaded[0], MemoryEntry)
        assert isinstance(loaded[1], CalculationResult)

    def test_load_all_filters_correctly(self, storage):
        """Test load_all() distinguishes between types correctly."""
        memory_entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True, "id1", None, _TS)
        calc_result = CalculationResult("subtract", 5.0, 3.0, 2.0, _TS)
        memory_entry2 = MemoryEntry("multiply", 3.0, 4.0, 12.0, True, "id2", None, _TS)
        storage.save(memory_entry1)
        storage.save(calc_result)
        storage.save(memory_entry2)
        loaded = storage.load_all()
        assert len(loaded) == 3
        assert isinstance(loaded[0], MemoryEntry)
        assert isinstance(loaded[1], CalculationResult)
        assert isinstance(loaded[2], MemoryEntry)


class TestBackwardCompatibility:
    """Test backward compatibility with old CalculationResult entries."""

    @pytest.fixture
    def storage(self, tmp_path):
        return JsonStorage(tmp_path / "compat.json")

    def test_old_calculation_result_entries_still_load(self, storage):
        """Test that old CalculationResult entries still load correctly."""
        # Old format without entry_id
        old_calc = CalculationResult("add", 3.0, 5.0, 8.0, _TS)
        storage.save(old_calc)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert isinstance(loaded[0], CalculationResult)
        assert loaded[0].operation == "add"
        assert loaded[0].result == 8.0

    def test_legacy_json_without_entry_id_loads_as_calculation_result(self, storage):
        """Test legacy JSON format loads as CalculationResult."""
        legacy_dict = {
            "operation": "add",
            "operand_a": 2.0,
            "operand_b": 3.0,
            "result": 5.0,
            "timestamp": _TS,
        }
        storage._write_raw([legacy_dict])
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert isinstance(loaded[0], CalculationResult)

    def test_mixed_old_and_new_entries(self, storage):
        """Test mixed old CalculationResult and new MemoryEntry entries."""
        calc_result = CalculationResult("add", 1.0, 2.0, 3.0, _TS)
        memory_entry = MemoryEntry("subtract", 5.0, 3.0, 2.0, True, "new-id", None, _TS)
        calc_result2 = CalculationResult("multiply", 3.0, 4.0, 12.0, _TS)
        storage.save(calc_result)
        storage.save(memory_entry)
        storage.save(calc_result2)
        loaded = storage.load_all()
        assert len(loaded) == 3
        assert isinstance(loaded[0], CalculationResult)
        assert isinstance(loaded[1], MemoryEntry)
        assert isinstance(loaded[2], CalculationResult)

    def test_get_all_entries_only_returns_memory_entries(self, storage):
        """Test that calling load_all then filtering returns only MemoryEntry."""
        calc_result = CalculationResult("add", 1.0, 2.0, 3.0, _TS)
        memory_entry = MemoryEntry("subtract", 5.0, 3.0, 2.0, True, "mem-id", None, _TS)
        storage.save(calc_result)
        storage.save(memory_entry)
        all_records = storage.load_all()
        memory_entries = [r for r in all_records if isinstance(r, MemoryEntry)]
        assert len(memory_entries) == 1
        assert memory_entries[0].operation_name == "subtract"


class TestMemoryEntryPersistence:
    """Test persistence specifics of MemoryEntry."""

    @pytest.fixture
    def storage(self, tmp_path):
        return JsonStorage(tmp_path / "persist.json")

    def test_persisted_as_valid_json_with_entry_id(self, storage):
        """Test MemoryEntry is persisted as valid JSON with entry_id field."""
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True, "test-id", None, _TS, 1.5)
        storage.save(entry)
        with open(storage.filepath) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["entry_id"] == "test-id"
        assert data[0]["operation_name"] == "add"
        assert data[0]["result"] == 3.0

    def test_persisted_entry_includes_execution_time_ms(self, storage):
        """Test MemoryEntry persists with execution_time_ms."""
        entry = MemoryEntry("subtract", 10.0, 3.0, 7.0, True, "id", None, _TS, 3.5)
        storage.save(entry)
        with open(storage.filepath) as f:
            data = json.load(f)
        assert data[0]["execution_time_ms"] == 3.5

    def test_persisted_failed_entry_has_null_result(self, storage):
        """Test failed MemoryEntry persists with result=null."""
        entry = MemoryEntry("divide", 5.0, 0.0, None, False, "fail-id", "Division error", _TS, 1.0)
        storage.save(entry)
        with open(storage.filepath) as f:
            data = json.load(f)
        assert data[0]["result"] is None
        assert data[0]["success"] is False
        assert data[0]["error_message"] == "Division error"

    def test_persisted_entry_includes_all_nine_fields(self, storage):
        """Test persisted MemoryEntry includes all 9 required fields."""
        entry = MemoryEntry(
            operation_name="power",
            operand_a=2.0,
            operand_b=3.0,
            result=8.0,
            success=True,
            entry_id="complete-id",
            error_message=None,
            timestamp="2026-01-01T12:00:00",
            execution_time_ms=2.0,
        )
        storage.save(entry)
        with open(storage.filepath) as f:
            data = json.load(f)
        record = data[0]
        assert "operation_name" in record
        assert "operand_a" in record
        assert "operand_b" in record
        assert "result" in record
        assert "success" in record
        assert "entry_id" in record
        assert "error_message" in record
        assert "timestamp" in record
        assert "execution_time_ms" in record
        assert len(record) == 9
