import pytest
from src.models.calculation_result import CalculationResult


class TestCalculationResultModel:
    """Test CalculationResult dataclass field behavior and serialization."""

    def test_accepts_execution_time_ms_field(self):
        """Test 1: CalculationResult accepts execution_time_ms field on instantiation."""
        result = CalculationResult(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            execution_time_ms=1.5
        )
        assert result.execution_time_ms == 1.5

    def test_default_execution_time_ms_is_zero(self):
        """Test 2: CalculationResult has default value of 0.0 for execution_time_ms."""
        result = CalculationResult(
            operation="subtract",
            operand_a=10.0,
            operand_b=4.0,
            result=6.0
        )
        assert result.execution_time_ms == 0.0

    def test_from_dict_backward_compatibility_missing_execution_time_ms(self):
        """Test 3: Loading old JSON records without execution_time_ms defaults to 0.0."""
        old_data = {
            "operation": "multiply",
            "operand_a": 3.0,
            "operand_b": 4.0,
            "result": 12.0,
            "timestamp": "2026-01-01T12:00:00"
        }
        result = CalculationResult.from_dict(old_data)
        assert result.execution_time_ms == 0.0
        assert result.operation == "multiply"
        assert result.result == 12.0

    def test_to_dict_includes_execution_time_ms(self):
        """Test 4: execution_time_ms is included in to_dict() output."""
        result = CalculationResult(
            operation="divide",
            operand_a=10.0,
            operand_b=2.0,
            result=5.0,
            execution_time_ms=2.3
        )
        result_dict = result.to_dict()
        assert "execution_time_ms" in result_dict
        assert result_dict["execution_time_ms"] == 2.3

    def test_to_dict_all_fields_present(self):
        """Test 4b: to_dict includes all required fields."""
        result = CalculationResult(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            execution_time_ms=0.5
        )
        result_dict = result.to_dict()
        assert "operation" in result_dict
        assert "operand_a" in result_dict
        assert "operand_b" in result_dict
        assert "result" in result_dict
        assert "timestamp" in result_dict
        assert "execution_time_ms" in result_dict

    @pytest.mark.parametrize("exec_time", [0.0, 0.5, 1.0, 1.5, 2.3, 10.7, 999.9])
    def test_execution_time_ms_various_values(self, exec_time):
        """Test 4c: execution_time_ms accepts various float values."""
        result = CalculationResult(
            operation="add",
            operand_a=1.0,
            operand_b=1.0,
            result=2.0,
            execution_time_ms=exec_time
        )
        assert result.execution_time_ms == exec_time

    def test_round_trip_serialization_with_execution_time_ms(self):
        """Test 4d: execution_time_ms survives serialization round-trip."""
        original = CalculationResult(
            operation="subtract",
            operand_a=100.0,
            operand_b=42.0,
            result=58.0,
            execution_time_ms=3.7
        )
        serialized = original.to_dict()
        deserialized = CalculationResult.from_dict(serialized)
        assert deserialized.execution_time_ms == 3.7
        assert deserialized.operation == original.operation
        assert deserialized.result == original.result

    def test_timestamp_auto_generated(self):
        """Test that timestamp is auto-generated if not provided."""
        result = CalculationResult(
            operation="add",
            operand_a=1.0,
            operand_b=1.0,
            result=2.0
        )
        assert result.timestamp != ""
        assert "T" in result.timestamp

    def test_str_representation(self):
        """Test __str__ method produces readable output."""
        result = CalculationResult(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0
        )
        str_repr = str(result)
        assert "3" in str_repr
        assert "5" in str_repr
        assert "8" in str_repr
        assert "+" in str_repr
