import math
import pytest
from src.services.calculator import Calculator


class TestSquareOperation:
    """Test the square() method."""

    def setup_method(self):
        self.calc = Calculator()

    def test_square_returns_correct_result(self):
        """Test that square(4) returns 16."""
        assert self.calc.square(4) == 16

    def test_square_of_zero(self):
        """Test that square(0) returns 0."""
        assert self.calc.square(0) == 0

    @pytest.mark.parametrize(
        "value,expected",
        [
            (1, 1),
            (2, 4),
            (3, 9),
            (5, 25),
            (10, 100),
            (-1, 1),
            (-2, 4),
            (-5, 25),
            (0.5, 0.25),
            (1.5, pytest.approx(2.25)),
            (0.1, pytest.approx(0.01)),
        ],
    )
    def test_square_various_values(self, value, expected):
        """Test square with various positive, negative, and fractional values."""
        assert self.calc.square(value) == expected

    def test_square_large_number(self):
        """Test square with a large number."""
        assert self.calc.square(1000) == 1000000

    def test_square_negative_number(self):
        """Test that squaring a negative number yields positive."""
        assert self.calc.square(-3) == 9


class TestSqrtOperation:
    """Test the sqrt() method."""

    def setup_method(self):
        self.calc = Calculator()

    def test_sqrt_returns_correct_result(self):
        """Test that sqrt(9) returns approximately 3.0."""
        assert self.calc.sqrt(9) == pytest.approx(3.0)

    def test_sqrt_of_zero(self):
        """Test that sqrt(0) returns 0."""
        assert self.calc.sqrt(0) == 0.0

    def test_sqrt_of_negative_raises(self):
        """Test that sqrt of negative number raises an Exception."""
        with pytest.raises(Exception):
            self.calc.sqrt(-1)

    @pytest.mark.parametrize(
        "value,expected",
        [
            (1, 1.0),
            (4, 2.0),
            (16, 4.0),
            (25, 5.0),
            (100, 10.0),
            (0.25, 0.5),
            (0.01, 0.1),
            (2, pytest.approx(math.sqrt(2))),
            (3, pytest.approx(math.sqrt(3))),
        ],
    )
    def test_sqrt_various_values(self, value, expected):
        """Test sqrt with various perfect and imperfect squares."""
        assert self.calc.sqrt(value) == expected

    def test_sqrt_negative_small(self):
        """Test that sqrt of small negative number raises."""
        with pytest.raises(Exception):
            self.calc.sqrt(-0.5)

    def test_sqrt_negative_large(self):
        """Test that sqrt of large negative number raises."""
        with pytest.raises(Exception):
            self.calc.sqrt(-100)


class TestPowerOperation:
    """Test the power() method."""

    def setup_method(self):
        self.calc = Calculator()

    def test_power_integer_exponent(self):
        """Test power with integer exponent: 2^10 = 1024."""
        assert self.calc.power(2, 10) == 1024

    def test_power_fractional_exponent(self):
        """Test power with fractional exponent: 8^(1/3) ≈ 2.0 (cube root)."""
        assert self.calc.power(8, 1 / 3) == pytest.approx(2.0, rel=1e-5)

    def test_power_negative_exponent(self):
        """Test power with negative exponent: 2^(-1) ≈ 0.5."""
        assert self.calc.power(2, -1) == pytest.approx(0.5)

    @pytest.mark.parametrize(
        "base,exponent,expected",
        [
            (2, 0, 1.0),
            (2, 1, 2.0),
            (2, 2, 4.0),
            (2, 3, 8.0),
            (3, 2, 9.0),
            (5, 3, 125.0),
            (10, 3, 1000.0),
            (0, 5, 0.0),
            (1, 100, 1.0),
            (5, 0, 1.0),
            (3, -1, pytest.approx(1 / 3)),
            (4, 0.5, 2.0),
            (27, 1 / 3, pytest.approx(3.0, rel=1e-5)),
        ],
    )
    def test_power_various_cases(self, base, exponent, expected):
        """Test power with various bases and exponents."""
        assert self.calc.power(base, exponent) == expected

    def test_power_fractional_base(self):
        """Test power with fractional base."""
        assert self.calc.power(0.5, 2) == 0.25

    def test_power_negative_base_integer_exponent(self):
        """Test power with negative base and integer exponent."""
        assert self.calc.power(-2, 2) == 4.0
        assert self.calc.power(-2, 3) == -8.0

    def test_power_large_exponent(self):
        """Test power with large exponent."""
        assert self.calc.power(2, 20) == 1048576


class TestModuloOperation:
    """Test the modulo() method."""

    def setup_method(self):
        self.calc = Calculator()

    def test_modulo_returns_correct_result(self):
        """Test that modulo(10, 3) returns 1."""
        assert self.calc.modulo(10, 3) == 1

    def test_modulo_by_zero_raises(self):
        """Test that modulo with divisor 0 raises an Exception."""
        with pytest.raises(Exception):
            self.calc.modulo(10, 0)

    @pytest.mark.parametrize(
        "dividend,divisor,expected",
        [
            (10, 3, 1),
            (7, 7, 0),
            (5, 10, 5),
            (20, 3, 2),
            (17, 5, 2),
            (100, 7, 2),
            (1, 2, 1),
            (0, 5, 0),
            (9, 3, 0),
            (15, 4, 3),
        ],
    )
    def test_modulo_various_cases(self, dividend, divisor, expected):
        """Test modulo with various dividend and divisor combinations."""
        assert self.calc.modulo(dividend, divisor) == expected

    def test_modulo_with_negative_dividend(self):
        """Test modulo with negative dividend."""
        # Python's modulo with negative dividend follows flooring division
        result = self.calc.modulo(-10, 3)
        assert result == pytest.approx(2)

    def test_modulo_with_negative_divisor(self):
        """Test modulo with negative divisor."""
        result = self.calc.modulo(10, -3)
        assert result == pytest.approx(-2)

    def test_modulo_with_floats(self):
        """Test modulo with floating-point numbers."""
        result = self.calc.modulo(10.5, 3)
        assert result == pytest.approx(1.5, rel=1e-9)

    def test_modulo_zero_divisor_negative(self):
        """Test that modulo with negative divisor of zero raises."""
        with pytest.raises(Exception):
            self.calc.modulo(10, -0.0)


class TestCalculatorDispatch:
    """Test the calculate() dispatch method with new operations."""

    def setup_method(self):
        self.calc = Calculator()

    def test_calculate_square_dispatch(self):
        """Test that calculate() dispatches to square correctly."""
        from src.models.operation import Operation

        # Note: square and sqrt ignore the second parameter
        result = self.calc.calculate(Operation.SQUARE, 4, 0)
        assert result == 16

    def test_calculate_sqrt_dispatch(self):
        """Test that calculate() dispatches to sqrt correctly."""
        from src.models.operation import Operation

        result = self.calc.calculate(Operation.SQRT, 9, 0)
        assert result == pytest.approx(3.0)

    def test_calculate_power_dispatch(self):
        """Test that calculate() dispatches to power correctly."""
        from src.models.operation import Operation

        result = self.calc.calculate(Operation.POWER, 2, 10)
        assert result == 1024

    def test_calculate_modulo_dispatch(self):
        """Test that calculate() dispatches to modulo correctly."""
        from src.models.operation import Operation

        result = self.calc.calculate(Operation.MODULO, 10, 3)
        assert result == 1

    def test_calculate_all_new_operations_valid(self):
        """Test that all new operations are in the dispatch table."""
        from src.models.operation import Operation

        operations = [Operation.SQUARE, Operation.SQRT, Operation.POWER, Operation.MODULO]
        for op in operations:
            # Should not raise ValueError about unsupported operation
            try:
                self.calc.calculate(op, 2, 2)
            except ValueError as e:
                if "Unsupported operation" in str(e):
                    pytest.fail(f"Operation {op} not in dispatch table: {e}")


class TestExistingOperationsUnchanged:
    """Verify that existing operations still work correctly."""

    def setup_method(self):
        self.calc = Calculator()

    def test_existing_operations_unchanged(self):
        """Test that all existing operations remain unchanged and working."""
        assert self.calc.add(2, 3) == 5
        assert self.calc.subtract(5, 3) == 2
        assert self.calc.multiply(3, 4) == 12
        assert self.calc.divide(10, 2) == 5

    def test_add_still_works(self):
        """Verify add operation."""
        assert self.calc.add(2, 3) == 5
        assert self.calc.add(-1, -1) == -2

    def test_subtract_still_works(self):
        """Verify subtract operation."""
        assert self.calc.subtract(5, 3) == 2
        assert self.calc.subtract(1, 5) == -4

    def test_multiply_still_works(self):
        """Verify multiply operation."""
        assert self.calc.multiply(3, 4) == 12
        assert self.calc.multiply(-2, 3) == -6

    def test_divide_still_works(self):
        """Verify divide operation."""
        assert self.calc.divide(10, 2) == 5
        assert self.calc.divide(7, 2) == pytest.approx(3.5)

    def test_calculate_existing_dispatch(self):
        """Test that calculate() still dispatches existing operations correctly."""
        from src.models.operation import Operation

        assert self.calc.calculate(Operation.ADD, 3, 5) == 8
        assert self.calc.calculate(Operation.SUBTRACT, 10, 4) == 6
        assert self.calc.calculate(Operation.MULTIPLY, 3, 5) == 15
        assert self.calc.calculate(Operation.DIVIDE, 10, 2) == 5.0
