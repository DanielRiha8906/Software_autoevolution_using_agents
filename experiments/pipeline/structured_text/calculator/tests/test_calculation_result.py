import pytest
from src.models.calculation_result import CalculationResult

_TS = "2026-01-01T00:00:00"


class TestCalculationResultSymbols:
    def test_square_symbol(self):
        result = CalculationResult("square", 5, 0, 25, _TS, 0.0)
        assert "²" in str(result)

    def test_sqrt_symbol(self):
        result = CalculationResult("sqrt", 4, 0, 2.0, _TS, 0.0)
        assert "√" in str(result)

    def test_power_symbol(self):
        result = CalculationResult("power", 2, 3, 8, _TS, 0.0)
        assert "^" in str(result)

    def test_modulo_symbol(self):
        result = CalculationResult("modulo", 10, 3, 1, _TS, 0.0)
        assert "%" in str(result)
