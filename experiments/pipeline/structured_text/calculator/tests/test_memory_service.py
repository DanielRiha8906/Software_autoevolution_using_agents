import json
import pytest
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.storage.memory_entry_storage import MemoryEntryStorage

_TS = "2026-01-01T00:00:00"


class TestMemoryService:
    @pytest.fixture
    def storage(self, tmp_path):
        return MemoryEntryStorage(tmp_path / "memory.json")

    @pytest.fixture
    def service(self, storage):
        return MemoryService(storage)

    def test_store_single_entry(self, service, storage):
        """Test storing a single successful MemoryEntry."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=0.1,
        )
        service.store(entry)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].operation == "add"
        assert loaded[0].result == 8

    def test_get_all_empty_when_nothing_stored(self, service):
        """Test retrieving empty list when no entries are stored."""
        assert service.get_all() == []

    def test_get_all_multiple_entries(self, service):
        """Test retrieving multiple entries in order."""
        entry1 = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=0.1,
        )
        entry2 = MemoryEntry(
            operation="multiply",
            operand_a=3,
            operand_b=4,
            result=12,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=0.1,
        )
        service.store(entry1)
        service.store(entry2)
        entries = service.get_all()
        assert len(entries) == 2
        assert entries[0].operation == "add"
        assert entries[1].operation == "multiply"

    def test_entry_contents_preserved_after_store_retrieve(self, service):
        """Test that entry contents are preserved after store/retrieve cycle."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=10,
            operand_b=2,
            result=5.0,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=0.5,
        )
        service.store(entry)
        entries = service.get_all()
        loaded = entries[0]
        assert loaded.operation == "divide"
        assert loaded.operand_a == 10
        assert loaded.operand_b == 2
        assert loaded.result == 5.0
        assert loaded.success is True
        assert loaded.error_message is None
        assert loaded.execution_time_ms == 0.5

    def test_works_with_successful_memory_entry(self, service):
        """Test service works correctly with successful MemoryEntry."""
        entry = MemoryEntry(
            operation="subtract",
            operand_a=10,
            operand_b=3,
            result=7,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=0.1,
        )
        service.store(entry)
        entries = service.get_all()
        assert len(entries) == 1
        assert entries[0].success is True

    def test_works_with_failed_memory_entry(self, service):
        """Test service works correctly with failed MemoryEntry."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            result=None,
            success=False,
            error_message="Division by zero",
            timestamp=_TS,
            execution_time_ms=0.1,
        )
        service.store(entry)
        entries = service.get_all()
        assert len(entries) == 1
        assert entries[0].success is False
        assert entries[0].error_message == "Division by zero"
        assert entries[0].result is None

    def test_works_with_backward_compatible_old_format(self, service, storage):
        """Test that service can load old CalculationResult format entries."""
        # Manually write old-format JSON without success, error_message, entry_id
        old_json = [
            {
                "operation": "add",
                "operand_a": 1.0,
                "operand_b": 2.0,
                "result": 3.0,
                "timestamp": "2026-01-01T00:00:00",
                "execution_time_ms": 0.1,
            }
        ]
        with open(storage.filepath, "w") as f:
            json.dump(old_json, f)

        # Load through service and verify backward compatibility
        entries = service.get_all()
        assert len(entries) == 1
        assert entries[0].operation == "add"
        assert entries[0].result == 3.0
        assert entries[0].success is True  # Default for old format
        assert entries[0].error_message is None  # Default for old format

    def test_entry_id_preserved(self, service):
        """Test that entry ID is preserved after store/retrieve."""
        entry = MemoryEntry(
            operation="square",
            operand_a=5,
            operand_b=0,
            result=25,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=0.1,
        )
        original_id = entry.entry_id
        service.store(entry)
        entries = service.get_all()
        assert entries[0].entry_id == original_id

    def test_timestamp_preserved(self, service):
        """Test that timestamp is preserved after store/retrieve."""
        custom_ts = "2026-05-02T12:30:45.123456"
        entry = MemoryEntry(
            operation="power",
            operand_a=2,
            operand_b=3,
            result=8,
            success=True,
            error_message=None,
            timestamp=custom_ts,
            execution_time_ms=0.1,
        )
        service.store(entry)
        entries = service.get_all()
        assert entries[0].timestamp == custom_ts

    def test_multiple_stores_accumulate(self, service):
        """Test that multiple stores accumulate entries."""
        for i in range(5):
            entry = MemoryEntry(
                operation="add",
                operand_a=i,
                operand_b=1,
                result=i + 1,
                success=True,
                error_message=None,
                timestamp=_TS,
                execution_time_ms=0.1,
            )
            service.store(entry)
        entries = service.get_all()
        assert len(entries) == 5

    def test_data_survives_reload_with_new_service_instance(self, storage):
        """Test that stored data persists across service instance reloads."""
        # Store with first service instance
        service1 = MemoryService(storage)
        entry = MemoryEntry(
            operation="modulo",
            operand_a=10,
            operand_b=3,
            result=1,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=0.1,
        )
        service1.store(entry)

        # Load with second service instance
        service2 = MemoryService(storage)
        entries = service2.get_all()
        assert len(entries) == 1
        assert entries[0].operation == "modulo"
        assert entries[0].result == 1
