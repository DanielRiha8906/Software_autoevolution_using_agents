import pytest
from pathlib import Path
from src.models.operation import Operation
from src.models.memory_entry import ResultEntry, ErrorEntry, _reset_id_counter
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService
from src.storage.json_storage import JsonStorage


class TestIntegration:
    @pytest.fixture
    def service(self, tmp_path):
        _reset_id_counter()
        storage_path = tmp_path / "calc.json"
        storage = JsonStorage(storage_path)
        return CalculatorService(Calculator(), storage)

    def test_perform_saves_calculation_result(self, service):
        result = service.perform(Operation.ADD, 3, 5)
        assert result.result == 8
        history = service.get_history()
        assert len(history) == 1
        assert history[0].operation == "add"

    def test_perform_with_memory_saves_memory_entry(self, service):
        entry = service.perform_with_memory(Operation.MULTIPLY, 2, 3)
        assert entry.result == 6
        memory = service.get_memory_history()
        assert len(memory) == 1
        assert isinstance(memory[0], ResultEntry)

    def test_perform_and_memory_coexist(self, service, tmp_path):
        """Verify both perform() and perform_with_memory() can save to separate files."""
        # Save a calculation result
        calc = service.perform(Operation.ADD, 1, 1)
        assert calc.result == 2

        # Save a memory entry (success case)
        mem = service.perform_with_memory(Operation.SUBTRACT, 5, 2)
        assert mem.result == 3

        # Both should be retrievable
        calc_history = service.get_history()
        memory_history = service.get_memory_history()
        assert len(calc_history) == 1
        assert len(memory_history) == 1

    def test_error_stored_in_memory(self, service):
        """Verify errors are stored in memory history."""
        with pytest.raises(ValueError):
            service.perform_with_memory(Operation.DIVIDE, 5, 0)

        memory = service.get_memory_history()
        assert len(memory) == 1
        assert isinstance(memory[0], ErrorEntry)
        assert memory[0].is_error() is True
        assert "Division by zero" in memory[0].error_message

    def test_mixed_operations_with_errors(self, service):
        """Test a sequence of successful and failed operations."""
        _reset_id_counter()
        # Success
        e1 = service.perform_with_memory(Operation.ADD, 2, 3)
        assert e1.result == 5
        # Error
        try:
            service.perform_with_memory(Operation.SQRT, -1, 0)
        except ValueError:
            pass
        # Success
        e3 = service.perform_with_memory(Operation.MULTIPLY, 3, 4)
        assert e3.result == 12

        memory = service.get_memory_history()
        assert len(memory) == 3
        assert memory[0].is_error() is False
        assert memory[1].is_error() is True
        assert memory[2].is_error() is False

    def test_sequential_ids_across_errors_and_results(self, service):
        """Verify entry IDs are sequential regardless of success/error."""
        _reset_id_counter()
        r1 = service.perform_with_memory(Operation.ADD, 1, 1)
        try:
            service.perform_with_memory(Operation.DIVIDE, 5, 0)
        except ValueError:
            pass
        r3 = service.perform_with_memory(Operation.SUBTRACT, 10, 3)

        memory = service.get_memory_history()
        assert memory[0].entry_id == 1
        assert memory[1].entry_id == 2
        assert memory[2].entry_id == 3

    def test_execution_time_recorded(self, service):
        """Verify execution time is recorded for both results and errors."""
        _reset_id_counter()
        result = service.perform_with_memory(Operation.ADD, 1, 1)
        assert result.execution_time_ms >= 0

        try:
            service.perform_with_memory(Operation.DIVIDE, 5, 0)
        except ValueError:
            pass
        memory = service.get_memory_history()
        error_entry = memory[1]
        assert error_entry.execution_time_ms >= 0

    def test_timestamp_recorded(self, service):
        """Verify timestamp is recorded for all entries."""
        _reset_id_counter()
        entry = service.perform_with_memory(Operation.MULTIPLY, 2, 3)
        assert entry.timestamp != ""
        assert "T" in entry.timestamp

    def test_operations_with_varying_operands(self, service):
        """Test that operands are correctly recorded."""
        _reset_id_counter()
        entry = service.perform_with_memory(Operation.POWER, 2, 10)
        assert entry.operands == [2, 10]
        assert entry.result == 1024
        memory = service.get_memory_history()
        assert memory[0].operands == [2, 10]

    def test_persistence_across_service_instances(self, tmp_path):
        """Verify data persists when creating new service instances."""
        _reset_id_counter()
        path = tmp_path / "calc.json"
        storage1 = JsonStorage(path)
        service1 = CalculatorService(Calculator(), storage1)

        entry1 = service1.perform_with_memory(Operation.ADD, 1, 2)
        assert entry1.result == 3

        # Create a new service instance with the same storage
        service2 = CalculatorService(Calculator(), storage1)
        memory = service2.get_memory_history()
        assert len(memory) == 1
        assert memory[0].result == 3


class TestMemoryServiceIntegration:
    @pytest.fixture
    def memory_service(self, tmp_path):
        _reset_id_counter()
        storage_path = tmp_path / "memory.json"
        storage = JsonStorage(storage_path)
        from src.services.memory_service import MemoryService
        return MemoryService(storage)

    def test_store_and_retrieve(self, memory_service):
        """Test storing and retrieving memory entries."""
        entry = ResultEntry(operation="add", operands=[1, 2], result=3)
        memory_service.store(entry)
        
        retrieved = memory_service.retrieve()
        assert len(retrieved) == 1
        assert retrieved[0].operation == "add"
        assert retrieved[0].result == 3

    def test_store_multiple_entries(self, memory_service):
        """Test storing and retrieving multiple entries."""
        _reset_id_counter()
        e1 = ResultEntry(operation="add", operands=[1, 2], result=3)
        e2 = ErrorEntry(operation="divide", operands=[5, 0], error_message="error")
        e3 = ResultEntry(operation="multiply", operands=[2, 3], result=6)
        
        memory_service.store(e1)
        memory_service.store(e2)
        memory_service.store(e3)
        
        retrieved = memory_service.retrieve()
        assert len(retrieved) == 3
        assert retrieved[0].operation == "add"
        assert retrieved[1].operation == "divide"
        assert retrieved[2].operation == "multiply"

    def test_persistence_across_instances(self, tmp_path):
        """Verify memory entries persist across service instances."""
        _reset_id_counter()
        path = tmp_path / "memory.json"
        storage1 = JsonStorage(path)
        from src.services.memory_service import MemoryService
        
        service1 = MemoryService(storage1)
        entry1 = ResultEntry(operation="add", operands=[1, 2], result=3)
        service1.store(entry1)
        
        # Create a new service instance with the same storage
        service2 = MemoryService(storage1)
        retrieved = service2.retrieve()
        assert len(retrieved) == 1
        assert retrieved[0].operation == "add"
        assert retrieved[0].result == 3

    def test_retrieve_preserves_entry_types(self, memory_service):
        """Verify that retrieved entries maintain their types."""
        _reset_id_counter()
        result_entry = ResultEntry(operation="add", operands=[1, 2], result=3)
        error_entry = ErrorEntry(operation="divide", operands=[5, 0], error_message="error")
        
        memory_service.store(result_entry)
        memory_service.store(error_entry)
        
        retrieved = memory_service.retrieve()
        assert len(retrieved) == 2
        assert isinstance(retrieved[0], ResultEntry)
        assert isinstance(retrieved[1], ErrorEntry)
        assert not retrieved[0].is_error()
        assert retrieved[1].is_error()
