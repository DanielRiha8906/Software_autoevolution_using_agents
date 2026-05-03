"""Tests for scientific mode operations."""

import pytest
import math
from unittest.mock import MagicMock
from src.models.operation import Operation
from src.models.calculation_result import CalculationResult
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService


class TestOperationArity:
    """Test the arity methods on Operation enum."""

    def test_unary_operations_have_arity_one(self):
        """Unary operations should have arity 1."""
        unary_ops = [Operation.SIN, Operation.COS, Operation.TAN, Operation.LOG, Operation.LN, Operation.EXP, Operation.SQUARE, Operation.SQRT]
        for op in unary_ops:
            assert op.arity() == 1, f"{op.value} should have arity 1"
            assert op.is_unary(), f"{op.value} should be unary"

    def test_binary_operations_have_arity_two(self):
        """Binary operations should have arity 2."""
        binary_ops = [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE, Operation.POWER, Operation.MODULO]
        for op in binary_ops:
            assert op.arity() == 2, f"{op.value} should have arity 2"
            assert not op.is_unary(), f"{op.value} should not be unary"


class TestCalculatorScientificOperations:
    """Test scientific operations in Calculator."""

    def setup_method(self):
        self.calc = Calculator()

    def test_sin_operation(self):
        """Test sine operation."""
        result = self.calc.sin(0, 0)
        assert result == pytest.approx(0.0)
        result = self.calc.sin(math.pi / 2, 0)
        assert result == pytest.approx(1.0)

    def test_cos_operation(self):
        """Test cosine operation."""
        result = self.calc.cos(0, 0)
        assert result == pytest.approx(1.0)
        result = self.calc.cos(math.pi, 0)
        assert result == pytest.approx(-1.0)

    def test_tan_operation(self):
        """Test tangent operation."""
        result = self.calc.tan(0, 0)
        assert result == pytest.approx(0.0)
        result = self.calc.tan(math.pi / 4, 0)
        assert result == pytest.approx(1.0)

    def test_log_base10_operation(self):
        """Test base-10 logarithm."""
        result = self.calc.log(1, 0)
        assert result == pytest.approx(0.0)
        result = self.calc.log(10, 0)
        assert result == pytest.approx(1.0)
        result = self.calc.log(100, 0)
        assert result == pytest.approx(2.0)

    def test_log_negative_raises(self):
        """Log of negative number should raise."""
        with pytest.raises(ValueError, match="non-positive"):
            self.calc.log(-5, 0)

    def test_log_zero_raises(self):
        """Log of zero should raise."""
        with pytest.raises(ValueError, match="non-positive"):
            self.calc.log(0, 0)

    def test_ln_natural_log_operation(self):
        """Test natural logarithm."""
        result = self.calc.ln(1, 0)
        assert result == pytest.approx(0.0)
        result = self.calc.ln(math.e, 0)
        assert result == pytest.approx(1.0)

    def test_ln_negative_raises(self):
        """Natural log of negative number should raise."""
        with pytest.raises(ValueError, match="non-positive"):
            self.calc.ln(-5, 0)

    def test_ln_zero_raises(self):
        """Natural log of zero should raise."""
        with pytest.raises(ValueError, match="non-positive"):
            self.calc.ln(0, 0)

    def test_exp_operation(self):
        """Test exponential operation."""
        result = self.calc.exp(0, 0)
        assert result == pytest.approx(1.0)
        result = self.calc.exp(1, 0)
        assert result == pytest.approx(math.e)
        result = self.calc.exp(2, 0)
        assert result == pytest.approx(math.e ** 2)

    def test_calculate_dispatches_sin(self):
        """Calculate should dispatch sin correctly."""
        result = self.calc.calculate(Operation.SIN, 0, 0)
        assert result == pytest.approx(0.0)

    def test_calculate_dispatches_cos(self):
        """Calculate should dispatch cos correctly."""
        result = self.calc.calculate(Operation.COS, 0, 0)
        assert result == pytest.approx(1.0)

    def test_calculate_dispatches_tan(self):
        """Calculate should dispatch tan correctly."""
        result = self.calc.calculate(Operation.TAN, 0, 0)
        assert result == pytest.approx(0.0)

    def test_calculate_dispatches_log(self):
        """Calculate should dispatch log correctly."""
        result = self.calc.calculate(Operation.LOG, 10, 0)
        assert result == pytest.approx(1.0)

    def test_calculate_dispatches_ln(self):
        """Calculate should dispatch ln correctly."""
        result = self.calc.calculate(Operation.LN, math.e, 0)
        assert result == pytest.approx(1.0)

    def test_calculate_dispatches_exp(self):
        """Calculate should dispatch exp correctly."""
        result = self.calc.calculate(Operation.EXP, 0, 0)
        assert result == pytest.approx(1.0)

    def test_calculator_mode_attribute(self):
        """Calculator should have a mode attribute."""
        calc = Calculator(mode="scientific")
        assert calc.mode == "scientific"
        calc_std = Calculator(mode="standard")
        assert calc_std.mode == "standard"
        calc_default = Calculator()
        assert calc_default.mode == "standard"


class TestCalculationResultWithUnaryOps:
    """Test CalculationResult rendering for unary operations."""

    def test_unary_op_renders_as_op_a_equals_r(self):
        """Unary operations should render as 'op(a) = r'."""
        result = CalculationResult("sin", 0.0, None, 0.0)
        assert "sin(0" in str(result)
        assert "= 0" in str(result)

    def test_unary_op_with_operand_b_none(self):
        """operand_b can be None for unary operations."""
        result = CalculationResult("cos", math.pi, None, -1.0)
        assert "cos(" in str(result)
        assert str(result).endswith("= -1")

    def test_binary_op_still_works(self):
        """Binary operations should still render as 'a op b = r'."""
        result = CalculationResult("add", 3.0, 5.0, 8.0)
        assert "3" in str(result)
        assert "+" in str(result)
        assert "5" in str(result)
        assert "8" in str(result)

    def test_to_dict_with_unary_op(self):
        """to_dict should work with unary operations."""
        result = CalculationResult("sin", 0.0, None, 0.0)
        d = result.to_dict()
        assert d["operation"] == "sin"
        assert d["operand_a"] == 0.0
        assert d["operand_b"] is None
        assert d["result"] == 0.0

    def test_from_dict_with_unary_op(self):
        """from_dict should work with unary operations."""
        data = {
            "operation": "ln",
            "operand_a": 2.718281828,
            "operand_b": None,
            "result": 1.0,
            "timestamp": "2026-01-01T00:00:00",
            "execution_time_ms": 0.5,
        }
        result = CalculationResult.from_dict(data)
        assert result.operation == "ln"
        assert result.operand_a == 2.718281828
        assert result.operand_b is None
        assert result.result == 1.0


class TestCalculatorServiceWithUnaryOps:
    """Test CalculatorService with unary operations."""

    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_unary_op_with_none_operand_b(self):
        """perform should accept None for operand_b on unary ops."""
        result = self.service.perform(Operation.SIN, 0, None)
        assert result.operation == "sin"
        assert result.operand_a == 0
        assert result.operand_b is None
        assert result.result == pytest.approx(0.0)

    def test_perform_unary_op_saves_with_none(self):
        """perform should save with None operand_b for unary ops."""
        self.service.perform(Operation.LN, math.e, None)
        self.storage.save.assert_called_once()
        saved: CalculationResult = self.storage.save.call_args[0][0]
        assert saved.operand_b is None
        assert saved.operation == "ln"

    def test_perform_log_invalid_value_raises(self):
        """perform should raise for invalid log values."""
        with pytest.raises(ValueError, match="non-positive"):
            self.service.perform(Operation.LOG, -5, None)

    def test_perform_with_memory_unary_op(self):
        """perform_with_memory should work with unary operations."""
        result = self.service.perform_with_memory(Operation.EXP, 1, None)
        assert result.operation == "exp"
        assert len(result.operands) == 1
        assert result.operands[0] == 1
        assert result.result == pytest.approx(math.e)

    def test_perform_with_memory_unary_op_error(self):
        """perform_with_memory should capture errors for unary ops."""
        with pytest.raises(ValueError):
            self.service.perform_with_memory(Operation.LN, 0, None)
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        assert saved.operation == "ln"
        assert len(saved.operands) == 1


class TestOperationFromString:
    """Test Operation.from_string with scientific operations."""

    def test_from_string_sin(self):
        """from_string should recognize 'sin'."""
        assert Operation.from_string("sin") == Operation.SIN

    def test_from_string_cos(self):
        """from_string should recognize 'cos'."""
        assert Operation.from_string("cos") == Operation.COS

    def test_from_string_tan(self):
        """from_string should recognize 'tan'."""
        assert Operation.from_string("tan") == Operation.TAN

    def test_from_string_log(self):
        """from_string should recognize 'log'."""
        assert Operation.from_string("log") == Operation.LOG

    def test_from_string_ln(self):
        """from_string should recognize 'ln'."""
        assert Operation.from_string("ln") == Operation.LN

    def test_from_string_exp(self):
        """from_string should recognize 'exp'."""
        assert Operation.from_string("exp") == Operation.EXP

    def test_from_string_case_insensitive(self):
        """from_string should be case-insensitive."""
        assert Operation.from_string("SIN") == Operation.SIN
        assert Operation.from_string("Sin") == Operation.SIN
        assert Operation.from_string("LN") == Operation.LN
