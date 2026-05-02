import pytest
from unittest.mock import MagicMock
from src.models.operation import Operation
from src.models.calculation_result import CalculationResult
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService


class TestCalculatorService:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_add_returns_result(self):
        result = self.service.perform(Operation.ADD, 3, 5)
        assert result.result == 8
        assert result.operation == "add"
        assert result.operand_a == 3
        assert result.operand_b == 5

    def test_perform_subtract(self):
        assert self.service.perform(Operation.SUBTRACT, 10, 4).result == 6

    def test_perform_multiply(self):
        assert self.service.perform(Operation.MULTIPLY, 3, 4).result == 12

    def test_perform_divide(self):
        assert self.service.perform(Operation.DIVIDE, 9, 3).result == 3.0

    def test_perform_saves_to_storage(self):
        self.service.perform(Operation.ADD, 3, 5)
        self.storage.save.assert_called_once()
        saved: CalculationResult = self.storage.save.call_args[0][0]
        assert saved.result == 8

    def test_perform_divide_by_zero_raises(self):
        with pytest.raises(ValueError, match="Division by zero"):
            self.service.perform(Operation.DIVIDE, 5, 0)

    def test_perform_divide_by_zero_does_not_save(self):
        with pytest.raises(ValueError):
            self.service.perform(Operation.DIVIDE, 5, 0)
        self.storage.save.assert_not_called()

    def test_get_history_delegates_to_storage(self):
        mock_history = [CalculationResult("add", 1, 2, 3, "2026-01-01T00:00:00")]
        self.storage.load_all.return_value = mock_history
        assert self.service.get_history() == mock_history

    def test_result_has_timestamp(self):
        result = self.service.perform(Operation.ADD, 1, 1)
        assert result.timestamp != ""


class TestCalculatorServiceExecutionTiming:
    """Test execution time tracking in CalculatorService.perform()."""

    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_measures_execution_time(self):
        """Test 5: Service.perform() measures and assigns execution_time_ms."""
        result = self.service.perform(Operation.ADD, 3, 5)
        assert result.execution_time_ms > 0
        assert isinstance(result.execution_time_ms, float)

    def test_execution_time_in_milliseconds(self):
        """Test 6: execution_time_ms value is reasonable (milliseconds not microseconds/seconds)."""
        result = self.service.perform(Operation.ADD, 10, 20)
        assert result.execution_time_ms < 1000, "Execution time should be less than 1000ms for simple arithmetic"
        assert result.execution_time_ms >= 0

    @pytest.mark.parametrize("operation,a,b", [
        (Operation.ADD, 5, 3),
        (Operation.SUBTRACT, 10, 4),
        (Operation.MULTIPLY, 7, 6),
        (Operation.DIVIDE, 20, 4),
    ])
    def test_different_operations_have_measurable_timing(self, operation, a, b):
        """Test 7: Different operations have measurable timing > 0 and < 50ms."""
        result = self.service.perform(operation, a, b)
        assert result.execution_time_ms > 0, f"{operation.value} should have measurable execution time"
        assert result.execution_time_ms < 50, f"{operation.value} timing should be under 50ms"

    def test_division_by_zero_no_record_saved(self):
        """Test 8: Division by zero error handling - no record saved."""
        with pytest.raises(ValueError):
            self.service.perform(Operation.DIVIDE, 5, 0)
        self.storage.save.assert_not_called()

    def test_execution_time_in_saved_record(self):
        """Test 5b: Saved record includes execution_time_ms."""
        self.service.perform(Operation.MULTIPLY, 3, 4)
        self.storage.save.assert_called_once()
        saved: CalculationResult = self.storage.save.call_args[0][0]
        assert saved.execution_time_ms > 0

    def test_execution_time_positive_for_all_operations(self):
        """Test 7b: All operations have positive execution time."""
        for operation in [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE]:
            self.storage.reset_mock()
            result = self.service.perform(operation, 10, 5)
            assert result.execution_time_ms > 0, f"{operation.value} should have positive execution time"
