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
                          Operation.SQUARE, Operation.SQRT, Operation.POWER, Operation.MODULO,
                          Operation.SIN, Operation.COS, Operation.TAN, Operation.LOG, Operation.LN, Operation.EXP]:
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


class TestServiceSin:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_sin_zero(self):
        result = self.service.perform(Operation.SIN, 0, 0)
        assert result.result == pytest.approx(0.0)

    def test_perform_sin_pi_over_2(self):
        import math
        result = self.service.perform(Operation.SIN, math.pi / 2, 0)
        assert result.result == pytest.approx(1.0)

    def test_perform_sin_saves_to_storage(self):
        self.service.perform(Operation.SIN, 0, 0)
        self.storage.save.assert_called_once()

    def test_perform_sin_result_has_correct_fields(self):
        result = self.service.perform(Operation.SIN, 0.5, 0)
        assert result.operation == "sin"
        assert result.operand_a == 0.5
        assert result.operand_b == 0
        assert result.execution_time_ms > 0


class TestServiceCos:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_cos_zero(self):
        result = self.service.perform(Operation.COS, 0, 0)
        assert result.result == pytest.approx(1.0)

    def test_perform_cos_pi(self):
        import math
        result = self.service.perform(Operation.COS, math.pi, 0)
        assert result.result == pytest.approx(-1.0)

    def test_perform_cos_saves_to_storage(self):
        self.service.perform(Operation.COS, 0, 0)
        self.storage.save.assert_called_once()

    def test_perform_cos_result_has_correct_fields(self):
        result = self.service.perform(Operation.COS, 0.5, 0)
        assert result.operation == "cos"
        assert result.operand_a == 0.5
        assert result.operand_b == 0
        assert result.execution_time_ms > 0


class TestServiceTan:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_tan_zero(self):
        result = self.service.perform(Operation.TAN, 0, 0)
        assert result.result == pytest.approx(0.0)

    def test_perform_tan_pi_over_4(self):
        import math
        result = self.service.perform(Operation.TAN, math.pi / 4, 0)
        assert result.result == pytest.approx(1.0)

    def test_perform_tan_saves_to_storage(self):
        self.service.perform(Operation.TAN, 0, 0)
        self.storage.save.assert_called_once()

    def test_perform_tan_result_has_correct_fields(self):
        result = self.service.perform(Operation.TAN, 0.3, 0)
        assert result.operation == "tan"
        assert result.operand_a == 0.3
        assert result.operand_b == 0
        assert result.execution_time_ms > 0


class TestServiceLog:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_log_100(self):
        result = self.service.perform(Operation.LOG, 100, 0)
        assert result.result == pytest.approx(2.0)

    def test_perform_log_10(self):
        result = self.service.perform(Operation.LOG, 10, 0)
        assert result.result == pytest.approx(1.0)

    def test_perform_log_saves_to_storage(self):
        self.service.perform(Operation.LOG, 100, 0)
        self.storage.save.assert_called_once()

    def test_perform_log_zero_raises(self):
        with pytest.raises(ValueError, match="Logarithm of x <= 0 is not allowed"):
            self.service.perform(Operation.LOG, 0, 0)

    def test_perform_log_zero_does_not_save(self):
        with pytest.raises(ValueError):
            self.service.perform(Operation.LOG, 0, 0)
        self.storage.save.assert_not_called()

    def test_perform_log_negative_raises(self):
        with pytest.raises(ValueError, match="Logarithm of x <= 0 is not allowed"):
            self.service.perform(Operation.LOG, -5, 0)

    def test_perform_log_negative_does_not_save(self):
        with pytest.raises(ValueError):
            self.service.perform(Operation.LOG, -5, 0)
        self.storage.save.assert_not_called()

    def test_perform_log_result_has_correct_fields(self):
        result = self.service.perform(Operation.LOG, 100, 0)
        assert result.operation == "log"
        assert result.operand_a == 100
        assert result.operand_b == 0
        assert result.execution_time_ms > 0


class TestServiceLn:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_ln_e(self):
        import math
        result = self.service.perform(Operation.LN, math.e, 0)
        assert result.result == pytest.approx(1.0)

    def test_perform_ln_1(self):
        result = self.service.perform(Operation.LN, 1, 0)
        assert result.result == pytest.approx(0.0)

    def test_perform_ln_saves_to_storage(self):
        import math
        self.service.perform(Operation.LN, math.e, 0)
        self.storage.save.assert_called_once()

    def test_perform_ln_zero_raises(self):
        with pytest.raises(ValueError, match="Logarithm of x <= 0 is not allowed"):
            self.service.perform(Operation.LN, 0, 0)

    def test_perform_ln_zero_does_not_save(self):
        with pytest.raises(ValueError):
            self.service.perform(Operation.LN, 0, 0)
        self.storage.save.assert_not_called()

    def test_perform_ln_negative_raises(self):
        with pytest.raises(ValueError, match="Logarithm of x <= 0 is not allowed"):
            self.service.perform(Operation.LN, -5, 0)

    def test_perform_ln_negative_does_not_save(self):
        with pytest.raises(ValueError):
            self.service.perform(Operation.LN, -5, 0)
        self.storage.save.assert_not_called()

    def test_perform_ln_result_has_correct_fields(self):
        import math
        result = self.service.perform(Operation.LN, math.e, 0)
        assert result.operation == "ln"
        assert result.operand_a == math.e
        assert result.operand_b == 0
        assert result.execution_time_ms > 0


class TestServiceExp:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_exp_zero(self):
        result = self.service.perform(Operation.EXP, 0, 0)
        assert result.result == pytest.approx(1.0)

    def test_perform_exp_one(self):
        import math
        result = self.service.perform(Operation.EXP, 1, 0)
        assert result.result == pytest.approx(math.e)

    def test_perform_exp_two(self):
        import math
        result = self.service.perform(Operation.EXP, 2, 0)
        assert result.result == pytest.approx(math.e ** 2)

    def test_perform_exp_saves_to_storage(self):
        self.service.perform(Operation.EXP, 0, 0)
        self.storage.save.assert_called_once()

    def test_perform_exp_negative(self):
        import math
        result = self.service.perform(Operation.EXP, -1, 0)
        assert result.result == pytest.approx(1.0 / math.e)

    def test_perform_exp_result_has_correct_fields(self):
        result = self.service.perform(Operation.EXP, 0, 0)
        assert result.operation == "exp"
        assert result.operand_a == 0
        assert result.operand_b == 0
        assert result.execution_time_ms > 0
