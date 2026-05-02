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

    def test_square(self):
        assert self.calc.square(5, 0) == 25

    def test_square_zero(self):
        assert self.calc.square(0, 0) == 0

    def test_square_negative(self):
        assert self.calc.square(-4, 0) == 16

    def test_square_float(self):
        assert self.calc.square(2.5, 0) == pytest.approx(6.25)

    def test_sqrt(self):
        assert self.calc.sqrt(9, 0) == 3.0

    def test_sqrt_perfect_square(self):
        assert self.calc.sqrt(16, 0) == 4.0

    def test_sqrt_non_perfect_square(self):
        assert self.calc.sqrt(2, 0) == pytest.approx(1.414213562, rel=1e-5)

    def test_sqrt_zero(self):
        assert self.calc.sqrt(0, 0) == 0.0

    def test_sqrt_negative_raises(self):
        with pytest.raises(ValueError, match="Square root of negative number is not allowed"):
            self.calc.sqrt(-1, 0)

    def test_power(self):
        assert self.calc.power(2, 3) == 8

    def test_power_zero_exponent(self):
        assert self.calc.power(5, 0) == 1

    def test_power_negative_exponent(self):
        assert self.calc.power(2, -2) == pytest.approx(0.25)

    def test_power_fractional_exponent(self):
        assert self.calc.power(4, 0.5) == pytest.approx(2.0)

    def test_power_negative_base(self):
        assert self.calc.power(-2, 3) == -8

    def test_modulo(self):
        assert self.calc.modulo(10, 3) == 1

    def test_modulo_exact_division(self):
        assert self.calc.modulo(10, 5) == 0

    def test_modulo_floats(self):
        assert self.calc.modulo(7.5, 2) == pytest.approx(1.5)

    def test_modulo_negative(self):
        assert self.calc.modulo(-10, 3) == 2

    def test_modulo_by_zero_raises(self):
        with pytest.raises(ValueError, match="Modulo by zero is not allowed"):
            self.calc.modulo(5, 0)

    def test_calculate_dispatches_all_operations(self):
        assert self.calc.calculate(Operation.ADD,      3, 5) == 8
        assert self.calc.calculate(Operation.SUBTRACT, 10, 4) == 6
        assert self.calc.calculate(Operation.MULTIPLY, 3, 5) == 15
        assert self.calc.calculate(Operation.DIVIDE,   10, 2) == 5.0
        assert self.calc.calculate(Operation.SQUARE,   5, 0) == 25
        assert self.calc.calculate(Operation.SQRT,     9, 0) == 3.0
        assert self.calc.calculate(Operation.POWER,    2, 3) == 8
        assert self.calc.calculate(Operation.MODULO,   10, 3) == 1
