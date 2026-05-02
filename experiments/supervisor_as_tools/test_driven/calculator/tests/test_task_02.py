import math
import pytest
from src.services.calculator import Calculator


def test_square_returns_correct_result():
    assert Calculator().square(4) == 16


def test_square_of_zero():
    assert Calculator().square(0) == 0


def test_sqrt_returns_correct_result():
    assert Calculator().sqrt(9) == pytest.approx(3.0)


def test_sqrt_of_negative_raises():
    with pytest.raises(Exception):
        Calculator().sqrt(-1)


def test_power_integer_exponent():
    assert Calculator().power(2, 10) == 1024


def test_power_fractional_exponent():
    assert Calculator().power(8, 1 / 3) == pytest.approx(2.0, rel=1e-5)


def test_power_negative_exponent():
    assert Calculator().power(2, -1) == pytest.approx(0.5)


def test_modulo_returns_correct_result():
    assert Calculator().modulo(10, 3) == 1


def test_modulo_by_zero_raises():
    with pytest.raises(Exception):
        Calculator().modulo(10, 0)


def test_existing_operations_unchanged():
    calc = Calculator()
    assert calc.add(2, 3) == 5
    assert calc.subtract(5, 3) == 2
    assert calc.multiply(3, 4) == 12
    assert calc.divide(10, 2) == 5
