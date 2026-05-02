import pytest
from unittest.mock import MagicMock, call
from src.models.operation import Operation
from src.models.calculation_result import CalculationResult
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService


class TestMemoryServiceInitialization:
    def test_memory_service_initialization(self):
        """Test MemoryService initializes with calculator_service and storage."""
        calculator_service = MagicMock()
        storage = MagicMock()

        service = MemoryService(calculator_service, storage)

        assert service.calculator_service is calculator_service
        assert service.storage is storage


class TestMemoryServiceStore:
    def test_store_saves_entry(self):
        """Test store() calls storage.save() with the entry."""
        calculator_service = MagicMock()
        storage = MagicMock()
        service = MemoryService(calculator_service, storage)

        entry = MemoryEntry.success(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
        )

        service.store(entry)

        storage.save.assert_called_once_with(entry)


class TestMemoryServiceRetrieveAll:
    def test_retrieve_all_returns_all_entries(self):
        """Test retrieve_all() returns list of MemoryEntry objects from storage."""
        calculator_service = MagicMock()
        storage = MagicMock()
        service = MemoryService(calculator_service, storage)

        # Setup mock storage to return CalculationResult objects
        calc_results = [
            CalculationResult("add", 1.0, 2.0, 3.0),
            CalculationResult("subtract", 5.0, 2.0, 3.0),
        ]
        storage.load_all.return_value = calc_results

        entries = service.retrieve_all()

        assert len(entries) == 2
        assert all(isinstance(e, MemoryEntry) for e in entries)
        assert entries[0].operation == "add"
        assert entries[0].result == 3.0
        assert entries[0].status == "success"
        assert entries[1].operation == "subtract"
        assert entries[1].result == 3.0

    def test_retrieve_all_returns_empty_list_when_no_entries(self):
        """Test retrieve_all() returns empty list when no entries exist."""
        calculator_service = MagicMock()
        storage = MagicMock()
        service = MemoryService(calculator_service, storage)

        storage.load_all.return_value = []

        entries = service.retrieve_all()

        assert entries == []


class TestMemoryServicePerform:
    def test_perform_successful_calculation(self):
        """Test perform() on successful calculation saves success MemoryEntry."""
        calculator_service = MagicMock()
        storage = MagicMock()
        service = MemoryService(calculator_service, storage)

        # Setup mock calculator_service to return a result
        expected_result = CalculationResult(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
        )
        calculator_service.perform.return_value = expected_result

        result = service.perform(Operation.ADD, 3.0, 5.0)

        # Verify calculator_service was called
        calculator_service.perform.assert_called_once_with(Operation.ADD, 3.0, 5.0)

        # Verify result is returned unchanged
        assert result == expected_result

        # Verify storage.save was called with a MemoryEntry
        storage.save.assert_called_once()
        saved_entry = storage.save.call_args[0][0]
        assert isinstance(saved_entry, MemoryEntry)
        assert saved_entry.operation == "add"
        assert saved_entry.operand_a == 3.0
        assert saved_entry.operand_b == 5.0
        assert saved_entry.result == 8.0
        assert saved_entry.status == "success"
        assert saved_entry.error_message is None

    def test_perform_division_by_zero_creates_error_entry(self):
        """Test perform() on division by zero saves error MemoryEntry and re-raises."""
        calculator_service = MagicMock()
        storage = MagicMock()
        service = MemoryService(calculator_service, storage)

        # Setup mock calculator_service to raise ValueError
        error_msg = "Division by zero is not allowed"
        calculator_service.perform.side_effect = ValueError(error_msg)

        # Verify ValueError is re-raised
        with pytest.raises(ValueError, match="Division by zero"):
            service.perform(Operation.DIVIDE, 5.0, 0.0)

        # Verify calculator_service was called
        calculator_service.perform.assert_called_once_with(Operation.DIVIDE, 5.0, 0.0)

        # Verify storage.save was called with a MemoryEntry
        storage.save.assert_called_once()
        saved_entry = storage.save.call_args[0][0]
        assert isinstance(saved_entry, MemoryEntry)
        assert saved_entry.operation == "divide"
        assert saved_entry.operand_a == 5.0
        assert saved_entry.operand_b == 0.0
        assert saved_entry.result is None
        assert saved_entry.status == "error"
        assert saved_entry.error_message == error_msg

    def test_perform_saves_with_execution_time(self):
        """Test perform() saves MemoryEntry with execution_time_ms."""
        calculator_service = MagicMock()
        storage = MagicMock()
        service = MemoryService(calculator_service, storage)

        expected_result = CalculationResult(
            operation="multiply",
            operand_a=3.0,
            operand_b=4.0,
            result=12.0,
        )
        calculator_service.perform.return_value = expected_result

        service.perform(Operation.MULTIPLY, 3.0, 4.0)

        saved_entry = storage.save.call_args[0][0]
        assert saved_entry.execution_time_ms >= 0.0


class TestMemoryServiceGetHistory:
    def test_get_history_delegates_to_calculator_service(self):
        """Test get_history() delegates to calculator_service.get_history()."""
        calculator_service = MagicMock()
        storage = MagicMock()
        service = MemoryService(calculator_service, storage)

        mock_history = [
            CalculationResult("add", 1.0, 2.0, 3.0, "2026-01-01T00:00:00"),
            CalculationResult("subtract", 5.0, 2.0, 3.0, "2026-01-01T00:00:01"),
        ]
        calculator_service.get_history.return_value = mock_history

        history = service.get_history()

        calculator_service.get_history.assert_called_once()
        assert history == mock_history
        assert len(history) == 2
