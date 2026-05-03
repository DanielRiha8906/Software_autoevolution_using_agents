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

    # =====================================================================
    # Tests for SQUARE operation
    # =====================================================================

    def test_square_positive_integer(self):
        assert self.calc.square(5, 0) == 25

    def test_square_zero(self):
        assert self.calc.square(0, 0) == 0

    def test_square_negative_integer(self):
        assert self.calc.square(-4, 0) == 16

    def test_square_positive_float(self):
        assert self.calc.square(2.5, 0) == pytest.approx(6.25)

    def test_square_negative_float(self):
        assert self.calc.square(-3.5, 0) == pytest.approx(12.25)

    def test_square_ignores_second_operand(self):
        """square() ignores the b parameter"""
        assert self.calc.square(5, 100) == 25
        assert self.calc.square(5, 0) == 25
        assert self.calc.square(5, -50) == 25

    def test_square_via_calculate(self):
        assert self.calc.calculate(Operation.SQUARE, 3, 0) == 9
        assert self.calc.calculate(Operation.SQUARE, 10, 999) == 100

    # =====================================================================
    # Tests for SQRT operation
    # =====================================================================

    def test_sqrt_perfect_square(self):
        assert self.calc.sqrt(16, 0) == 4.0

    def test_sqrt_zero(self):
        assert self.calc.sqrt(0, 0) == 0.0

    def test_sqrt_one(self):
        assert self.calc.sqrt(1, 0) == 1.0

    def test_sqrt_non_perfect_square(self):
        assert self.calc.sqrt(2, 0) == pytest.approx(1.414213562)

    def test_sqrt_float_input(self):
        assert self.calc.sqrt(6.25, 0) == pytest.approx(2.5)

    def test_sqrt_negative_raises_value_error(self):
        with pytest.raises(ValueError, match="Square root of negative"):
            self.calc.sqrt(-4, 0)

    def test_sqrt_very_small_negative_raises(self):
        with pytest.raises(ValueError, match="Square root of negative"):
            self.calc.sqrt(-0.0001, 0)

    def test_sqrt_ignores_second_operand(self):
        """sqrt() ignores the b parameter"""
        assert self.calc.sqrt(9, 100) == 3.0
        assert self.calc.sqrt(9, 0) == 3.0
        assert self.calc.sqrt(9, -50) == 3.0

    def test_sqrt_via_calculate(self):
        assert self.calc.calculate(Operation.SQRT, 25, 0) == 5.0
        assert self.calc.calculate(Operation.SQRT, 100, 999) == 10.0

    # =====================================================================
    # Tests for POWER operation
    # =====================================================================

    def test_power_positive_base_positive_exponent(self):
        assert self.calc.power(2, 3) == 8

    def test_power_positive_base_zero_exponent(self):
        assert self.calc.power(5, 0) == 1.0

    def test_power_positive_base_one(self):
        assert self.calc.power(5, 1) == 5.0

    def test_power_one_base_any_exponent(self):
        assert self.calc.power(1, 10) == 1.0
        assert self.calc.power(1, -5) == pytest.approx(1.0)

    def test_power_zero_base_positive_exponent(self):
        assert self.calc.power(0, 5) == 0

    def test_power_zero_base_zero_exponent(self):
        # This is mathematically undefined, but Python returns 1
        assert self.calc.power(0, 0) == 1

    def test_power_negative_base_even_exponent(self):
        assert self.calc.power(-2, 2) == 4

    def test_power_negative_base_odd_exponent(self):
        assert self.calc.power(-2, 3) == -8

    def test_power_fractional_exponent(self):
        assert self.calc.power(4, 0.5) == pytest.approx(2.0)

    def test_power_negative_exponent(self):
        assert self.calc.power(2, -1) == pytest.approx(0.5)

    def test_power_negative_exponent_fraction(self):
        assert self.calc.power(4, -0.5) == pytest.approx(0.5)

    def test_power_float_base_float_exponent(self):
        assert self.calc.power(2.5, 2) == pytest.approx(6.25)

    def test_power_via_calculate(self):
        assert self.calc.calculate(Operation.POWER, 2, 8) == 256
        assert self.calc.calculate(Operation.POWER, 3, -2) == pytest.approx(0.1111111)

    # =====================================================================
    # Tests for MODULO operation
    # =====================================================================

    def test_modulo_basic(self):
        assert self.calc.modulo(10, 3) == 1

    def test_modulo_evenly_divisible(self):
        assert self.calc.modulo(10, 2) == 0

    def test_modulo_remainder_equals_divisor_minus_one(self):
        assert self.calc.modulo(10, 3) == 1

    def test_modulo_dividend_less_than_divisor(self):
        assert self.calc.modulo(3, 10) == 3

    def test_modulo_negative_dividend(self):
        assert self.calc.modulo(-10, 3) == 2

    def test_modulo_negative_divisor(self):
        assert self.calc.modulo(10, -3) == -2

    def test_modulo_both_negative(self):
        assert self.calc.modulo(-10, -3) == -1

    def test_modulo_zero_dividend(self):
        assert self.calc.modulo(0, 5) == 0

    def test_modulo_divisor_one(self):
        assert self.calc.modulo(10, 1) == 0

    def test_modulo_divisor_negative_one(self):
        assert self.calc.modulo(10, -1) == 0

    def test_modulo_float_operands(self):
        assert self.calc.modulo(10.5, 3) == pytest.approx(1.5)

    def test_modulo_by_zero_raises_value_error(self):
        with pytest.raises(ValueError, match="Modulo by zero"):
            self.calc.modulo(10, 0)

    def test_modulo_float_by_zero_raises(self):
        with pytest.raises(ValueError, match="Modulo by zero"):
            self.calc.modulo(5.5, 0)

    def test_modulo_via_calculate(self):
        assert self.calc.calculate(Operation.MODULO, 17, 5) == 2
        assert self.calc.calculate(Operation.MODULO, 100, 7) == 2
