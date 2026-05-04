import math
import pytest
from src.services.calculator import Calculator
from src.services.scientific_calculator import ScientificCalculator


def test_scientific_calculator_exists():
    calc = ScientificCalculator()
    assert calc is not None


def test_sin():
    calc = ScientificCalculator()
    assert calc.sin(0) == pytest.approx(0.0)


def test_cos():
    calc = ScientificCalculator()
    assert calc.cos(0) == pytest.approx(1.0)


def test_tan():
    calc = ScientificCalculator()
    assert calc.tan(0) == pytest.approx(0.0)


def test_log_base_10():
    calc = ScientificCalculator()
    assert calc.log(100) == pytest.approx(2.0)


def test_log_of_non_positive_raises():
    calc = ScientificCalculator()
    with pytest.raises(Exception):
        calc.log(0)


def test_ln():
    calc = ScientificCalculator()
    assert calc.ln(math.e) == pytest.approx(1.0)


def test_exp():
    calc = ScientificCalculator()
    assert calc.exp(1) == pytest.approx(math.e)


def test_standard_operations_still_work():
    calc = ScientificCalculator()
    assert calc.add(2, 3) == 5
    assert calc.divide(10, 2) == 5
