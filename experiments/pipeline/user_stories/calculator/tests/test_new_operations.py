"""
Comprehensive tests for new operations: square, sqrt, power, modulo.
Covers Calculator methods, CalculatorService integration, CalculationResult formatting,
and CLI integration.
"""
import math
import pytest
from unittest.mock import MagicMock, patch

from src.models.operation import Operation
from src.models.calculation_result import CalculationResult
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService
from src.cli.calculator_cli import CalculatorCLI


# ============================================================================
# TestOperationEnum: Verify Operation enum has all 8 members
# ============================================================================

class TestOperationEnum:
    def test_operation_enum_has_eight_members(self):
        """Verify Operation enum now has exactly 8 members."""
        assert len(list(Operation)) == 8

    def test_operation_enum_contains_new_operations(self):
        """Verify new operations are in the enum."""
        assert Operation.SQUARE in Operation
        assert Operation.SQRT in Operation
        assert Operation.POWER in Operation
        assert Operation.MODULO in Operation

    def test_operation_from_string_square(self):
        """Test from_string() for square."""
        assert Operation.from_string("square") == Operation.SQUARE

    def test_operation_from_string_sqrt(self):
        """Test from_string() for sqrt."""
        assert Operation.from_string("sqrt") == Operation.SQRT

    def test_operation_from_string_power(self):
        """Test from_string() for power."""
        assert Operation.from_string("power") == Operation.POWER

    def test_operation_from_string_modulo(self):
        """Test from_string() for modulo."""
        assert Operation.from_string("modulo") == Operation.MODULO

    def test_operation_display_name_new_ops(self):
        """Test display_name() for new operations."""
        assert Operation.SQUARE.display_name() == "Square"
        assert Operation.SQRT.display_name() == "Sqrt"
        assert Operation.POWER.display_name() == "Power"
        assert Operation.MODULO.display_name() == "Modulo"


# ============================================================================
# TestSquare: Square operation (unary)
# ============================================================================

class TestSquare:
    def setup_method(self):
        self.calc = Calculator()

    def test_square_basic(self):
        """5² = 25"""
        assert self.calc.square(5, 0) == 25

    def test_square_zero(self):
        """0² = 0"""
        assert self.calc.square(0, 0) == 0

    def test_square_negative(self):
        """(-3)² = 9"""
        assert self.calc.square(-3, 0) == 9

    def test_square_one(self):
        """1² = 1"""
        assert self.calc.square(1, 0) == 1

    def test_square_two(self):
        """2² = 4"""
        assert self.calc.square(2, 0) == 4

    def test_square_large_number(self):
        """1000² = 1,000,000"""
        assert self.calc.square(1000, 0) == 1000000

    def test_square_float(self):
        """(1.5)² = 2.25"""
        assert self.calc.square(1.5, 0) == pytest.approx(2.25)

    def test_square_negative_float(self):
        """(-2.5)² = 6.25"""
        assert self.calc.square(-2.5, 0) == pytest.approx(6.25)

    def test_square_small_float(self):
        """(0.5)² = 0.25"""
        assert self.calc.square(0.5, 0) == pytest.approx(0.25)


# ============================================================================
# TestSqrt: Square root operation (unary)
# ============================================================================

class TestSqrt:
    def setup_method(self):
        self.calc = Calculator()

    def test_sqrt_perfect_square_16(self):
        """√16 = 4"""
        assert self.calc.sqrt(16, 0) == 4

    def test_sqrt_perfect_square_1(self):
        """√1 = 1"""
        assert self.calc.sqrt(1, 0) == 1

    def test_sqrt_perfect_square_0(self):
        """√0 = 0"""
        assert self.calc.sqrt(0, 0) == 0

    def test_sqrt_perfect_square_25(self):
        """√25 = 5"""
        assert self.calc.sqrt(25, 0) == 5

    def test_sqrt_perfect_square_100(self):
        """√100 = 10"""
        assert self.calc.sqrt(100, 0) == 10

    def test_sqrt_non_perfect_square(self):
        """√2 ≈ 1.414..."""
        assert self.calc.sqrt(2, 0) == pytest.approx(math.sqrt(2))

    def test_sqrt_non_perfect_square_3(self):
        """√3 ≈ 1.732..."""
        assert self.calc.sqrt(3, 0) == pytest.approx(math.sqrt(3))

    def test_sqrt_fractional(self):
        """√0.25 = 0.5"""
        assert self.calc.sqrt(0.25, 0) == pytest.approx(0.5)

    def test_sqrt_large_number(self):
        """√10000 = 100"""
        assert self.calc.sqrt(10000, 0) == 100

    def test_sqrt_negative_raises_valueerror(self):
        """√(-1) raises ValueError"""
        with pytest.raises(ValueError, match="Square root of negative"):
            self.calc.sqrt(-1, 0)

    def test_sqrt_negative_raises_valueerror_decimal(self):
        """√(-0.5) raises ValueError"""
        with pytest.raises(ValueError, match="Square root of negative"):
            self.calc.sqrt(-0.5, 0)


# ============================================================================
# TestPower: Power operation (binary: a^b)
# ============================================================================

class TestPower:
    def setup_method(self):
        self.calc = Calculator()

    def test_power_positive_exponent(self):
        """2³ = 8"""
        assert self.calc.power(2, 3) == 8

    def test_power_positive_exponent_larger(self):
        """3⁴ = 81"""
        assert self.calc.power(3, 4) == 81

    def test_power_zero_exponent(self):
        """5⁰ = 1"""
        assert self.calc.power(5, 0) == 1

    def test_power_zero_exponent_base_zero(self):
        """0⁰ = 1 (Python convention)"""
        assert self.calc.power(0, 0) == 1

    def test_power_negative_exponent(self):
        """2⁻² = 0.25"""
        assert self.calc.power(2, -2) == pytest.approx(0.25)

    def test_power_negative_exponent_larger(self):
        """10⁻¹ = 0.1"""
        assert self.calc.power(10, -1) == pytest.approx(0.1)

    def test_power_fractional_exponent(self):
        """4^0.5 = 2.0 (square root)"""
        assert self.calc.power(4, 0.5) == pytest.approx(2.0)

    def test_power_fractional_exponent_cube_root(self):
        """8^(1/3) ≈ 2.0 (cube root)"""
        assert self.calc.power(8, 1/3) == pytest.approx(2.0)

    def test_power_fractional_exponent_non_perfect(self):
        """2^0.5 ≈ 1.414... (square root of 2)"""
        assert self.calc.power(2, 0.5) == pytest.approx(math.sqrt(2))

    def test_power_base_one(self):
        """1^n = 1 for any n"""
        assert self.calc.power(1, 100) == 1
        assert self.calc.power(1, -5) == 1

    def test_power_base_negative(self):
        """(-2)³ = -8 (odd exponent)"""
        assert self.calc.power(-2, 3) == -8

    def test_power_base_negative_even_exponent(self):
        """(-2)⁴ = 16 (even exponent)"""
        assert self.calc.power(-2, 4) == 16

    def test_power_large_exponent(self):
        """2¹⁰ = 1024"""
        assert self.calc.power(2, 10) == 1024


# ============================================================================
# TestModulo: Modulo operation (binary: a % b)
# ============================================================================

class TestModulo:
    def setup_method(self):
        self.calc = Calculator()

    def test_modulo_basic(self):
        """7 % 3 = 1"""
        assert self.calc.modulo(7, 3) == 1

    def test_modulo_no_remainder(self):
        """10 % 5 = 0"""
        assert self.calc.modulo(10, 5) == 0

    def test_modulo_divisor_larger(self):
        """3 % 7 = 3"""
        assert self.calc.modulo(3, 7) == 3

    def test_modulo_one(self):
        """5 % 1 = 0"""
        assert self.calc.modulo(5, 1) == 0

    def test_modulo_negative_dividend(self):
        """(-7) % 3 = 2 (Python: -7 % 3 = 2)"""
        assert self.calc.modulo(-7, 3) == pytest.approx(2)

    def test_modulo_negative_divisor(self):
        """7 % (-3) = -2 (Python: 7 % -3 = -2)"""
        assert self.calc.modulo(7, -3) == pytest.approx(-2)

    def test_modulo_both_negative(self):
        """(-7) % (-3) = -1"""
        assert self.calc.modulo(-7, -3) == pytest.approx(-1)

    def test_modulo_zero_dividend(self):
        """0 % 7 = 0"""
        assert self.calc.modulo(0, 7) == 0

    def test_modulo_floats(self):
        """7.5 % 2.5 = 0.0"""
        assert self.calc.modulo(7.5, 2.5) == pytest.approx(0.0)

    def test_modulo_float_with_remainder(self):
        """7.5 % 2 = 1.5"""
        assert self.calc.modulo(7.5, 2) == pytest.approx(1.5)

    def test_modulo_by_zero_raises_valueerror(self):
        """7 % 0 raises ValueError"""
        with pytest.raises(ValueError, match="Modulo by zero"):
            self.calc.modulo(7, 0)

    def test_modulo_by_zero_with_float(self):
        """7.5 % 0.0 raises ValueError"""
        with pytest.raises(ValueError, match="Modulo by zero"):
            self.calc.modulo(7.5, 0.0)


# ============================================================================
# TestCalculatorCalculateDispatch: Test dispatch mechanism for new ops
# ============================================================================

class TestCalculatorCalculateDispatch:
    def setup_method(self):
        self.calc = Calculator()

    def test_calculate_dispatches_square(self):
        """calculate() dispatches SQUARE operation"""
        result = self.calc.calculate(Operation.SQUARE, 5, 0)
        assert result == 25

    def test_calculate_dispatches_sqrt(self):
        """calculate() dispatches SQRT operation"""
        result = self.calc.calculate(Operation.SQRT, 16, 0)
        assert result == 4

    def test_calculate_dispatches_power(self):
        """calculate() dispatches POWER operation"""
        result = self.calc.calculate(Operation.POWER, 2, 3)
        assert result == 8

    def test_calculate_dispatches_modulo(self):
        """calculate() dispatches MODULO operation"""
        result = self.calc.calculate(Operation.MODULO, 7, 3)
        assert result == 1

    def test_calculate_with_error_condition(self):
        """calculate() propagates errors from methods"""
        with pytest.raises(ValueError, match="Modulo by zero"):
            self.calc.calculate(Operation.MODULO, 7, 0)


# ============================================================================
# TestCalculatorServiceNewOperations: Service integration
# ============================================================================

class TestCalculatorServiceNewOperations:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_square_returns_result(self):
        """perform() returns CalculationResult for square"""
        result = self.service.perform(Operation.SQUARE, 5, 0)
        assert result.result == 25
        assert result.operation == "square"
        assert result.operand_a == 5
        assert result.operand_b == -1.0  # unary op

    def test_perform_sqrt_returns_result(self):
        """perform() returns CalculationResult for sqrt"""
        result = self.service.perform(Operation.SQRT, 16, 0)
        assert result.result == 4
        assert result.operation == "sqrt"
        assert result.operand_a == 16
        assert result.operand_b == -1.0  # unary op

    def test_perform_power_returns_result(self):
        """perform() returns CalculationResult for power"""
        result = self.service.perform(Operation.POWER, 2, 3)
        assert result.result == 8
        assert result.operation == "power"
        assert result.operand_a == 2
        assert result.operand_b == 3

    def test_perform_modulo_returns_result(self):
        """perform() returns CalculationResult for modulo"""
        result = self.service.perform(Operation.MODULO, 7, 3)
        assert result.result == 1
        assert result.operation == "modulo"
        assert result.operand_a == 7
        assert result.operand_b == 3

    def test_perform_square_saves_to_storage(self):
        """perform(SQUARE) saves to storage"""
        self.service.perform(Operation.SQUARE, 5, 0)
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        assert saved.result == 25
        assert saved.operation == "square"

    def test_perform_sqrt_saves_to_storage(self):
        """perform(SQRT) saves to storage"""
        self.service.perform(Operation.SQRT, 16, 0)
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        assert saved.result == 4

    def test_perform_power_saves_to_storage(self):
        """perform(POWER) saves to storage"""
        self.service.perform(Operation.POWER, 2, 3)
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        assert saved.result == 8

    def test_perform_modulo_saves_to_storage(self):
        """perform(MODULO) saves to storage"""
        self.service.perform(Operation.MODULO, 7, 3)
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        assert saved.result == 1

    def test_perform_sqrt_negative_raises(self):
        """perform(SQRT) with negative raises ValueError"""
        with pytest.raises(ValueError, match="Square root of negative"):
            self.service.perform(Operation.SQRT, -1, 0)

    def test_perform_sqrt_negative_does_not_save(self):
        """perform(SQRT) with error does not save"""
        with pytest.raises(ValueError):
            self.service.perform(Operation.SQRT, -1, 0)
        self.storage.save.assert_not_called()

    def test_perform_modulo_by_zero_raises(self):
        """perform(MODULO) by zero raises ValueError"""
        with pytest.raises(ValueError, match="Modulo by zero"):
            self.service.perform(Operation.MODULO, 7, 0)

    def test_perform_modulo_by_zero_does_not_save(self):
        """perform(MODULO) with error does not save"""
        with pytest.raises(ValueError):
            self.service.perform(Operation.MODULO, 7, 0)
        self.storage.save.assert_not_called()

    def test_perform_square_unary_marker(self):
        """perform(SQUARE) sets operand_b to -1.0"""
        result = self.service.perform(Operation.SQUARE, 3, 999)
        # Even if b is 999, for unary ops it's stored as -1.0
        assert result.operand_b == -1.0

    def test_perform_sqrt_unary_marker(self):
        """perform(SQRT) sets operand_b to -1.0"""
        result = self.service.perform(Operation.SQRT, 9, 888)
        # Even if b is 888, for unary ops it's stored as -1.0
        assert result.operand_b == -1.0


# ============================================================================
# TestCalculationResultFormatting: String representation with new ops
# ============================================================================

class TestCalculationResultFormatting:
    def test_square_formatting(self):
        """CalculationResult.__str__() formats square as ²a = r"""
        result = CalculationResult("square", 5, -1, 25, "2026-01-01T00:00:00")
        assert str(result) == "²5 = 25"

    def test_square_formatting_decimal(self):
        """Square with decimal keeps precision"""
        result = CalculationResult("square", 1.5, -1, 2.25, "2026-01-01T00:00:00")
        assert str(result) == "²1.5 = 2.25"

    def test_sqrt_formatting(self):
        """CalculationResult.__str__() formats sqrt as √a = r"""
        result = CalculationResult("sqrt", 16, -1, 4, "2026-01-01T00:00:00")
        assert str(result) == "√16 = 4"

    def test_sqrt_formatting_non_perfect_square(self):
        """Sqrt with non-integer result"""
        result = CalculationResult("sqrt", 2, -1, 1.4142135623730951, "2026-01-01T00:00:00")
        # Result is non-integer so it should be formatted as float
        assert "√2" in str(result)

    def test_power_formatting(self):
        """CalculationResult.__str__() formats power as a ^ b = r"""
        result = CalculationResult("power", 2, 3, 8, "2026-01-01T00:00:00")
        assert str(result) == "2 ^ 3 = 8"

    def test_power_formatting_float_exponent(self):
        """Power with fractional exponent"""
        result = CalculationResult("power", 4, 0.5, 2.0, "2026-01-01T00:00:00")
        assert str(result) == "4 ^ 0.5 = 2"

    def test_modulo_formatting(self):
        """CalculationResult.__str__() formats modulo as a % b = r"""
        result = CalculationResult("modulo", 7, 3, 1, "2026-01-01T00:00:00")
        assert str(result) == "7 % 3 = 1"

    def test_modulo_formatting_with_decimals(self):
        """Modulo with float operands"""
        result = CalculationResult("modulo", 7.5, 2.5, 0.0, "2026-01-01T00:00:00")
        assert str(result) == "7.5 % 2.5 = 0"

    def test_unary_ops_ignore_operand_b(self):
        """Unary ops should ignore operand_b in formatting"""
        result_sq = CalculationResult("square", 5, 999, 25, "2026-01-01T00:00:00")
        result_sqrt = CalculationResult("sqrt", 16, 888, 4, "2026-01-01T00:00:00")
        # Should still format correctly, ignoring the operand_b
        assert "999" not in str(result_sq)
        assert "888" not in str(result_sqrt)
        assert str(result_sq) == "²5 = 25"
        assert str(result_sqrt) == "√16 = 4"


# ============================================================================
# TestCLINewOperations: CLI integration for new operations
# ============================================================================

class TestCLIRunCommandNewOps:
    def setup_method(self):
        self.service = MagicMock()
        self.cli = CalculatorCLI(self.service)

    def test_run_command_square(self, capsys):
        """run_command('square', 5, 0) works"""
        self.service.perform.return_value = CalculationResult("square", 5, -1, 25, "2026-01-01T00:00:00")
        self.cli.run_command("square", 5, 0)
        assert "25" in capsys.readouterr().out

    def test_run_command_sqrt(self, capsys):
        """run_command('sqrt', 16, 0) works"""
        self.service.perform.return_value = CalculationResult("sqrt", 16, -1, 4, "2026-01-01T00:00:00")
        self.cli.run_command("sqrt", 16, 0)
        assert "4" in capsys.readouterr().out

    def test_run_command_power(self, capsys):
        """run_command('power', 2, 3) works"""
        self.service.perform.return_value = CalculationResult("power", 2, 3, 8, "2026-01-01T00:00:00")
        self.cli.run_command("power", 2, 3)
        assert "8" in capsys.readouterr().out

    def test_run_command_modulo(self, capsys):
        """run_command('modulo', 7, 3) works"""
        self.service.perform.return_value = CalculationResult("modulo", 7, 3, 1, "2026-01-01T00:00:00")
        self.cli.run_command("modulo", 7, 3)
        assert "1" in capsys.readouterr().out

    def test_run_command_sqrt_negative_error(self, capsys):
        """run_command('sqrt', -1, 0) exits with error"""
        self.service.perform.side_effect = ValueError("Square root of negative")
        with pytest.raises(SystemExit):
            self.cli.run_command("sqrt", -1, 0)
        assert "Square root of negative" in capsys.readouterr().err

    def test_run_command_modulo_by_zero_error(self, capsys):
        """run_command('modulo', 7, 0) exits with error"""
        self.service.perform.side_effect = ValueError("Modulo by zero")
        with pytest.raises(SystemExit):
            self.cli.run_command("modulo", 7, 0)
        assert "Modulo by zero" in capsys.readouterr().err


class TestCLIMenuNewOps:
    def setup_method(self):
        self.service = MagicMock()
        self.cli = CalculatorCLI(self.service)

    def test_menu_includes_square_option(self):
        """Menu has Square at option 5"""
        menu_ops = [op for op, _ in self.cli._MENU]
        assert Operation.SQUARE in menu_ops
        idx = menu_ops.index(Operation.SQUARE)
        assert idx == 4  # 0-indexed, so position 5

    def test_menu_includes_sqrt_option(self):
        """Menu has Square Root at option 6"""
        menu_ops = [op for op, _ in self.cli._MENU]
        assert Operation.SQRT in menu_ops
        idx = menu_ops.index(Operation.SQRT)
        assert idx == 5  # 0-indexed, so position 6

    def test_menu_includes_power_option(self):
        """Menu has Power at option 7"""
        menu_ops = [op for op, _ in self.cli._MENU]
        assert Operation.POWER in menu_ops
        idx = menu_ops.index(Operation.POWER)
        assert idx == 6  # 0-indexed, so position 7

    def test_menu_includes_modulo_option(self):
        """Menu has Modulo at option 8"""
        menu_ops = [op for op, _ in self.cli._MENU]
        assert Operation.MODULO in menu_ops
        idx = menu_ops.index(Operation.MODULO)
        assert idx == 7  # 0-indexed, so position 8

    def test_menu_has_eight_operations(self):
        """Menu has exactly 8 operations"""
        assert len(self.cli._MENU) == 8

    def test_menu_order_correct(self):
        """Menu operations in correct order"""
        menu_ops = [op for op, _ in self.cli._MENU]
        expected = [
            Operation.ADD,
            Operation.SUBTRACT,
            Operation.MULTIPLY,
            Operation.DIVIDE,
            Operation.SQUARE,
            Operation.SQRT,
            Operation.POWER,
            Operation.MODULO,
        ]
        assert menu_ops == expected


class TestCLIInteractiveNewOps:
    def setup_method(self):
        self.service = MagicMock()
        self.cli = CalculatorCLI(self.service)

    def test_interactive_square_option(self, capsys):
        """Interactive menu option 5 (Square)"""
        self.service.perform.return_value = CalculationResult("square", 5, -1, 25, "2026-01-01T00:00:00")
        with patch("builtins.input", side_effect=["5", "5", "10"]):
            self.cli.run_interactive()
        assert "25" in capsys.readouterr().out

    def test_interactive_sqrt_option(self, capsys):
        """Interactive menu option 6 (Square Root)"""
        self.service.perform.return_value = CalculationResult("sqrt", 16, -1, 4, "2026-01-01T00:00:00")
        with patch("builtins.input", side_effect=["6", "16", "10"]):
            self.cli.run_interactive()
        assert "4" in capsys.readouterr().out

    def test_interactive_power_option(self, capsys):
        """Interactive menu option 7 (Power)"""
        self.service.perform.return_value = CalculationResult("power", 2, 3, 8, "2026-01-01T00:00:00")
        with patch("builtins.input", side_effect=["7", "2", "3", "10"]):
            self.cli.run_interactive()
        assert "8" in capsys.readouterr().out

    def test_interactive_modulo_option(self, capsys):
        """Interactive menu option 8 (Modulo)"""
        self.service.perform.return_value = CalculationResult("modulo", 7, 3, 1, "2026-01-01T00:00:00")
        with patch("builtins.input", side_effect=["8", "7", "3", "10"]):
            self.cli.run_interactive()
        assert "1" in capsys.readouterr().out

    def test_interactive_sqrt_negative_error(self, capsys):
        """Interactive sqrt with negative number shows error"""
        self.service.perform.side_effect = ValueError("Square root of negative")
        with patch("builtins.input", side_effect=["6", "-1", "10"]):
            self.cli.run_interactive()
        assert "Square root of negative" in capsys.readouterr().out

    def test_interactive_modulo_by_zero_error(self, capsys):
        """Interactive modulo with zero divisor shows error"""
        self.service.perform.side_effect = ValueError("Modulo by zero")
        with patch("builtins.input", side_effect=["8", "7", "0", "10"]):
            self.cli.run_interactive()
        assert "Modulo by zero" in capsys.readouterr().out
