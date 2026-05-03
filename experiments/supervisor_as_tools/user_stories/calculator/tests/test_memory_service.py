import pytest
from unittest.mock import MagicMock, patch
from src.models.memory_entry import MemoryEntry
from src.models.operation import Operation
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService
from src.services.memory_service import MemoryService
from src.storage.json_storage import JsonStorage


class TestMemoryServiceInitialization:
    """Test MemoryService initialization."""

    def test_initialization_with_calculator_service_and_storage(self):
        """Test MemoryService initialization with required dependencies."""
        calc_service = MagicMock()
        storage = MagicMock()
        memory_service = MemoryService(calc_service, storage)
        assert memory_service.calculator_service is calc_service
        assert memory_service.storage is storage


class TestMemoryServiceRecord:
    """Test MemoryService.record() method."""

    @pytest.fixture
    def setup(self):
        """Setup MemoryService with real Calculator and mock storage."""
        calc_service = CalculatorService(Calculator(), MagicMock())
        storage = MagicMock()
        return MemoryService(calc_service, storage), storage

    def test_record_successful_addition(self, setup):
        """Test record() with successful add operation (3 + 5 = 8)."""
        memory_service, storage = setup
        entry = memory_service.record("add", 3.0, 5.0)
        assert entry.operation_name == "add"
        assert entry.operand_a == 3.0
        assert entry.operand_b == 5.0
        assert entry.result == 8.0
        assert entry.success is True
        assert entry.error_message is None

    def test_record_successful_subtraction(self, setup):
        """Test record() with successful subtract operation."""
        memory_service, storage = setup
        entry = memory_service.record("subtract", 10.0, 4.0)
        assert entry.operation_name == "subtract"
        assert entry.result == 6.0
        assert entry.success is True

    def test_record_successful_multiplication(self, setup):
        """Test record() with successful multiply operation."""
        memory_service, storage = setup
        entry = memory_service.record("multiply", 3.0, 4.0)
        assert entry.operation_name == "multiply"
        assert entry.result == 12.0
        assert entry.success is True

    def test_record_successful_division(self, setup):
        """Test record() with successful divide operation."""
        memory_service, storage = setup
        entry = memory_service.record("divide", 9.0, 3.0)
        assert entry.operation_name == "divide"
        assert entry.result == 3.0
        assert entry.success is True

    def test_record_successful_square(self, setup):
        """Test record() with successful square operation."""
        memory_service, storage = setup
        entry = memory_service.record("square", 5.0, 0.0)
        assert entry.operation_name == "square"
        assert entry.result == 25.0
        assert entry.success is True

    def test_record_successful_sqrt(self, setup):
        """Test record() with successful sqrt operation."""
        memory_service, storage = setup
        entry = memory_service.record("sqrt", 9.0, 0.0)
        assert entry.operation_name == "sqrt"
        assert entry.result == 3.0
        assert entry.success is True

    def test_record_successful_power(self, setup):
        """Test record() with successful power operation."""
        memory_service, storage = setup
        entry = memory_service.record("power", 2.0, 3.0)
        assert entry.operation_name == "power"
        assert entry.result == 8.0
        assert entry.success is True

    def test_record_successful_modulo(self, setup):
        """Test record() with successful modulo operation."""
        memory_service, storage = setup
        entry = memory_service.record("modulo", 10.0, 3.0)
        assert entry.operation_name == "modulo"
        assert entry.result == 1.0
        assert entry.success is True

    def test_record_failed_divide_by_zero(self, setup):
        """Test record() with failed divide by zero operation."""
        memory_service, storage = setup
        entry = memory_service.record("divide", 5.0, 0.0)
        assert entry.operation_name == "divide"
        assert entry.operand_a == 5.0
        assert entry.operand_b == 0.0
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message is not None
        assert "Division by zero" in entry.error_message

    def test_record_failed_sqrt_negative(self, setup):
        """Test record() with failed sqrt of negative number."""
        memory_service, storage = setup
        entry = memory_service.record("sqrt", -4.0, 0.0)
        assert entry.operation_name == "sqrt"
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message is not None
        assert "negative" in entry.error_message.lower()

    def test_record_failed_modulo_by_zero(self, setup):
        """Test record() with failed modulo by zero."""
        memory_service, storage = setup
        entry = memory_service.record("modulo", 10.0, 0.0)
        assert entry.operation_name == "modulo"
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message is not None
        assert "zero" in entry.error_message.lower()

    def test_record_failed_power_zero_negative(self, setup):
        """Test record() with failed power (0 to negative exponent)."""
        memory_service, storage = setup
        entry = memory_service.record("power", 0.0, -1.0)
        assert entry.operation_name == "power"
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message is not None

    def test_record_invalid_operation_raises(self, setup):
        """Test record() with invalid operation raises ValueError."""
        memory_service, storage = setup
        with pytest.raises(ValueError, match="Invalid operation"):
            memory_service.record("invalid_op", 1.0, 2.0)

    def test_record_execution_time_is_measured(self, setup):
        """Test that record() measures execution_time_ms correctly."""
        memory_service, storage = setup
        entry = memory_service.record("add", 3.0, 5.0)
        assert entry.execution_time_ms >= 0
        # Should be very fast for a simple add, but allow reasonable upper bound
        assert entry.execution_time_ms < 1000

    def test_record_execution_time_measured_for_failed(self, setup):
        """Test that record() measures execution_time_ms even on failure."""
        memory_service, storage = setup
        entry = memory_service.record("divide", 5.0, 0.0)
        assert entry.execution_time_ms >= 0

    def test_record_saves_to_storage(self, setup):
        """Test that record() saves the entry to storage."""
        memory_service, storage = setup
        entry = memory_service.record("add", 3.0, 5.0)
        storage.save.assert_called_once()
        saved_entry = storage.save.call_args[0][0]
        assert saved_entry is entry

    def test_record_saves_failed_entry_to_storage(self, setup):
        """Test that record() saves failed entries to storage."""
        memory_service, storage = setup
        entry = memory_service.record("divide", 5.0, 0.0)
        storage.save.assert_called_once()
        saved_entry = storage.save.call_args[0][0]
        assert saved_entry.success is False

    def test_record_with_mixed_case_operation(self, setup):
        """Test record() with mixed case operation name."""
        memory_service, storage = setup
        entry = memory_service.record("ADD", 2.0, 3.0)
        assert entry.operation_name == "add"
        assert entry.result == 5.0

    @pytest.mark.parametrize("op_name", ["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"])
    def test_record_all_operations(self, setup, op_name):
        """Test record() with all operation types."""
        memory_service, storage = setup
        # Use operands that won't fail for most operations
        operand_a = 5.0 if op_name != "sqrt" else 9.0
        operand_b = 3.0
        entry = memory_service.record(op_name, operand_a, operand_b)
        assert entry.operation_name == op_name
        assert entry.operand_a == operand_a
        assert entry.operand_b == operand_b

    def test_record_returns_memory_entry_instance(self, setup):
        """Test that record() returns a MemoryEntry instance."""
        memory_service, storage = setup
        entry = memory_service.record("add", 1.0, 2.0)
        assert isinstance(entry, MemoryEntry)


class TestMemoryServiceGetAllEntries:
    """Test MemoryService.get_all_entries() method."""

    def test_get_all_entries_returns_list(self):
        """Test get_all_entries() returns a list."""
        calc_service = MagicMock()
        storage = MagicMock()
        storage.load_all.return_value = []
        memory_service = MemoryService(calc_service, storage)
        entries = memory_service.get_all_entries()
        assert isinstance(entries, list)

    def test_get_all_entries_empty_when_no_entries(self):
        """Test get_all_entries() returns empty list when no entries."""
        calc_service = MagicMock()
        storage = MagicMock()
        storage.load_all.return_value = []
        memory_service = MemoryService(calc_service, storage)
        entries = memory_service.get_all_entries()
        assert entries == []

    def test_get_all_entries_returns_memory_entries(self):
        """Test get_all_entries() returns list of MemoryEntry objects."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        entry2 = MemoryEntry("subtract", 5.0, 3.0, 2.0, True)
        storage.load_all.return_value = [entry1, entry2]
        memory_service = MemoryService(calc_service, storage)
        entries = memory_service.get_all_entries()
        assert len(entries) == 2
        assert entries[0] is entry1
        assert entries[1] is entry2

    def test_get_all_entries_filters_out_non_memory_entries(self):
        """Test get_all_entries() filters to only MemoryEntry objects."""
        from src.models.calculation_result import CalculationResult
        calc_service = MagicMock()
        storage = MagicMock()
        memory_entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        calc_result = CalculationResult("subtract", 5.0, 3.0, 2.0, "2026-01-01T00:00:00")
        storage.load_all.return_value = [memory_entry, calc_result]
        memory_service = MemoryService(calc_service, storage)
        entries = memory_service.get_all_entries()
        # Should only get MemoryEntry
        assert len(entries) == 1
        assert entries[0] is memory_entry

    def test_get_all_entries_calls_storage_load_all(self):
        """Test get_all_entries() calls storage.load_all()."""
        calc_service = MagicMock()
        storage = MagicMock()
        storage.load_all.return_value = []
        memory_service = MemoryService(calc_service, storage)
        memory_service.get_all_entries()
        storage.load_all.assert_called_once()


class TestMemoryServiceFilterByOperation:
    """Test MemoryService.filter_by_operation() method."""

    def test_filter_by_operation_returns_list(self):
        """Test filter_by_operation() returns a list."""
        calc_service = MagicMock()
        storage = MagicMock()
        storage.load_all.return_value = []
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter_by_operation("add")
        assert isinstance(result, list)

    def test_filter_by_operation_single_match(self):
        """Test filter_by_operation() with single matching entry."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        storage.load_all.return_value = [entry]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter_by_operation("add")
        assert len(result) == 1
        assert result[0] is entry

    def test_filter_by_operation_multiple_matches(self):
        """Test filter_by_operation() with multiple matching entries."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        entry2 = MemoryEntry("add", 5.0, 3.0, 8.0, True)
        entry3 = MemoryEntry("subtract", 10.0, 3.0, 7.0, True)
        storage.load_all.return_value = [entry1, entry2, entry3]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter_by_operation("add")
        assert len(result) == 2
        assert entry1 in result
        assert entry2 in result
        assert entry3 not in result

    def test_filter_by_operation_no_matches(self):
        """Test filter_by_operation() with no matching entries."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        storage.load_all.return_value = [entry]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter_by_operation("multiply")
        assert len(result) == 0

    def test_filter_by_operation_case_insensitive(self):
        """Test filter_by_operation() is case-insensitive."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        storage.load_all.return_value = [entry]
        memory_service = MemoryService(calc_service, storage)
        result1 = memory_service.filter_by_operation("ADD")
        result2 = memory_service.filter_by_operation("Add")
        result3 = memory_service.filter_by_operation("add")
        assert len(result1) == 1
        assert len(result2) == 1
        assert len(result3) == 1

    def test_filter_by_operation_returns_memory_entries(self):
        """Test filter_by_operation() returns MemoryEntry instances."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        storage.load_all.return_value = [entry]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter_by_operation("add")
        assert all(isinstance(e, MemoryEntry) for e in result)


class TestMemoryServiceFilterBySuccess:
    """Test MemoryService.filter_by_success() method."""

    def test_filter_by_success_returns_list(self):
        """Test filter_by_success() returns a list."""
        calc_service = MagicMock()
        storage = MagicMock()
        storage.load_all.return_value = []
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter_by_success(True)
        assert isinstance(result, list)

    def test_filter_by_success_true_single_match(self):
        """Test filter_by_success(True) with single successful entry."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        storage.load_all.return_value = [entry]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter_by_success(True)
        assert len(result) == 1
        assert result[0] is entry

    def test_filter_by_success_true_multiple_matches(self):
        """Test filter_by_success(True) with multiple successful entries."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        entry2 = MemoryEntry("subtract", 5.0, 3.0, 2.0, True)
        entry3 = MemoryEntry("divide", 5.0, 0.0, None, False)
        storage.load_all.return_value = [entry1, entry2, entry3]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter_by_success(True)
        assert len(result) == 2
        assert entry1 in result
        assert entry2 in result
        assert entry3 not in result

    def test_filter_by_success_false_single_match(self):
        """Test filter_by_success(False) with single failed entry."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry = MemoryEntry("divide", 5.0, 0.0, None, False, error_message="Division by zero")
        storage.load_all.return_value = [entry]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter_by_success(False)
        assert len(result) == 1
        assert result[0] is entry

    def test_filter_by_success_false_multiple_matches(self):
        """Test filter_by_success(False) with multiple failed entries."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry1 = MemoryEntry("divide", 5.0, 0.0, None, False, error_message="Division by zero")
        entry2 = MemoryEntry("sqrt", -4.0, 0.0, None, False, error_message="negative")
        entry3 = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        storage.load_all.return_value = [entry1, entry2, entry3]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter_by_success(False)
        assert len(result) == 2
        assert entry1 in result
        assert entry2 in result
        assert entry3 not in result

    def test_filter_by_success_no_matches(self):
        """Test filter_by_success() with no matching entries."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        storage.load_all.return_value = [entry]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter_by_success(False)
        assert len(result) == 0

    def test_filter_by_success_returns_memory_entries(self):
        """Test filter_by_success() returns MemoryEntry instances."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        storage.load_all.return_value = [entry]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter_by_success(True)
        assert all(isinstance(e, MemoryEntry) for e in result)


class TestMemoryServiceFilter:
    """Test MemoryService.filter() method."""

    def test_filter_returns_list(self):
        """Test filter() returns a list."""
        calc_service = MagicMock()
        storage = MagicMock()
        storage.load_all.return_value = []
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter()
        assert isinstance(result, list)

    def test_filter_both_none_returns_all(self):
        """Test filter() with both parameters None returns all entries."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        entry2 = MemoryEntry("subtract", 5.0, 3.0, 2.0, True)
        entry3 = MemoryEntry("divide", 5.0, 0.0, None, False, error_message="Division by zero")
        storage.load_all.return_value = [entry1, entry2, entry3]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter()
        assert len(result) == 3

    def test_filter_operation_only(self):
        """Test filter() with operation_name only."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        entry2 = MemoryEntry("add", 5.0, 3.0, 8.0, True)
        entry3 = MemoryEntry("subtract", 10.0, 3.0, 7.0, True)
        storage.load_all.return_value = [entry1, entry2, entry3]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter(operation_name="add")
        assert len(result) == 2
        assert entry1 in result
        assert entry2 in result

    def test_filter_success_only(self):
        """Test filter() with success only."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        entry2 = MemoryEntry("divide", 5.0, 0.0, None, False, error_message="Division by zero")
        entry3 = MemoryEntry("subtract", 10.0, 3.0, 7.0, True)
        storage.load_all.return_value = [entry1, entry2, entry3]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter(success=True)
        assert len(result) == 2
        assert entry1 in result
        assert entry3 in result

    def test_filter_both_criteria(self):
        """Test filter() with both operation_name and success."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        entry2 = MemoryEntry("add", 5.0, 0.0, None, False, error_message="error")
        entry3 = MemoryEntry("subtract", 10.0, 3.0, 7.0, True)
        storage.load_all.return_value = [entry1, entry2, entry3]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter(operation_name="add", success=True)
        assert len(result) == 1
        assert entry1 in result

    def test_filter_operation_case_insensitive(self):
        """Test filter() with operation_name is case-insensitive."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        storage.load_all.return_value = [entry]
        memory_service = MemoryService(calc_service, storage)
        result1 = memory_service.filter(operation_name="ADD")
        result2 = memory_service.filter(operation_name="Add")
        assert len(result1) == 1
        assert len(result2) == 1

    def test_filter_operation_no_matches(self):
        """Test filter() with operation_name that has no matches."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        storage.load_all.return_value = [entry]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter(operation_name="multiply")
        assert len(result) == 0

    def test_filter_success_false_no_matches(self):
        """Test filter() with success=False with no failed entries."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        storage.load_all.return_value = [entry]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter(success=False)
        assert len(result) == 0

    def test_filter_both_criteria_no_matches(self):
        """Test filter() with both criteria having no matches."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry1 = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        entry2 = MemoryEntry("subtract", 5.0, 3.0, 2.0, True)
        storage.load_all.return_value = [entry1, entry2]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter(operation_name="add", success=False)
        assert len(result) == 0

    def test_filter_returns_memory_entries(self):
        """Test filter() returns MemoryEntry instances."""
        calc_service = MagicMock()
        storage = MagicMock()
        entry = MemoryEntry("add", 1.0, 2.0, 3.0, True)
        storage.load_all.return_value = [entry]
        memory_service = MemoryService(calc_service, storage)
        result = memory_service.filter(operation_name="add")
        assert all(isinstance(e, MemoryEntry) for e in result)
