import pytest
from src.models.calculation_result import CalculationResult


class TestCalculationResult:
    def test_square_display(self):
        result = CalculationResult("square", 5, 0, 25, "2026-01-01T00:00:00")
        assert "5² = 25" in str(result)

    def test_sqrt_display(self):
        result = CalculationResult("sqrt", 9, 0, 3.0, "2026-01-01T00:00:00")
        assert "√9 = 3" in str(result)

    def test_power_display(self):
        result = CalculationResult("power", 2, 3, 8, "2026-01-01T00:00:00")
        assert "2 ^ 3 = 8" in str(result)

    def test_modulo_display(self):
        result = CalculationResult("modulo", 10, 3, 1, "2026-01-01T00:00:00")
        assert "10 % 3 = 1" in str(result)
