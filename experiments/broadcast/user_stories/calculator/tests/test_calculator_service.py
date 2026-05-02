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

    def test_perform_square(self):
        assert self.service.perform(Operation.SQUARE, 5, 0).result == 25

    def test_perform_sqrt(self):
        assert self.service.perform(Operation.SQRT, 25, 0).result == 5.0

    def test_perform_sqrt_negative_raises(self):
        with pytest.raises(ValueError, match="Square root of a negative number"):
            self.service.perform(Operation.SQRT, -1, 0)

    def test_perform_sqrt_negative_does_not_save(self):
        with pytest.raises(ValueError):
            self.service.perform(Operation.SQRT, -1, 0)
        self.storage.save.assert_not_called()

    def test_perform_power(self):
        assert self.service.perform(Operation.POWER, 2, 3).result == 8.0

    def test_perform_modulo(self):
        assert self.service.perform(Operation.MODULO, 10, 3).result == 1

    def test_perform_modulo_by_zero_raises(self):
        with pytest.raises(ValueError, match="Modulo by zero"):
            self.service.perform(Operation.MODULO, 10, 0)

    def test_perform_modulo_by_zero_does_not_save(self):
        with pytest.raises(ValueError):
            self.service.perform(Operation.MODULO, 10, 0)
        self.storage.save.assert_not_called()
