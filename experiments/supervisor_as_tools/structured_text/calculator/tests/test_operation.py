import pytest
from src.models.operation import Operation


class TestOperation:
    def test_from_string_add(self):
        assert Operation.from_string("add") == Operation.ADD

    def test_from_string_subtract(self):
        assert Operation.from_string("subtract") == Operation.SUBTRACT

    def test_from_string_multiply(self):
        assert Operation.from_string("multiply") == Operation.MULTIPLY

    def test_from_string_divide(self):
        assert Operation.from_string("divide") == Operation.DIVIDE

    def test_from_string_square(self):
        assert Operation.from_string("square") == Operation.SQUARE

    def test_from_string_sqrt(self):
        assert Operation.from_string("sqrt") == Operation.SQRT

    def test_from_string_power(self):
        assert Operation.from_string("power") == Operation.POWER

    def test_from_string_modulo(self):
        assert Operation.from_string("modulo") == Operation.MODULO

    def test_from_string_case_insensitive(self):
        assert Operation.from_string("ADD") == Operation.ADD
        assert Operation.from_string("Sqrt") == Operation.SQRT
        assert Operation.from_string("POWER") == Operation.POWER

    def test_from_string_invalid_raises(self):
        with pytest.raises(ValueError, match="Unknown operation"):
            Operation.from_string("invalid")

    def test_display_name_add(self):
        assert Operation.ADD.display_name() == "Add"

    def test_display_name_subtract(self):
        assert Operation.SUBTRACT.display_name() == "Subtract"

    def test_display_name_multiply(self):
        assert Operation.MULTIPLY.display_name() == "Multiply"

    def test_display_name_divide(self):
        assert Operation.DIVIDE.display_name() == "Divide"

    def test_display_name_square(self):
        assert Operation.SQUARE.display_name() == "Square"

    def test_display_name_sqrt(self):
        assert Operation.SQRT.display_name() == "Sqrt"

    def test_display_name_power(self):
        assert Operation.POWER.display_name() == "Power"

    def test_display_name_modulo(self):
        assert Operation.MODULO.display_name() == "Modulo"
