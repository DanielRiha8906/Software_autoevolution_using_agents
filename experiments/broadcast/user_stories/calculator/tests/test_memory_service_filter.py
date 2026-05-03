"""Tests for MemoryService filtering integration."""

import pytest
import tempfile
import json
from pathlib import Path
from src.services.memory_service import MemoryService
from src.storage.json_storage import JsonStorage
from src.models.memory_entry import ResultEntry, ErrorEntry, _reset_id_counter


@pytest.fixture
def temp_storage_path():
    """Create a temporary storage file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_path = Path(f.name)
    yield temp_path
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def memory_service(temp_storage_path):
    """Provide a MemoryService with temporary storage."""
    return MemoryService(JsonStorage(temp_storage_path))


@pytest.fixture
def populated_service(memory_service):
    """Provide a MemoryService populated with test entries."""
    _reset_id_counter()
    entries = [
        ResultEntry(operation="add", operands=[2.0, 3.0], result=5.0),
        ResultEntry(operation="subtract", operands=[10.0, 4.0], result=6.0),
        ErrorEntry(operation="add", operands=[1.0, 2.0], error_message="Test error"),
        ResultEntry(operation="multiply", operands=[3.0, 4.0], result=12.0),
        ErrorEntry(operation="divide", operands=[10.0, 0.0], error_message="Division by zero"),
    ]
    for entry in entries:
        memory_service.store(entry)
    return memory_service


class TestMemoryServiceFilterEntries:
    """Test filter_entries method integration."""

    def test_filter_by_operation(self, populated_service):
        """Filter stored entries by operation."""
        results = populated_service.filter_entries(operation="add")
        assert len(results) == 2
        assert all(e.operation == "add" for e in results)

    def test_filter_by_state_success(self, populated_service):
        """Filter stored entries by success state."""
        results = populated_service.filter_entries(state="success")
        assert len(results) == 3
        assert all(isinstance(e, ResultEntry) for e in results)

    def test_filter_by_state_error(self, populated_service):
        """Filter stored entries by error state."""
        results = populated_service.filter_entries(state="error")
        assert len(results) == 2
        assert all(isinstance(e, ErrorEntry) for e in results)

    def test_filter_combined(self, populated_service):
        """Filter by both operation and state."""
        results = populated_service.filter_entries(operation="add", state="success")
        assert len(results) == 1
        assert results[0].operation == "add"
        assert isinstance(results[0], ResultEntry)

    def test_filter_combined_error(self, populated_service):
        """Filter by operation and error state."""
        results = populated_service.filter_entries(operation="add", state="error")
        assert len(results) == 1
        assert isinstance(results[0], ErrorEntry)

    def test_filter_no_matches(self, populated_service):
        """Filter with no matches returns empty list."""
        results = populated_service.filter_entries(operation="power")
        assert len(results) == 0

    def test_filter_no_parameters_returns_all(self, populated_service):
        """Filter with no parameters returns all entries."""
        results = populated_service.filter_entries()
        assert len(results) == 5

    def test_filter_invalid_state_raises_error(self, populated_service):
        """Invalid state raises ValueError."""
        with pytest.raises(ValueError, match="Invalid state"):
            populated_service.filter_entries(state="invalid")

    def test_filter_on_empty_storage(self, memory_service):
        """Filter on empty storage returns empty list."""
        results = memory_service.filter_entries(operation="add")
        assert results == []


class TestMemoryServiceGetValidOperations:
    """Test get_valid_operations method integration."""

    def test_get_valid_operations_from_storage(self, populated_service):
        """Get all unique operations from stored entries."""
        operations = populated_service.get_valid_operations()
        expected = ["add", "divide", "multiply", "subtract"]
        assert operations == expected

    def test_get_valid_operations_empty_storage(self, memory_service):
        """Get operations from empty storage returns empty list."""
        operations = memory_service.get_valid_operations()
        assert operations == []

    def test_get_valid_operations_single_operation(self, memory_service):
        """Get operations with only one type stored."""
        _reset_id_counter()
        memory_service.store(ResultEntry(operation="add", operands=[1.0, 2.0], result=3.0))
        memory_service.store(ResultEntry(operation="add", operands=[4.0, 5.0], result=9.0))
        operations = memory_service.get_valid_operations()
        assert operations == ["add"]


class TestMemoryServiceFilterPersistence:
    """Test that filtering works with persisted data."""

    def test_filter_persisted_entries(self, memory_service, temp_storage_path):
        """Filter entries that were previously persisted."""
        _reset_id_counter()
        # Store entries
        memory_service.store(ResultEntry(operation="add", operands=[1.0, 2.0], result=3.0))
        memory_service.store(ErrorEntry(operation="add", operands=[1.0, 2.0], error_message="Error"))
        memory_service.store(ResultEntry(operation="subtract", operands=[5.0, 3.0], result=2.0))

        # Create new service with same storage to simulate reload
        new_service = MemoryService(JsonStorage(temp_storage_path))
        results = new_service.filter_entries(operation="add")

        assert len(results) == 2
        assert all(e.operation == "add" for e in results)

    def test_filter_mixed_operations_and_states(self, memory_service):
        """Filter complex dataset with mixed operations and states."""
        _reset_id_counter()
        operations = ["add", "subtract", "multiply", "divide"]
        for i, op in enumerate(operations):
            # Add success
            memory_service.store(
                ResultEntry(operation=op, operands=[i + 1.0, 2.0], result=float(i + 3))
            )
            # Add error
            memory_service.store(
                ErrorEntry(operation=op, operands=[i + 1.0, 0.0], error_message=f"{op} error")
            )

        # All successes
        successes = memory_service.filter_entries(state="success")
        assert len(successes) == 4

        # All errors
        errors = memory_service.filter_entries(state="error")
        assert len(errors) == 4

        # Specific operation
        adds = memory_service.filter_entries(operation="add")
        assert len(adds) == 2

        # Specific operation and state
        add_success = memory_service.filter_entries(operation="add", state="success")
        assert len(add_success) == 1
        assert isinstance(add_success[0], ResultEntry)
