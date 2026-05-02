import math
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

    def test_square_returns_correct_result(self):
        assert self.calc.square(4) == 16

    def test_square_of_zero(self):
        assert self.calc.square(0) == 0

    def test_sqrt_returns_correct_result(self):
        assert self.calc.sqrt(9) == pytest.approx(3.0)

    def test_sqrt_of_negative_raises(self):
        with pytest.raises(Exception):
            self.calc.sqrt(-1)

    def test_power_integer_exponent(self):
        assert self.calc.power(2, 10) == 1024

    def test_power_fractional_exponent(self):
        assert self.calc.power(8, 1 / 3) == pytest.approx(2.0, rel=1e-5)

    def test_power_negative_exponent(self):
        assert self.calc.power(2, -1) == pytest.approx(0.5)

    def test_modulo_returns_correct_result(self):
        assert self.calc.modulo(10, 3) == 1

    def test_modulo_by_zero_raises(self):
        with pytest.raises(Exception):
            self.calc.modulo(10, 0)

    def test_existing_operations_unchanged(self):
        calc = Calculator()
        assert calc.add(2, 3) == 5
        assert calc.subtract(5, 3) == 2
        assert calc.multiply(3, 4) == 12
        assert calc.divide(10, 2) == 5
