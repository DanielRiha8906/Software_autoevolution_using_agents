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


class TestCalculatorServiceNewOperations:
    """Test new mathematical operations in CalculatorService."""

    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    # ========== SQUARE operation tests ==========
    @pytest.mark.parametrize("a,expected", [
        (0, 0),
        (5, 25),
        (-3, 9),
        (0.5, 0.25),
    ])
    def test_perform_square(self, a, expected):
        """Test perform() with square operation."""
        result = self.service.perform(Operation.SQUARE, a, 999)  # b is ignored for unary
        assert result.result == expected
        assert result.operation == "square"
        assert result.operand_a == a

    def test_perform_square_saves_to_storage(self):
        """Test square operation result is saved to storage."""
        self.service.perform(Operation.SQUARE, 5, 0)
        self.storage.save.assert_called_once()
        saved: CalculationResult = self.storage.save.call_args[0][0]
        assert saved.result == 25
        assert saved.operation == "square"

    # ========== SQRT operation tests ==========
    @pytest.mark.parametrize("a,expected", [
        (0, 0),
        (4, 2),
        (9, 3),
        (0.25, 0.5),
    ])
    def test_perform_sqrt(self, a, expected):
        """Test perform() with sqrt operation."""
        result = self.service.perform(Operation.SQRT, a, 999)  # b is ignored for unary
        assert result.result == expected
        assert result.operation == "sqrt"
        assert result.operand_a == a

    def test_perform_sqrt_saves_to_storage(self):
        """Test sqrt operation result is saved to storage."""
        self.service.perform(Operation.SQRT, 16, 0)
        self.storage.save.assert_called_once()
        saved: CalculationResult = self.storage.save.call_args[0][0]
        assert saved.result == 4
        assert saved.operation == "sqrt"

    def test_perform_sqrt_negative_raises(self):
        """Test sqrt of negative raises ValueError."""
        with pytest.raises(ValueError, match="Cannot take square root of negative number"):
            self.service.perform(Operation.SQRT, -1, 0)

    def test_perform_sqrt_negative_does_not_save(self):
        """Test sqrt negative error doesn't save to storage."""
        with pytest.raises(ValueError):
            self.service.perform(Operation.SQRT, -5, 0)
        self.storage.save.assert_not_called()

    # ========== POWER operation tests ==========
    @pytest.mark.parametrize("a,b,expected", [
        (2, 3, 8),
        (5, 2, 25),
        (2, 0, 1),
        (2, -1, 0.5),
        (10, 0.5, pytest.approx(3.1622776601683795)),
    ])
    def test_perform_power(self, a, b, expected):
        """Test perform() with power operation."""
        result = self.service.perform(Operation.POWER, a, b)
        assert result.result == expected
        assert result.operation == "power"
        assert result.operand_a == a
        assert result.operand_b == b

    def test_perform_power_saves_to_storage(self):
        """Test power operation result is saved to storage."""
        self.service.perform(Operation.POWER, 2, 3)
        self.storage.save.assert_called_once()
        saved: CalculationResult = self.storage.save.call_args[0][0]
        assert saved.result == 8
        assert saved.operation == "power"

    # ========== MODULO operation tests ==========
    @pytest.mark.parametrize("a,b,expected", [
        (10, 3, 1),
        (7, 2, 1),
        (15, 4, 3),
        (0, 5, 0),
    ])
    def test_perform_modulo(self, a, b, expected):
        """Test perform() with modulo operation."""
        result = self.service.perform(Operation.MODULO, a, b)
        assert result.result == expected
        assert result.operation == "modulo"
        assert result.operand_a == a
        assert result.operand_b == b

    def test_perform_modulo_saves_to_storage(self):
        """Test modulo operation result is saved to storage."""
        self.service.perform(Operation.MODULO, 10, 3)
        self.storage.save.assert_called_once()
        saved: CalculationResult = self.storage.save.call_args[0][0]
        assert saved.result == 1
        assert saved.operation == "modulo"

    def test_perform_modulo_by_zero_raises(self):
        """Test modulo by zero raises ValueError."""
        with pytest.raises(ValueError, match="Modulo by zero is not allowed"):
            self.service.perform(Operation.MODULO, 10, 0)

    def test_perform_modulo_by_zero_does_not_save(self):
        """Test modulo by zero error doesn't save to storage."""
        with pytest.raises(ValueError):
            self.service.perform(Operation.MODULO, 5, 0)
        self.storage.save.assert_not_called()

    # ========== Execution timing for new operations ==========
    @pytest.mark.parametrize("operation,a,b", [
        (Operation.SQUARE, 5, 0),
        (Operation.SQRT, 16, 0),
        (Operation.POWER, 2, 3),
        (Operation.MODULO, 10, 3),
    ])
    def test_new_operations_have_execution_time(self, operation, a, b):
        """Test all new operations record execution time."""
        result = self.service.perform(operation, a, b)
        assert result.execution_time_ms > 0
        assert isinstance(result.execution_time_ms, float)
