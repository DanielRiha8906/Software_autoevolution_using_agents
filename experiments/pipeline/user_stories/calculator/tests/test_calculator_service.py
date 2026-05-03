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

    # ====== Square Tests ======
    def test_perform_square_returns_result(self):
        result = self.service.perform(Operation.SQUARE, 5, 0)
        assert result.result == 25
        assert result.operation == "square"
        assert result.operand_a == 5
        assert result.operand_b == 0

    def test_perform_square_saves_to_storage(self):
        self.service.perform(Operation.SQUARE, 5, 0)
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        assert saved.result == 25

    @pytest.mark.parametrize("value,expected", [
        (0, 0),
        (2, 4),
        (10, 100),
        (-3, 9),
        (1.5, pytest.approx(2.25)),
    ])
    def test_perform_square_parametrized(self, value, expected):
        result = self.service.perform(Operation.SQUARE, value, 0)
        assert result.result == expected

    # ====== Square Root Tests ======
    def test_perform_sqrt_returns_result(self):
        result = self.service.perform(Operation.SQRT, 25, 0)
        assert result.result == 5
        assert result.operation == "sqrt"
        assert result.operand_a == 25
        assert result.operand_b == 0

    def test_perform_sqrt_saves_to_storage(self):
        self.service.perform(Operation.SQRT, 16, 0)
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        assert saved.result == 4

    def test_perform_sqrt_negative_raises(self):
        with pytest.raises(ValueError, match="Cannot take square root of negative number"):
            self.service.perform(Operation.SQRT, -1, 0)

    def test_perform_sqrt_negative_does_not_save(self):
        with pytest.raises(ValueError):
            self.service.perform(Operation.SQRT, -5, 0)
        self.storage.save.assert_not_called()

    @pytest.mark.parametrize("value,expected", [
        (0, 0),
        (1, 1),
        (4, 2),
        (9, 3),
        (1.5, pytest.approx(1.2247448713915890)),
    ])
    def test_perform_sqrt_parametrized(self, value, expected):
        result = self.service.perform(Operation.SQRT, value, 0)
        assert result.result == expected

    # ====== Power Tests ======
    def test_perform_power_returns_result(self):
        result = self.service.perform(Operation.POWER, 2, 5)
        assert result.result == 32
        assert result.operation == "power"
        assert result.operand_a == 2
        assert result.operand_b == 5

    def test_perform_power_saves_to_storage(self):
        self.service.perform(Operation.POWER, 3, 2)
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        assert saved.result == 9

    @pytest.mark.parametrize("base,exp,expected", [
        (2, 0, 1),
        (2, 1, 2),
        (2, 3, 8),
        (5, 2, 25),
        (2, -1, pytest.approx(0.5)),
        (9, 0.5, pytest.approx(3)),
    ])
    def test_perform_power_parametrized(self, base, exp, expected):
        result = self.service.perform(Operation.POWER, base, exp)
        assert result.result == expected

    # ====== Modulo Tests ======
    def test_perform_modulo_returns_result(self):
        result = self.service.perform(Operation.MODULO, 10, 3)
        assert result.result == 1
        assert result.operation == "modulo"
        assert result.operand_a == 10
        assert result.operand_b == 3

    def test_perform_modulo_saves_to_storage(self):
        self.service.perform(Operation.MODULO, 10, 3)
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        assert saved.result == 1

    def test_perform_modulo_by_zero_raises(self):
        with pytest.raises(ValueError, match="Modulo by zero is not allowed"):
            self.service.perform(Operation.MODULO, 10, 0)

    def test_perform_modulo_by_zero_does_not_save(self):
        with pytest.raises(ValueError):
            self.service.perform(Operation.MODULO, 10, 0)
        self.storage.save.assert_not_called()

    @pytest.mark.parametrize("a,b,expected", [
        (10, 3, 1),
        (10, 5, 0),
        (7, 2, 1),
        (-10, 3, 2),
        (10, -3, -2),
        (5.5, 2, pytest.approx(1.5)),
    ])
    def test_perform_modulo_parametrized(self, a, b, expected):
        result = self.service.perform(Operation.MODULO, a, b)
        assert result.result == expected
