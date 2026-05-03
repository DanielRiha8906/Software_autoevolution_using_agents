import pytest
from unittest.mock import MagicMock
from src.models.operation import Operation
from src.models.memory_entry import MemoryEntry
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService
from src.services.memory_service import MemoryService
from src.storage.json_storage import JsonStorage


class TestCalculatorServiceErrorHandling:
    """Test CalculatorService error handling with MemoryEntry."""

    def setup_method(self):
        self.storage_mock = MagicMock(spec=JsonStorage)
        self.memory_service = MemoryService(self.storage_mock)
        self.service = CalculatorService(Calculator(), self.memory_service)

    def test_perform_successful_calculation_returns_memory_entry(self):
        """Successful calculations return MemoryEntry with no error."""
        result = self.service.perform(Operation.ADD, 3, 5)
        assert isinstance(result, MemoryEntry)
        assert result.operation == "add"
        assert result.operand_a == 3
        assert result.operand_b == 5
        assert result.result == 8
        assert result.error is None
        assert result.error_type is None

    def test_perform_success_has_uuid_and_timestamp(self):
        """Successful MemoryEntry has UUID and timestamp."""
        result = self.service.perform(Operation.ADD, 1, 1)
        assert result.uuid != ""
        assert result.timestamp != ""

    def test_perform_successful_saves_to_storage(self):
        """Successful calculation saves to storage."""
        self.service.perform(Operation.ADD, 3, 5)
        self.storage_mock.save.assert_called_once()
        saved = self.storage_mock.save.call_args[0][0]
        assert isinstance(saved, MemoryEntry)
        assert saved.result == 8

    def test_perform_divide_by_zero_returns_error_memory_entry(self):
        """Division by zero returns error MemoryEntry, doesn't raise."""
        result = self.service.perform(Operation.DIVIDE, 5, 0)
        assert isinstance(result, MemoryEntry)
        assert result.operation == "divide"
        assert result.operand_a == 5
        assert result.operand_b == 0
        assert result.result is None
        assert result.error is not None
        assert result.error_type == "ValueError"

    def test_perform_divide_by_zero_saves_error(self):
        """Division by zero error is saved to storage."""
        result = self.service.perform(Operation.DIVIDE, 5, 0)
        self.storage_mock.save.assert_called_once()
        saved = self.storage_mock.save.call_args[0][0]
        assert saved.error is not None
        assert "Division by zero" in saved.error

    def test_perform_sqrt_negative_returns_error_memory_entry(self):
        """Square root of negative returns error MemoryEntry, doesn't raise."""
        result = self.service.perform(Operation.SQRT, -5, 0)
        assert isinstance(result, MemoryEntry)
        assert result.operation == "sqrt"
        assert result.operand_a == -5
        assert result.result is None
        assert result.error is not None
        assert result.error_type == "ValueError"

    def test_perform_sqrt_negative_saves_error(self):
        """Square root of negative error is saved to storage."""
        result = self.service.perform(Operation.SQRT, -1, 0)
        self.storage_mock.save.assert_called_once()
        saved = self.storage_mock.save.call_args[0][0]
        assert saved.error is not None
        assert "square root" in saved.error.lower()

    def test_perform_modulo_by_zero_returns_error_memory_entry(self):
        """Modulo by zero returns error MemoryEntry, doesn't raise."""
        result = self.service.perform(Operation.MODULO, 10, 0)
        assert isinstance(result, MemoryEntry)
        assert result.operation == "modulo"
        assert result.operand_a == 10
        assert result.operand_b == 0
        assert result.result is None
        assert result.error is not None
        assert result.error_type == "ValueError"

    def test_perform_modulo_by_zero_saves_error(self):
        """Modulo by zero error is saved to storage."""
        result = self.service.perform(Operation.MODULO, 10, 0)
        self.storage_mock.save.assert_called_once()
        saved = self.storage_mock.save.call_args[0][0]
        assert saved.error is not None
        assert "Modulo by zero" in saved.error

    def test_perform_error_has_all_fields_populated(self):
        """Error MemoryEntry has all fields including error info."""
        result = self.service.perform(Operation.DIVIDE, 5, 0)
        assert result.operation == "divide"
        assert result.operand_a == 5
        assert result.operand_b == 0
        assert result.result is None
        assert result.error is not None
        assert result.error_type is not None
        assert result.uuid != ""
        assert result.timestamp != ""

    def test_perform_always_saves_regardless_of_success(self):
        """Both successful and error results are saved."""
        success_result = self.service.perform(Operation.ADD, 1, 1)
        assert self.storage_mock.save.call_count == 1

        self.storage_mock.reset_mock()
        error_result = self.service.perform(Operation.DIVIDE, 5, 0)
        assert self.storage_mock.save.call_count == 1

    def test_get_history_returns_list_of_memory_entries(self):
        """get_history delegates to storage and returns MemoryEntry list."""
        mock_entries = [
            MemoryEntry("add", 1, 2, 3, None, None),
            MemoryEntry("divide", 5, 0, None, "error", "ValueError"),
        ]
        self.storage_mock.load_all.return_value = mock_entries
        history = self.service.get_history()
        assert len(history) == 2
        assert all(isinstance(e, MemoryEntry) for e in history)

    @pytest.mark.parametrize("a,b,expected_error", [
        (5, 0, "Division by zero"),
        (100, 0, "Division by zero"),
        (-5, 0, "Division by zero"),
    ])
    def test_perform_divide_by_zero_parametrized(self, a, b, expected_error):
        """Various division by zero scenarios."""
        result = self.service.perform(Operation.DIVIDE, a, b)
        assert result.result is None
        assert expected_error in result.error

    @pytest.mark.parametrize("a", [-1, -5, -100, -0.5])
    def test_perform_sqrt_negative_parametrized(self, a):
        """Various negative square root scenarios."""
        result = self.service.perform(Operation.SQRT, a, 0)
        assert result.result is None
        assert result.error is not None
        assert result.error_type == "ValueError"

    @pytest.mark.parametrize("a,b", [
        (10, 0),
        (5, 0),
        (-10, 0),
        (0, 0),
    ])
    def test_perform_modulo_by_zero_parametrized(self, a, b):
        """Various modulo by zero scenarios."""
        result = self.service.perform(Operation.MODULO, a, b)
        assert result.result is None
        assert result.error is not None

    def test_error_type_is_accurate(self):
        """error_type field correctly identifies the exception type."""
        result = self.service.perform(Operation.DIVIDE, 5, 0)
        assert result.error_type == "ValueError"

    def test_error_message_is_detailed(self):
        """error field contains the exception message."""
        result = self.service.perform(Operation.DIVIDE, 5, 0)
        assert result.error == "Division by zero is not allowed"

    def test_successful_operations_have_none_error_and_error_type(self):
        """Successful operations have None for both error fields."""
        test_cases = [
            (Operation.ADD, 1, 2),
            (Operation.SUBTRACT, 5, 3),
            (Operation.MULTIPLY, 4, 5),
            (Operation.DIVIDE, 10, 2),
            (Operation.SQUARE, 3, 0),
            (Operation.SQRT, 16, 0),
            (Operation.POWER, 2, 3),
            (Operation.MODULO, 10, 3),
        ]
        for op, a, b in test_cases:
            result = self.service.perform(op, a, b)
            assert result.error is None, f"Operation {op} should have None error"
            assert result.error_type is None, f"Operation {op} should have None error_type"
