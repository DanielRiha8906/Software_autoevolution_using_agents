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
        assert result.execution_time_ms > 0

    def test_perform_subtract(self):
        result = self.service.perform(Operation.SUBTRACT, 10, 4)
        assert result.result == 6
        assert result.execution_time_ms > 0

    def test_perform_multiply(self):
        result = self.service.perform(Operation.MULTIPLY, 3, 4)
        assert result.result == 12
        assert result.execution_time_ms > 0

    def test_perform_divide(self):
        result = self.service.perform(Operation.DIVIDE, 9, 3)
        assert result.result == 3.0
        assert result.execution_time_ms > 0

    def test_perform_saves_to_storage(self):
        self.service.perform(Operation.ADD, 3, 5)
        self.storage.save.assert_called_once()
        saved: CalculationResult = self.storage.save.call_args[0][0]
        assert saved.result == 8
        assert saved.execution_time_ms > 0

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

    def test_perform_execution_time_is_measured(self):
        result = self.service.perform(Operation.ADD, 3, 5)
        assert 0 < result.execution_time_ms < 100

    def test_perform_execution_time_all_operations(self):
        for operation in [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE,
                          Operation.SQUARE, Operation.SQRT, Operation.POWER, Operation.MODULO]:
            result = self.service.perform(operation, 3, 5)
            assert result.execution_time_ms > 0


class TestServiceSquare:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_square_returns_result(self):
        result = self.service.perform(Operation.SQUARE, 5, 0)
        assert result.result == 25

    def test_perform_square_saves_to_storage(self):
        self.service.perform(Operation.SQUARE, 5, 0)
        self.storage.save.assert_called_once()

    def test_perform_square_result_has_correct_fields(self):
        result = self.service.perform(Operation.SQUARE, 4, 0)
        assert result.operation == "square"
        assert result.operand_a == 4
        assert result.operand_b == 0
        assert result.execution_time_ms > 0


class TestServiceSqrt:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_sqrt_returns_result(self):
        result = self.service.perform(Operation.SQRT, 9, 0)
        assert result.result == 3.0

    def test_perform_sqrt_float_result(self):
        result = self.service.perform(Operation.SQRT, 2, 0)
        assert result.result == pytest.approx(1.414213, rel=1e-5)

    def test_perform_sqrt_saves_to_storage(self):
        self.service.perform(Operation.SQRT, 9, 0)
        self.storage.save.assert_called_once()

    def test_perform_sqrt_negative_raises(self):
        with pytest.raises(ValueError, match="Square root of negative numbers is not allowed"):
            self.service.perform(Operation.SQRT, -4, 0)

    def test_perform_sqrt_negative_does_not_save(self):
        with pytest.raises(ValueError):
            self.service.perform(Operation.SQRT, -4, 0)
        self.storage.save.assert_not_called()


class TestServicePower:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_power_returns_result(self):
        result = self.service.perform(Operation.POWER, 2, 3)
        assert result.result == 8

    def test_perform_power_with_zero_exponent(self):
        result = self.service.perform(Operation.POWER, 5, 0)
        assert result.result == 1

    def test_perform_power_with_negative_exponent(self):
        result = self.service.perform(Operation.POWER, 2, -2)
        assert result.result == pytest.approx(0.25)

    def test_perform_power_saves_to_storage(self):
        self.service.perform(Operation.POWER, 2, 3)
        self.storage.save.assert_called_once()

    def test_perform_power_zero_to_negative_raises(self):
        with pytest.raises(ValueError, match="Cannot raise zero to a negative power"):
            self.service.perform(Operation.POWER, 0, -1)

    def test_perform_power_zero_to_negative_does_not_save(self):
        with pytest.raises(ValueError):
            self.service.perform(Operation.POWER, 0, -1)
        self.storage.save.assert_not_called()


class TestServiceModulo:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_modulo_returns_result(self):
        result = self.service.perform(Operation.MODULO, 10, 3)
        assert result.result == 1

    def test_perform_modulo_evenly_divisible(self):
        result = self.service.perform(Operation.MODULO, 10, 2)
        assert result.result == 0

    def test_perform_modulo_saves_to_storage(self):
        self.service.perform(Operation.MODULO, 10, 3)
        self.storage.save.assert_called_once()

    def test_perform_modulo_by_zero_raises(self):
        with pytest.raises(ValueError, match="Modulo by zero is not allowed"):
            self.service.perform(Operation.MODULO, 10, 0)

    def test_perform_modulo_by_zero_does_not_save(self):
        with pytest.raises(ValueError):
            self.service.perform(Operation.MODULO, 10, 0)
        self.storage.save.assert_not_called()

    def test_perform_modulo_result_has_correct_fields(self):
        result = self.service.perform(Operation.MODULO, 7, 3)
        assert result.operation == "modulo"
        assert result.operand_a == 7
        assert result.operand_b == 3
        assert result.execution_time_ms > 0
