import pytest
from src.models.operation import Operation
from src.services.calculator import Calculator


class TestCalculator:
    def setup_method(self):
        self.calc = Calculator()

    def test_add_integers(self):
        assert self.calc.add(3, 5) == 8

    def test_add_negative(self):
        assert self.calc.add(-3, -5) == -8

    def test_add_floats(self):
        assert self.calc.add(1.5, 2.5) == pytest.approx(4.0)

    def test_subtract(self):
        assert self.calc.subtract(10, 4) == 6

    def test_subtract_to_negative(self):
        assert self.calc.subtract(3, 10) == -7

    def test_multiply(self):
        assert self.calc.multiply(3, 5) == 15

    def test_multiply_by_zero(self):
        assert self.calc.multiply(99, 0) == 0

    def test_multiply_floats(self):
        assert self.calc.multiply(0.1, 0.2) == pytest.approx(0.02)

    def test_divide(self):
        assert self.calc.divide(10, 2) == 5.0

    def test_divide_resulting_float(self):
        assert self.calc.divide(7, 2) == pytest.approx(3.5)

    def test_divide_by_zero_raises(self):
        with pytest.raises(ValueError, match="Division by zero"):
            self.calc.divide(5, 0)

    def test_calculate_dispatches_all_operations(self):
        assert self.calc.calculate(Operation.ADD,      3, 5) == 8
        assert self.calc.calculate(Operation.SUBTRACT, 10, 4) == 6
        assert self.calc.calculate(Operation.MULTIPLY, 3, 5) == 15
        assert self.calc.calculate(Operation.DIVIDE,   10, 2) == 5.0

    # Square tests - provided specification
    def test_square_returns_correct_result(self):
        assert self.calc.square(4) == 16

    def test_square_of_zero(self):
        assert self.calc.square(0) == 0

    # Square tests - additional edge cases
    def test_square_with_negative_input(self):
        assert self.calc.square(-3) == 9

    def test_square_with_float_input(self):
        assert self.calc.square(2.5) == pytest.approx(6.25)

    def test_square_with_negative_float(self):
        assert self.calc.square(-1.5) == pytest.approx(2.25)

    def test_square_with_one(self):
        assert self.calc.square(1) == 1

    # Sqrt tests - provided specification
    def test_sqrt_returns_correct_result(self):
        assert self.calc.sqrt(9) == pytest.approx(3.0)

    def test_sqrt_of_negative_raises(self):
        with pytest.raises(Exception):
            self.calc.sqrt(-1)

    # Sqrt tests - additional edge cases
    def test_sqrt_of_zero(self):
        assert self.calc.sqrt(0) == 0.0

    def test_sqrt_of_one(self):
        assert self.calc.sqrt(1) == pytest.approx(1.0)

    def test_sqrt_of_fractional_input(self):
        assert self.calc.sqrt(0.25) == pytest.approx(0.5)

    def test_sqrt_of_large_number(self):
        assert self.calc.sqrt(10000) == pytest.approx(100.0)

    # Power tests - provided specification
    def test_power_integer_exponent(self):
        assert self.calc.power(2, 10) == 1024

    def test_power_fractional_exponent(self):
        assert self.calc.power(8, 1 / 3) == pytest.approx(2.0, rel=1e-5)

    def test_power_negative_exponent(self):
        assert self.calc.power(2, -1) == pytest.approx(0.5)

    # Power tests - additional edge cases
    def test_power_with_zero_exponent(self):
        assert self.calc.power(5, 0) == pytest.approx(1.0)

    def test_power_with_zero_base(self):
        assert self.calc.power(0, 5) == pytest.approx(0.0)

    def test_power_with_one_base(self):
        assert self.calc.power(1, 100) == pytest.approx(1.0)

    def test_power_with_negative_base_even_exponent(self):
        assert self.calc.power(-2, 2) == pytest.approx(4.0)

    def test_power_with_negative_base_odd_exponent(self):
        assert self.calc.power(-2, 3) == pytest.approx(-8.0)

    def test_power_with_floats(self):
        assert self.calc.power(1.5, 2) == pytest.approx(2.25)

    # Modulo tests - provided specification
    def test_modulo_returns_correct_result(self):
        assert self.calc.modulo(10, 3) == 1

    def test_modulo_by_zero_raises(self):
        with pytest.raises(Exception):
            self.calc.modulo(10, 0)

    # Modulo tests - additional edge cases
    def test_modulo_with_zero_dividend(self):
        assert self.calc.modulo(0, 5) == pytest.approx(0.0)

    def test_modulo_with_equal_operands(self):
        assert self.calc.modulo(7, 7) == pytest.approx(0.0)

    def test_modulo_with_dividend_less_than_divisor(self):
        assert self.calc.modulo(3, 10) == pytest.approx(3.0)

    def test_modulo_with_floats(self):
        assert self.calc.modulo(10.5, 3) == pytest.approx(1.5)

    def test_modulo_with_negative_dividend(self):
        assert self.calc.modulo(-10, 3) == pytest.approx(2.0)

    def test_modulo_with_negative_divisor(self):
        assert self.calc.modulo(10, -3) == pytest.approx(-2.0)

    def test_modulo_with_both_negative(self):
        assert self.calc.modulo(-10, -3) == pytest.approx(-1.0)

    # Test that existing operations are unchanged
    def test_existing_operations_unchanged(self):
        calc = Calculator()
        assert calc.add(2, 3) == 5
        assert calc.subtract(5, 3) == 2
        assert calc.multiply(3, 4) == 12
        assert calc.divide(10, 2) == 5

    # Integration tests - verify dispatch works for new operations
    def test_calculate_dispatches_square(self):
        assert self.calc.calculate(Operation.SQUARE, 4, None) == 16

    def test_calculate_dispatches_sqrt(self):
        assert self.calc.calculate(Operation.SQRT, 9, None) == pytest.approx(3.0)

    def test_calculate_dispatches_power(self):
        assert self.calc.calculate(Operation.POWER, 2, 10) == 1024

    def test_calculate_dispatches_modulo(self):
        assert self.calc.calculate(Operation.MODULO, 10, 3) == 1
