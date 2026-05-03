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


class TestMemoryServiceFilterByOperation:
    """Test MemoryService.filter_by_operation() method."""

    @pytest.fixture
    def service_with_data(self, tmp_path):
        """Fixture providing service with pre-populated diverse entries."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
            MemoryEntry("add", 5.0, 5.0, 10.0, True, None, "2026-05-03T10:02:00", 1.5, "id-3"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:03:00", 2.0, "id-4"),
            MemoryEntry("divide", 20.0, 4.0, 5.0, True, None, "2026-05-03T10:04:00", 1.2, "id-5"),
            MemoryEntry("add", 100.0, 50.0, 150.0, True, None, "2026-05-03T10:05:00", 0.8, "id-6"),
        ]

        for entry in entries:
            service.store(entry)

        return service

    def test_filter_by_operation_exact_match_lowercase(self, service_with_data):
        """Test 1: Filter by operation with exact lowercase match."""
        result = service_with_data.filter_by_operation("add")
        assert len(result) == 3
        assert all(entry.operation == "add" for entry in result)
        assert result[0].operand_a == 1.0
        assert result[1].operand_a == 5.0
        assert result[2].operand_a == 100.0

    def test_filter_by_operation_case_insensitive_uppercase(self, service_with_data):
        """Test 2: Filter by operation is case-insensitive (uppercase)."""
        result = service_with_data.filter_by_operation("ADD")
        assert len(result) == 3
        assert all(entry.operation == "add" for entry in result)

    def test_filter_by_operation_case_insensitive_mixed(self, service_with_data):
        """Test 3: Filter by operation is case-insensitive (mixed case)."""
        result = service_with_data.filter_by_operation("SuBtRaCt")
        assert len(result) == 1
        assert result[0].operation == "subtract"

    def test_filter_by_operation_single_result(self, service_with_data):
        """Test 4: Filter returning single result."""
        result = service_with_data.filter_by_operation("multiply")
        assert len(result) == 1
        assert result[0].operation == "multiply"
        assert result[0].result == 20.0

    def test_filter_by_operation_no_matches(self, service_with_data):
        """Test 5: Filter with no matching operations returns empty list."""
        result = service_with_data.filter_by_operation("power")
        assert result == []
        assert isinstance(result, list)

    def test_filter_by_operation_empty_storage(self, tmp_path):
        """Test 6: Filter on empty storage returns empty list."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        result = service.filter_by_operation("add")
        assert result == []

    def test_filter_by_operation_preserves_order(self, service_with_data):
        """Test 7: Filter results preserve insertion order."""
        result = service_with_data.filter_by_operation("add")
        assert len(result) == 3
        # Verify insertion order is maintained
        assert result[0].operand_a == 1.0
        assert result[1].operand_a == 5.0
        assert result[2].operand_a == 100.0
        assert result[0].execution_timestamp < result[1].execution_timestamp < result[2].execution_timestamp


class TestMemoryServiceFilterBySuccess:
    """Test MemoryService.filter_by_success() method."""

    @pytest.fixture
    def service_with_mixed_results(self, tmp_path):
        """Fixture with both successful and failed entries."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:01:00", 0.5, "id-2"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:02:00", 2.0, "id-3"),
            MemoryEntry("sqrt", -4.0, 0.0, None, False, "Cannot take sqrt of negative", "2026-05-03T10:03:00", 0.8, "id-4"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:04:00", 1.2, "id-5"),
        ]

        for entry in entries:
            service.store(entry)

        return service

    def test_filter_by_success_true(self, service_with_mixed_results):
        """Test 1: Filter for successful operations only."""
        result = service_with_mixed_results.filter_by_success(True)
        assert len(result) == 3
        assert all(entry.success is True for entry in result)
        assert all(entry.error_message is None for entry in result)

    def test_filter_by_success_false(self, service_with_mixed_results):
        """Test 2: Filter for failed operations only."""
        result = service_with_mixed_results.filter_by_success(False)
        assert len(result) == 2
        assert all(entry.success is False for entry in result)
        assert all(entry.error_message is not None for entry in result)

    def test_filter_by_success_all_successful(self, tmp_path):
        """Test 3: Filter success=True when all entries are successful."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 1.0, "id-1"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:01:00", 2.0, "id-2"),
        ]

        for entry in entries:
            service.store(entry)

        result = service.filter_by_success(True)
        assert len(result) == 2
        assert all(entry.success is True for entry in result)

        result_false = service.filter_by_success(False)
        assert result_false == []

    def test_filter_by_success_all_failed(self, tmp_path):
        """Test 4: Filter success=False when all entries are failed."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("divide", 10.0, 0.0, None, False, "Division by zero", "2026-05-03T10:00:00", 0.5, "id-1"),
            MemoryEntry("sqrt", -4.0, 0.0, None, False, "Cannot take sqrt of negative", "2026-05-03T10:01:00", 0.8, "id-2"),
        ]

        for entry in entries:
            service.store(entry)

        result = service.filter_by_success(False)
        assert len(result) == 2
        assert all(entry.success is False for entry in result)

        result_true = service.filter_by_success(True)
        assert result_true == []

    def test_filter_by_success_empty_storage(self, tmp_path):
        """Test 5: Filter on empty storage returns empty list."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        result_true = service.filter_by_success(True)
        result_false = service.filter_by_success(False)

        assert result_true == []
        assert result_false == []

    def test_filter_by_success_preserves_order(self, service_with_mixed_results):
        """Test 6: Filter results preserve insertion order."""
        result = service_with_mixed_results.filter_by_success(True)
        assert len(result) == 3
        # Verify timestamps are in ascending order
        assert result[0].execution_timestamp < result[1].execution_timestamp < result[2].execution_timestamp


class TestMemoryServiceFilterByExecutionTime:
    """Test MemoryService.filter_by_execution_time() method."""

    @pytest.fixture
    def service_with_varied_times(self, tmp_path):
        """Fixture with entries having varied execution times."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entries = [
            MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 0.5, "id-1"),
            MemoryEntry("subtract", 10.0, 3.0, 7.0, True, None, "2026-05-03T10:01:00", 1.5, "id-2"),
            MemoryEntry("multiply", 4.0, 5.0, 20.0, True, None, "2026-05-03T10:02:00", 2.5, "id-3"),
            MemoryEntry("divide", 20.0, 4.0, 5.0, True, None, "2026-05-03T10:03:00", 3.5, "id-4"),
            MemoryEntry("power", 2.0, 10.0, 1024.0, True, None, "2026-05-03T10:04:00", 5.0, "id-5"),
        ]

        for entry in entries:
            service.store(entry)

        return service

    def test_filter_by_execution_time_range_middle(self, service_with_varied_times):
        """Test 1: Filter execution time in middle range."""
        result = service_with_varied_times.filter_by_execution_time(min_ms=1.0, max_ms=3.0)
        assert len(result) == 2
        assert all(1.0 <= entry.execution_time_ms <= 3.0 for entry in result)

    def test_filter_by_execution_time_inclusive_bounds(self, service_with_varied_times):
        """Test 2: Filter with inclusive bounds (exact matches included)."""
        result = service_with_varied_times.filter_by_execution_time(min_ms=1.5, max_ms=3.5)
        assert len(result) == 3
        # Should include entries with exactly 1.5 and 3.5
        times = [entry.execution_time_ms for entry in result]
        assert 1.5 in times
        assert 3.5 in times

    def test_filter_by_execution_time_single_result(self, service_with_varied_times):
        """Test 3: Filter returning single result."""
        result = service_with_varied_times.filter_by_execution_time(min_ms=5.0, max_ms=5.0)
        assert len(result) == 1
        assert result[0].execution_time_ms == 5.0

    def test_filter_by_execution_time_no_matches(self, service_with_varied_times):
        """Test 4: Filter with no matches returns empty list."""
        result = service_with_varied_times.filter_by_execution_time(min_ms=10.0, max_ms=20.0)
        assert result == []

    def test_filter_by_execution_time_default_min(self, service_with_varied_times):
        """Test 5: Filter with default min_ms=0.0."""
        result = service_with_varied_times.filter_by_execution_time(max_ms=2.0)
        assert len(result) == 2
        assert all(entry.execution_time_ms <= 2.0 for entry in result)

    def test_filter_by_execution_time_default_max(self, service_with_varied_times):
        """Test 6: Filter with default max_ms=infinity."""
        result = service_with_varied_times.filter_by_execution_time(min_ms=3.0)
        assert len(result) == 2
        assert all(entry.execution_time_ms >= 3.0 for entry in result)

    def test_filter_by_execution_time_no_args_returns_all(self, service_with_varied_times):
        """Test 7: Filter with no arguments returns all entries."""
        result = service_with_varied_times.filter_by_execution_time()
        assert len(result) == 5

    def test_filter_by_execution_time_empty_storage(self, tmp_path):
        """Test 8: Filter on empty storage returns empty list."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        result = service.filter_by_execution_time(min_ms=1.0, max_ms=10.0)
        assert result == []

    def test_filter_by_execution_time_zero_duration(self, tmp_path):
        """Test 9: Filter for zero-duration execution."""
        storage = MemoryJsonStorage(tmp_path / "memory.json")
        service = MemoryService(storage)

        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True, None, "2026-05-03T10:00:00", 0.0, "id-1")
        service.store(entry)

        result = service.filter_by_execution_time(min_ms=0.0, max_ms=0.0)
        assert len(result) == 1
        assert result[0].execution_time_ms == 0.0

    def test_filter_by_execution_time_preserves_order(self, service_with_varied_times):
        """Test 10: Filter results preserve insertion order."""
        result = service_with_varied_times.filter_by_execution_time(min_ms=0.5, max_ms=4.0)
        assert len(result) == 4
        # Verify execution times are in ascending order
        times = [entry.execution_time_ms for entry in result]
        assert times == sorted(times)


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
