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

    # ====== Square Tests ======
    @pytest.mark.parametrize("value,expected", [
        (0, 0),
        (1, 1),
        (2, 4),
        (5, 25),
        (10, 100),
        (-2, 4),
        (-5, 25),
        (1.5, pytest.approx(2.25)),
        (2.5, pytest.approx(6.25)),
        (-1.5, pytest.approx(2.25)),
        (0.5, pytest.approx(0.25)),
    ])
    def test_square_normal_cases(self, value, expected):
        # Note: square(a, b) only uses a, ignores b
        assert self.calc.square(value, 0) == expected

    def test_square_dispatches(self):
        assert self.calc.calculate(Operation.SQUARE, 5, 0) == 25

    # ====== Square Root Tests ======
    @pytest.mark.parametrize("value,expected", [
        (0, 0),
        (1, 1),
        (4, 2),
        (9, 3),
        (25, 5),
        (100, 10),
        (1.5, pytest.approx(1.2247448713915890)),
        (2.25, pytest.approx(1.5)),
        (0.25, pytest.approx(0.5)),
    ])
    def test_sqrt_normal_cases(self, value, expected):
        # Note: sqrt(a, b) only uses a, ignores b
        assert self.calc.sqrt(value, 0) == expected

    def test_sqrt_negative_raises(self):
        with pytest.raises(ValueError, match="Cannot take square root of negative number"):
            self.calc.sqrt(-1, 0)

    def test_sqrt_negative_various(self):
        with pytest.raises(ValueError, match="Cannot take square root of negative number"):
            self.calc.sqrt(-100, 0)

    def test_sqrt_dispatches(self):
        assert self.calc.calculate(Operation.SQRT, 16, 0) == 4

    # ====== Power Tests ======
    @pytest.mark.parametrize("base,exponent,expected", [
        (2, 0, 1),
        (2, 1, 2),
        (2, 2, 4),
        (2, 3, 8),
        (2, 10, 1024),
        (3, 2, 9),
        (5, 3, 125),
        (10, 2, 100),
        (2, -1, pytest.approx(0.5)),
        (2, -2, pytest.approx(0.25)),
        (4, -0.5, pytest.approx(0.5)),
        (9, 0.5, pytest.approx(3)),
        (2.5, 2, pytest.approx(6.25)),
        (0.5, 2, pytest.approx(0.25)),
        (10, -1, pytest.approx(0.1)),
    ])
    def test_power_normal_cases(self, base, exponent, expected):
        assert self.calc.power(base, exponent) == expected

    def test_power_dispatches(self):
        assert self.calc.calculate(Operation.POWER, 2, 5) == 32

    # ====== Modulo Tests ======
    @pytest.mark.parametrize("a,b,expected", [
        (10, 3, 1),
        (10, 5, 0),
        (7, 2, 1),
        (100, 7, 2),
        (5, 10, 5),  # a < b
        (-10, 3, 2),  # Python modulo behavior with negative a
        (10, -3, -2),  # Python modulo behavior with negative b
        (-10, -3, -1),  # Both negative
        (5.5, 2, pytest.approx(1.5)),
        (10.7, 3, pytest.approx(1.7)),
    ])
    def test_modulo_normal_cases(self, a, b, expected):
        assert self.calc.modulo(a, b) == expected

    def test_modulo_by_zero_raises(self):
        with pytest.raises(ValueError, match="Modulo by zero is not allowed"):
            self.calc.modulo(10, 0)

    def test_modulo_negative_by_zero_raises(self):
        with pytest.raises(ValueError, match="Modulo by zero is not allowed"):
            self.calc.modulo(-5, 0)

    def test_modulo_dispatches(self):
        assert self.calc.calculate(Operation.MODULO, 10, 3) == 1
