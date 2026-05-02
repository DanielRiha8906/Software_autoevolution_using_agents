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

    # ========== New operation tests: SQUARE ==========
    @pytest.mark.parametrize("a,expected", [
        (0, 0),
        (1, 1),
        (2, 4),
        (5, 25),
        (10, 100),
        (-2, 4),
        (-5, 25),
        (0.5, 0.25),
        (1.5, pytest.approx(2.25)),
        (-0.5, 0.25),
    ])
    def test_square(self, a, expected):
        """Test square operation with various inputs."""
        assert self.calc.square(a) == expected

    # ========== New operation tests: SQRT ==========
    @pytest.mark.parametrize("a,expected", [
        (0, 0),
        (1, 1),
        (4, 2),
        (9, 3),
        (16, 4),
        (25, 5),
        (100, 10),
        (0.25, 0.5),
        (0.5, pytest.approx(0.7071067811865476)),
        (2, pytest.approx(1.4142135623730951)),
    ])
    def test_sqrt(self, a, expected):
        """Test square root operation with valid inputs."""
        assert self.calc.sqrt(a) == expected

    @pytest.mark.parametrize("a", [-1, -0.5, -10, -100])
    def test_sqrt_negative_raises(self, a):
        """Test square root raises ValueError for negative inputs."""
        with pytest.raises(ValueError, match="Cannot take square root of negative number"):
            self.calc.sqrt(a)

    # ========== New operation tests: POWER ==========
    @pytest.mark.parametrize("a,b,expected", [
        (2, 0, 1),          # any number to power 0 = 1
        (2, 1, 2),          # number to power 1 = itself
        (2, 2, 4),          # 2^2
        (2, 3, 8),          # 2^3
        (2, 10, 1024),      # 2^10
        (3, 2, 9),          # 3^2
        (5, 3, 125),        # 5^3
        (10, 2, 100),       # 10^2
        (2, -1, 0.5),       # 2^-1 = 1/2
        (2, -2, 0.25),      # 2^-2 = 1/4
        (0.5, 2, 0.25),     # 0.5^2
        (10, 0.5, pytest.approx(3.1622776601683795)),  # 10^0.5 = sqrt(10)
        (4, 0.5, 2),        # 4^0.5 = 2
        (-2, 2, 4),         # negative base with even exponent
        (-2, 3, -8),        # negative base with odd exponent
    ])
    def test_power(self, a, b, expected):
        """Test power operation with various inputs."""
        assert self.calc.power(a, b) == expected

    # ========== New operation tests: MODULO ==========
    @pytest.mark.parametrize("a,b,expected", [
        (10, 3, 1),         # 10 % 3 = 1
        (7, 2, 1),          # 7 % 2 = 1
        (8, 2, 0),          # 8 % 2 = 0 (divisible)
        (15, 4, 3),         # 15 % 4 = 3
        (20, 6, 2),         # 20 % 6 = 2
        (100, 7, 2),        # 100 % 7 = 2
        (-10, 3, 2),        # negative operand with modulo
        (10, -3, -2),       # negative divisor with modulo
        (0, 5, 0),          # 0 % n = 0
        (5.5, 2, pytest.approx(1.5)),    # float operands
        (7.5, 2.5, 0),      # 7.5 % 2.5 = 0
    ])
    def test_modulo(self, a, b, expected):
        """Test modulo operation with various inputs."""
        assert self.calc.modulo(a, b) == expected

    @pytest.mark.parametrize("a", [0, 1, 5, 10, -5, 0.5, 100])
    def test_modulo_by_zero_raises(self, a):
        """Test modulo raises ValueError when dividing by zero."""
        with pytest.raises(ValueError, match="Modulo by zero is not allowed"):
            self.calc.modulo(a, 0)

    # ========== Test calculate() dispatch for new operations ==========
    @pytest.mark.parametrize("operation,a,expected", [
        (Operation.SQUARE, 5, 25),
        (Operation.SQUARE, -3, 9),
        (Operation.SQUARE, 0.5, 0.25),
    ])
    def test_calculate_square(self, operation, a, expected):
        """Test calculate() dispatch for square (unary operation)."""
        # Second operand should be ignored for unary operations
        assert self.calc.calculate(operation, a, 999) == expected

    @pytest.mark.parametrize("operation,a,expected", [
        (Operation.SQRT, 0, 0),
        (Operation.SQRT, 4, 2),
        (Operation.SQRT, 9, 3),
        (Operation.SQRT, 0.25, 0.5),
    ])
    def test_calculate_sqrt(self, operation, a, expected):
        """Test calculate() dispatch for sqrt (unary operation)."""
        # Second operand should be ignored for unary operations
        assert self.calc.calculate(operation, a, 999) == expected

    @pytest.mark.parametrize("operation,a,b,expected", [
        (Operation.POWER, 2, 3, 8),
        (Operation.POWER, 5, 2, 25),
        (Operation.POWER, 2, -1, 0.5),
    ])
    def test_calculate_power(self, operation, a, b, expected):
        """Test calculate() dispatch for power (binary operation)."""
        assert self.calc.calculate(operation, a, b) == expected

    @pytest.mark.parametrize("operation,a,b,expected", [
        (Operation.MODULO, 10, 3, 1),
        (Operation.MODULO, 7, 2, 1),
        (Operation.MODULO, 15, 4, 3),
    ])
    def test_calculate_modulo(self, operation, a, b, expected):
        """Test calculate() dispatch for modulo (binary operation)."""
        assert self.calc.calculate(operation, a, b) == expected

    def test_calculate_sqrt_negative_raises(self):
        """Test calculate() raises for sqrt of negative number."""
        with pytest.raises(ValueError, match="Cannot take square root of negative number"):
            self.calc.calculate(Operation.SQRT, -1, 0)

    def test_calculate_modulo_by_zero_raises(self):
        """Test calculate() raises for modulo by zero."""
        with pytest.raises(ValueError, match="Modulo by zero is not allowed"):
            self.calc.calculate(Operation.MODULO, 10, 0)
