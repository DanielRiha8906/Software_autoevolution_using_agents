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
        import math
        assert self.calc.calculate(Operation.ADD,      3, 5) == 8
        assert self.calc.calculate(Operation.SUBTRACT, 10, 4) == 6
        assert self.calc.calculate(Operation.MULTIPLY, 3, 5) == 15
        assert self.calc.calculate(Operation.DIVIDE,   10, 2) == 5.0
        assert self.calc.calculate(Operation.SQUARE,   5, 0) == 25
        assert self.calc.calculate(Operation.SQRT,     9, 0) == 3.0
        assert self.calc.calculate(Operation.POWER,    2, 3) == 8
        assert self.calc.calculate(Operation.MODULO,   10, 3) == 1
        assert self.calc.calculate(Operation.SIN,      0, 0) == pytest.approx(0.0)
        assert self.calc.calculate(Operation.COS,      0, 0) == pytest.approx(1.0)
        assert self.calc.calculate(Operation.TAN,      0, 0) == pytest.approx(0.0)
        assert self.calc.calculate(Operation.LOG,      100, 0) == pytest.approx(2.0)
        assert self.calc.calculate(Operation.LN,       math.e, 0) == pytest.approx(1.0)
        assert self.calc.calculate(Operation.EXP,      0, 0) == pytest.approx(1.0)


class TestSquare:
    def setup_method(self):
        self.calc = Calculator()

    def test_square_positive_integer(self):
        assert self.calc.square(5, 0) == 25

    def test_square_zero(self):
        assert self.calc.square(0, 0) == 0

    def test_square_negative(self):
        assert self.calc.square(-4, 0) == 16

    def test_square_float(self):
        assert self.calc.square(2.5, 0) == pytest.approx(6.25)

    def test_square_via_calculate(self):
        assert self.calc.calculate(Operation.SQUARE, 3, 0) == 9


class TestSqrt:
    def setup_method(self):
        self.calc = Calculator()

    def test_sqrt_perfect_square(self):
        assert self.calc.sqrt(9, 0) == 3.0

    def test_sqrt_zero(self):
        assert self.calc.sqrt(0, 0) == 0.0

    def test_sqrt_non_perfect_square(self):
        assert self.calc.sqrt(2, 0) == pytest.approx(1.414213, rel=1e-5)

    def test_sqrt_float_input(self):
        assert self.calc.sqrt(6.25, 0) == pytest.approx(2.5)

    def test_sqrt_negative_raises(self):
        with pytest.raises(ValueError, match="Square root of negative numbers is not allowed"):
            self.calc.sqrt(-4, 0)

    def test_sqrt_via_calculate(self):
        assert self.calc.calculate(Operation.SQRT, 16, 0) == 4.0


class TestPower:
    def setup_method(self):
        self.calc = Calculator()

    def test_power_positive_exponent(self):
        assert self.calc.power(2, 3) == 8

    def test_power_zero_exponent(self):
        assert self.calc.power(5, 0) == 1

    def test_power_negative_exponent(self):
        assert self.calc.power(2, -2) == pytest.approx(0.25)

    def test_power_base_one(self):
        assert self.calc.power(1, 100) == 1

    def test_power_float_inputs(self):
        assert self.calc.power(2.5, 2) == pytest.approx(6.25)

    def test_power_zero_to_negative_raises(self):
        with pytest.raises(ValueError, match="Cannot raise zero to a negative power"):
            self.calc.power(0, -1)

    def test_power_via_calculate(self):
        assert self.calc.calculate(Operation.POWER, 3, 2) == 9


class TestModulo:
    def setup_method(self):
        self.calc = Calculator()

    def test_modulo_basic(self):
        assert self.calc.modulo(10, 3) == 1

    def test_modulo_evenly_divisible(self):
        assert self.calc.modulo(10, 2) == 0

    def test_modulo_result_equals_dividend(self):
        assert self.calc.modulo(5, 10) == 5

    def test_modulo_negative_dividend(self):
        assert self.calc.modulo(-10, 3) == 2

    def test_modulo_float_inputs(self):
        assert self.calc.modulo(5.5, 2.0) == pytest.approx(1.5)

    def test_modulo_by_zero_raises(self):
        with pytest.raises(ValueError, match="Modulo by zero is not allowed"):
            self.calc.modulo(10, 0)

    def test_modulo_via_calculate(self):
        assert self.calc.calculate(Operation.MODULO, 7, 3) == 1


class TestSin:
    def setup_method(self):
        self.calc = Calculator()

    def test_sin_zero(self):
        assert self.calc.sin(0, 0) == pytest.approx(0.0)

    def test_sin_pi_over_2(self):
        import math
        assert self.calc.sin(math.pi / 2, 0) == pytest.approx(1.0)

    def test_sin_pi(self):
        import math
        assert self.calc.sin(math.pi, 0) == pytest.approx(0.0, abs=1e-10)

    def test_sin_negative_angle(self):
        import math
        assert self.calc.sin(-math.pi / 2, 0) == pytest.approx(-1.0)

    def test_sin_float_angle(self):
        assert self.calc.sin(0.5, 0) == pytest.approx(0.479426, rel=1e-5)

    def test_sin_via_calculate(self):
        result = self.calc.calculate(Operation.SIN, 0, 0)
        assert result == pytest.approx(0.0)


class TestCos:
    def setup_method(self):
        self.calc = Calculator()

    def test_cos_zero(self):
        assert self.calc.cos(0, 0) == pytest.approx(1.0)

    def test_cos_pi_over_2(self):
        import math
        assert self.calc.cos(math.pi / 2, 0) == pytest.approx(0.0, abs=1e-10)

    def test_cos_pi(self):
        import math
        assert self.calc.cos(math.pi, 0) == pytest.approx(-1.0)

    def test_cos_negative_angle(self):
        import math
        assert self.calc.cos(-math.pi, 0) == pytest.approx(-1.0)

    def test_cos_float_angle(self):
        assert self.calc.cos(0.5, 0) == pytest.approx(0.877583, rel=1e-5)

    def test_cos_via_calculate(self):
        result = self.calc.calculate(Operation.COS, 0, 0)
        assert result == pytest.approx(1.0)


class TestTan:
    def setup_method(self):
        self.calc = Calculator()

    def test_tan_zero(self):
        assert self.calc.tan(0, 0) == pytest.approx(0.0)

    def test_tan_pi_over_4(self):
        import math
        assert self.calc.tan(math.pi / 4, 0) == pytest.approx(1.0)

    def test_tan_negative_angle(self):
        assert self.calc.tan(-0.5, 0) == pytest.approx(-0.546302, rel=1e-5)

    def test_tan_float_angle(self):
        assert self.calc.tan(0.3, 0) == pytest.approx(0.309336, rel=1e-5)

    def test_tan_via_calculate(self):
        result = self.calc.calculate(Operation.TAN, 0, 0)
        assert result == pytest.approx(0.0)


class TestLog:
    def setup_method(self):
        self.calc = Calculator()

    def test_log_100(self):
        assert self.calc.log(100, 0) == pytest.approx(2.0)

    def test_log_10(self):
        assert self.calc.log(10, 0) == pytest.approx(1.0)

    def test_log_1(self):
        assert self.calc.log(1, 0) == pytest.approx(0.0)

    def test_log_float_input(self):
        assert self.calc.log(1000, 0) == pytest.approx(3.0)

    def test_log_zero_raises(self):
        with pytest.raises(ValueError, match="Logarithm of x <= 0 is not allowed"):
            self.calc.log(0, 0)

    def test_log_negative_raises(self):
        with pytest.raises(ValueError, match="Logarithm of x <= 0 is not allowed"):
            self.calc.log(-5, 0)

    def test_log_via_calculate(self):
        result = self.calc.calculate(Operation.LOG, 100, 0)
        assert result == pytest.approx(2.0)


class TestLn:
    def setup_method(self):
        self.calc = Calculator()

    def test_ln_e(self):
        import math
        assert self.calc.ln(math.e, 0) == pytest.approx(1.0)

    def test_ln_1(self):
        assert self.calc.ln(1, 0) == pytest.approx(0.0)

    def test_ln_float_input(self):
        import math
        assert self.calc.ln(math.e ** 2, 0) == pytest.approx(2.0)

    def test_ln_zero_raises(self):
        with pytest.raises(ValueError, match="Logarithm of x <= 0 is not allowed"):
            self.calc.ln(0, 0)

    def test_ln_negative_raises(self):
        with pytest.raises(ValueError, match="Logarithm of x <= 0 is not allowed"):
            self.calc.ln(-5, 0)

    def test_ln_via_calculate(self):
        import math
        result = self.calc.calculate(Operation.LN, math.e, 0)
        assert result == pytest.approx(1.0)


class TestExp:
    def setup_method(self):
        self.calc = Calculator()

    def test_exp_zero(self):
        assert self.calc.exp(0, 0) == pytest.approx(1.0)

    def test_exp_one(self):
        import math
        assert self.calc.exp(1, 0) == pytest.approx(math.e)

    def test_exp_two(self):
        import math
        assert self.calc.exp(2, 0) == pytest.approx(math.e ** 2)

    def test_exp_negative(self):
        import math
        assert self.calc.exp(-1, 0) == pytest.approx(1.0 / math.e)

    def test_exp_float_input(self):
        import math
        assert self.calc.exp(0.5, 0) == pytest.approx(math.sqrt(math.e))

    def test_exp_via_calculate(self):
        import math
        result = self.calc.calculate(Operation.EXP, 0, 0)
        assert result == pytest.approx(1.0)
