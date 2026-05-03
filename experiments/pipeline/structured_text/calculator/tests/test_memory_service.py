import json
import pytest
from pathlib import Path
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.storage.memory_json_storage import MemoryJsonStorage


class TestMemoryServiceInitialization:
    """Test MemoryService initialization."""

    def test_init_with_storage(self, tmp_path):
        """Test 1: Initialize MemoryService with MemoryJsonStorage."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)
        assert service.storage is storage

    def test_init_stores_reference(self, tmp_path):
        """Test 2: MemoryService maintains reference to storage."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)
        assert service.storage is storage


class TestMemoryServiceStore:
    """Test MemoryService.store() method."""

    @pytest.fixture
    def service(self, tmp_path):
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        return MemoryService(storage)

    def test_store_single_entry(self, service):
        """Test 1: Store a single MemoryEntry."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.5,
            memory_entry_id="test-id-1"
        )
        service.store(entry)

        # Verify it was persisted
        loaded = service.retrieve_all()
        assert len(loaded) == 1
        assert loaded[0].operation == "add"
        assert loaded[0].result == 3.0

    def test_store_multiple_entries(self, service):
        """Test 2: Store multiple entries accumulates them."""
        entry1 = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.5,
            memory_entry_id="id-1"
        )
        entry2 = MemoryEntry(
            operation="multiply",
            operand_a=3.0,
            operand_b=4.0,
            result=12.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:01:00",
            execution_time_ms=2.0,
            memory_entry_id="id-2"
        )

        service.store(entry1)
        service.store(entry2)

        loaded = service.retrieve_all()
        assert len(loaded) == 2
        assert loaded[0].operation == "add"
        assert loaded[1].operation == "multiply"

    @pytest.mark.parametrize("operation,a,b,result", [
        ("add", 1.0, 2.0, 3.0),
        ("subtract", 10.0, 3.0, 7.0),
        ("multiply", 4.0, 5.0, 20.0),
        ("divide", 20.0, 4.0, 5.0),
    ])
    def test_store_different_operations(self, service, operation, a, b, result):
        """Test 3: Store entries for different operation types."""
        entry = MemoryEntry(
            operation=operation,
            operand_a=a,
            operand_b=b,
            result=result,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.0,
            memory_entry_id=f"id-{operation}"
        )
        service.store(entry)

        loaded = service.retrieve_all()
        assert loaded[0].operation == operation
        assert loaded[0].result == result

    def test_store_successful_calculation(self, service):
        """Test 4: Store entry with success=True."""
        entry = MemoryEntry(
            operation="add",
            operand_a=5.0,
            operand_b=3.0,
            result=8.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.5,
            memory_entry_id="success-id"
        )
        service.store(entry)

        loaded = service.retrieve_all()
        assert loaded[0].success is True
        assert loaded[0].result == 8.0
        assert loaded[0].error_message is None

    def test_store_failed_calculation(self, service):
        """Test 5: Store entry with success=False and error message."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero",
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=0.5,
            memory_entry_id="error-id"
        )
        service.store(entry)

        loaded = service.retrieve_all()
        assert loaded[0].success is False
        assert loaded[0].result is None
        assert loaded[0].error_message == "Division by zero"

    def test_store_with_various_execution_times(self, service):
        """Test 6: Store entries preserve various execution_time_ms values."""
        exec_times = [0.0, 0.5, 1.25, 10.75, 999.999]
        for idx, exec_time in enumerate(exec_times):
            entry = MemoryEntry(
                operation="add",
                operand_a=1.0,
                operand_b=1.0,
                result=2.0,
                success=True,
                error_message=None,
                execution_timestamp="2026-05-03T10:00:00",
                execution_time_ms=exec_time,
                memory_entry_id=f"id-{idx}"
            )
            service.store(entry)

        loaded = service.retrieve_all()
        assert len(loaded) == 5
        for idx, expected_time in enumerate(exec_times):
            assert loaded[idx].execution_time_ms == expected_time


class TestMemoryServiceRetrieveAll:
    """Test MemoryService.retrieve_all() method."""

    @pytest.fixture
    def service(self, tmp_path):
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        return MemoryService(storage)

    def test_retrieve_all_empty_storage(self, service):
        """Test 1: retrieve_all() returns empty list when storage is empty."""
        loaded = service.retrieve_all()
        assert loaded == []
        assert isinstance(loaded, list)

    def test_retrieve_all_single_entry(self, service):
        """Test 2: retrieve_all() returns list with single entry."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.5,
            memory_entry_id="id-1"
        )
        service.store(entry)

        loaded = service.retrieve_all()
        assert len(loaded) == 1
        assert isinstance(loaded, list)
        assert isinstance(loaded[0], MemoryEntry)

    def test_retrieve_all_multiple_entries(self, service):
        """Test 3: retrieve_all() returns all stored entries in order."""
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=1.0,
                operand_b=2.0,
                result=3.0,
                success=True,
                error_message=None,
                execution_timestamp="2026-05-03T10:00:00",
                execution_time_ms=1.0,
                memory_entry_id="id-1"
            ),
            MemoryEntry(
                operation="subtract",
                operand_a=10.0,
                operand_b=3.0,
                result=7.0,
                success=True,
                error_message=None,
                execution_timestamp="2026-05-03T10:01:00",
                execution_time_ms=2.0,
                memory_entry_id="id-2"
            ),
            MemoryEntry(
                operation="multiply",
                operand_a=4.0,
                operand_b=5.0,
                result=20.0,
                success=True,
                error_message=None,
                execution_timestamp="2026-05-03T10:02:00",
                execution_time_ms=3.0,
                memory_entry_id="id-3"
            ),
        ]

        for entry in entries:
            service.store(entry)

        loaded = service.retrieve_all()
        assert len(loaded) == 3
        assert loaded[0].operation == "add"
        assert loaded[1].operation == "subtract"
        assert loaded[2].operation == "multiply"

    def test_retrieve_all_returns_memory_entries(self, service):
        """Test 4: retrieve_all() returns MemoryEntry instances."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=20.0,
            operand_b=4.0,
            result=5.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.5,
            memory_entry_id="id-1"
        )
        service.store(entry)

        loaded = service.retrieve_all()
        assert all(isinstance(e, MemoryEntry) for e in loaded)

    def test_retrieve_all_mixed_success_and_failure(self, service):
        """Test 5: retrieve_all() returns mix of successful and failed entries."""
        success_entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.0,
            memory_entry_id="id-1"
        )
        failure_entry = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero",
            execution_timestamp="2026-05-03T10:01:00",
            execution_time_ms=0.5,
            memory_entry_id="id-2"
        )

        service.store(success_entry)
        service.store(failure_entry)

        loaded = service.retrieve_all()
        assert len(loaded) == 2
        assert loaded[0].success is True
        assert loaded[1].success is False


class TestMemoryServiceRoundTripPersistence:
    """Test round-trip persistence: store -> retrieve -> verify."""

    @pytest.fixture
    def service(self, tmp_path):
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        return MemoryService(storage)

    def test_round_trip_single_entry(self, service):
        """Test 1: Single entry survives store and retrieve cycle."""
        original = MemoryEntry(
            operation="add",
            operand_a=5.0,
            operand_b=3.0,
            result=8.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.5,
            memory_entry_id="uuid-123"
        )

        service.store(original)
        loaded = service.retrieve_all()

        assert len(loaded) == 1
        assert loaded[0].operation == original.operation
        assert loaded[0].operand_a == original.operand_a
        assert loaded[0].operand_b == original.operand_b
        assert loaded[0].result == original.result
        assert loaded[0].success == original.success
        assert loaded[0].error_message == original.error_message
        assert loaded[0].execution_timestamp == original.execution_timestamp
        assert loaded[0].execution_time_ms == original.execution_time_ms
        assert loaded[0].memory_entry_id == original.memory_entry_id

    def test_round_trip_multiple_entries(self, service):
        """Test 2: Multiple entries survive store and retrieve cycle."""
        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:02:00", 3.0, "id-3"),
        ]

        for entry in entries:
            service.store(entry)

        loaded = service.retrieve_all()

        assert len(loaded) == 3
        for original, retrieved in zip(entries, loaded):
            assert retrieved.operation == original.operation
            assert retrieved.operand_a == original.operand_a
            assert retrieved.operand_b == original.operand_b
            assert retrieved.result == original.result

    def test_round_trip_failed_entry(self, service):
        """Test 3: Failed entry with error message survives round-trip."""
        original = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero",
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=0.5,
            memory_entry_id="error-uuid"
        )

        service.store(original)
        loaded = service.retrieve_all()

        assert loaded[0].success is False
        assert loaded[0].result is None
        assert loaded[0].error_message == "Division by zero"

    def test_round_trip_preserves_execution_time(self, service):
        """Test 4: execution_time_ms is preserved in round-trip."""
        original = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=1.0,
            result=2.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=2.75,
            memory_entry_id="id-1"
        )

        service.store(original)
        loaded = service.retrieve_all()

        assert loaded[0].execution_time_ms == 2.75

    def test_cross_service_persistence(self, tmp_path):
        """Test 5: Data survives across different service instances."""
        path = tmp_path / "memory.json"

        # First service instance: store
        storage1 = MemoryJsonStorage(path)
        service1 = MemoryService(storage1)
        entry = MemoryEntry(
            operation="add",
            operand_a=5.0,
            operand_b=3.0,
            result=8.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.5,
            memory_entry_id="uuid-123"
        )
        service1.store(entry)

        # Second service instance: retrieve
        storage2 = MemoryJsonStorage(path)
        service2 = MemoryService(storage2)
        loaded = service2.retrieve_all()

        assert len(loaded) == 1
        assert loaded[0].operation == "add"
        assert loaded[0].result == 8.0


class TestMemoryServiceErrorHandling:
    """Test error scenarios and edge cases."""

    @pytest.fixture
    def service(self, tmp_path):
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        return MemoryService(storage)

    def test_retrieve_all_missing_file_returns_empty(self, tmp_path):
        """Test 1: retrieve_all() returns empty list if file doesn't exist."""
        storage = MemoryJsonStorage(tmp_path / "nonexistent.json")
        service = MemoryService(storage)

        result = service.retrieve_all()

        assert result == []
        assert isinstance(result, list)

    def test_retrieve_all_corrupted_json_returns_empty(self, tmp_path):
        """Test 2: retrieve_all() returns empty list if JSON is malformed."""
        path = tmp_path / "corrupt.json"
        path.write_text("{not: valid json")

        storage = MemoryJsonStorage(path)
        service = MemoryService(storage)

        result = service.retrieve_all()
        assert result == []

    def test_store_creates_parent_directories(self, tmp_path):
        """Test 3: store() creates parent directories automatically."""
        deep_path = tmp_path / "a" / "b" / "c" / "memory.json"
        storage = MemoryJsonStorage(deep_path)
        service = MemoryService(storage)

        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.0,
            memory_entry_id="id-1"
        )
        service.store(entry)

        assert deep_path.exists()
        assert deep_path.is_file()

    def test_retrieve_all_after_corrupt_then_store(self, tmp_path):
        """Test 4: store() works after corrupted file is replaced."""
        path = tmp_path / "memory.json"
        path.write_text("{invalid json")

        storage = MemoryJsonStorage(path)
        service = MemoryService(storage)

        # Retrieve should return empty due to corruption
        assert service.retrieve_all() == []

        # Store should replace the file with valid data
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.0,
            memory_entry_id="id-1"
        )
        service.store(entry)

        # Now retrieve should work
        loaded = service.retrieve_all()
        assert len(loaded) == 1
        assert loaded[0].operation == "add"


class TestMemoryJsonStorageDirect:
    """Test MemoryJsonStorage directly (not through MemoryService)."""

    @pytest.fixture
    def storage(self, tmp_path):
        return MemoryJsonStorage(tmp_path / "memory.json")

    def test_save_creates_file(self, storage):
        """Test 1: save() creates the JSON file."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.0,
            memory_entry_id="id-1"
        )

        assert not storage.filepath.exists()
        storage.save(entry)
        assert storage.filepath.exists()

    def test_load_all_empty_file(self, storage):
        """Test 2: load_all() returns empty list for empty file."""
        result = storage.load_all()
        assert result == []

    def test_save_then_load_single(self, storage):
        """Test 3: save() then load_all() retrieves the entry."""
        entry = MemoryEntry(
            operation="multiply",
            operand_a=3.0,
            operand_b=4.0,
            result=12.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.5,
            memory_entry_id="id-1"
        )

        storage.save(entry)
        loaded = storage.load_all()

        assert len(loaded) == 1
        assert loaded[0].operation == "multiply"
        assert loaded[0].result == 12.0

    def test_multiple_saves_accumulate(self, storage):
        """Test 4: Multiple save() calls accumulate entries."""
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1")
        entry2 = MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2")

        storage.save(entry1)
        storage.save(entry2)

        loaded = storage.load_all()
        assert len(loaded) == 2

    def test_persisted_data_is_valid_json(self, storage):
        """Test 5: Persisted data is valid JSON."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=20.0,
            operand_b=4.0,
            result=5.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.5,
            memory_entry_id="id-1"
        )

        storage.save(entry)

        with open(storage.filepath) as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["operation"] == "divide"

    def test_successful_and_failed_entries_both_persist(self, storage):
        """Test 6: Both successful and failed entries persist correctly."""
        success = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.0,
            memory_entry_id="id-1"
        )
        failure = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero",
            execution_timestamp="2026-05-03T10:01:00",
            execution_time_ms=0.5,
            memory_entry_id="id-2"
        )

        storage.save(success)
        storage.save(failure)

        loaded = storage.load_all()
        assert len(loaded) == 2
        assert loaded[0].success is True
        assert loaded[1].success is False
        assert loaded[1].error_message == "Division by zero"

    def test_backward_compatibility_with_old_format(self, tmp_path):
        """Test 7: load_all() handles old JSON format without execution_time_ms."""
        path = tmp_path / "memory.json"
        old_entry = {
            "operation": "add",
            "operand_a": 1.0,
            "operand_b": 2.0,
            "result": 3.0,
            "timestamp": "2026-05-03T10:00:00"
        }
        with open(path, "w") as f:
            json.dump([old_entry], f)

        storage = MemoryJsonStorage(path)
        loaded = storage.load_all()

        assert len(loaded) == 1
        assert loaded[0].operation == "add"
        assert loaded[0].execution_time_ms == 0.0
        assert loaded[0].execution_timestamp == "2026-05-03T10:00:00"


class TestMemoryServiceIntegration:
    """Integration tests combining MemoryService and MemoryJsonStorage."""

    def test_service_delegates_to_storage(self, tmp_path):
        """Test 1: MemoryService correctly delegates store() to storage."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.0,
            memory_entry_id="id-1"
        )

        service.store(entry)

        # Verify storage has the file
        assert storage.filepath.exists()

    def test_service_delegates_to_storage_retrieve(self, tmp_path):
        """Test 2: MemoryService correctly delegates retrieve_all() to storage."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entry = MemoryEntry(
            operation="subtract",
            operand_a=10.0,
            operand_b=3.0,
            result=7.0,
            success=True,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=2.0,
            memory_entry_id="id-1"
        )

        service.store(entry)
        service_result = service.retrieve_all()
        storage_result = storage.load_all()

        assert len(service_result) == len(storage_result)
        assert service_result[0].operation == storage_result[0].operation

    def test_complete_workflow(self, tmp_path):
        """Test 3: Complete workflow from store to retrieve across instances."""
        path = tmp_path / "memory.json"

        # Workflow 1: Store entries with first service
        storage1 = MemoryJsonStorage(path)
        service1 = MemoryService(storage1)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
            MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:02:00", 0.5, "id-3"),
        ]

        for entry in entries:
            service1.store(entry)

        # Workflow 2: Retrieve with second service instance
        storage2 = MemoryJsonStorage(path)
        service2 = MemoryService(storage2)
        loaded = service2.retrieve_all()

        assert len(loaded) == 3
        assert loaded[0].operation == "add"
        assert loaded[1].operation == "multiply"
        assert loaded[2].success is False
