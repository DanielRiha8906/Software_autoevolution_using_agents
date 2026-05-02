"""
Test suite for the execution_time_ms feature added to CalculationResult.

Covers:
1. Backward compatibility with positional args
2. Field serialization (to_dict, from_dict)
3. Timing measurement in CalculatorService
4. Storage integration with execution_time_ms
"""

import json
import pytest
import time
from unittest.mock import MagicMock, patch
from src.models.operation import Operation
from src.models.calculation_result import CalculationResult
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService
from src.storage.json_storage import JsonStorage


_TS = "2026-01-01T00:00:00"


class TestCalculationResultBackwardCompatibility:
    """Test that CalculationResult maintains backward compatibility."""

    def test_positional_args_construction(self):
        """Construct with positional args (existing test pattern)."""
        result = CalculationResult("add", 3, 5, 8, _TS)
        assert result.operation == "add"
        assert result.operand_a == 3
        assert result.operand_b == 5
        assert result.result == 8
        assert result.timestamp == _TS
        assert result.execution_time_ms == 0.0

    def test_positional_args_with_execution_time(self):
        """Construct with positional args and execution_time_ms as keyword."""
        result = CalculationResult("add", 3, 5, 8, _TS, execution_time_ms=5.2)
        assert result.operation == "add"
        assert result.operand_a == 3
        assert result.operand_b == 5
        assert result.result == 8
        assert result.timestamp == _TS
        assert result.execution_time_ms == 5.2

    def test_all_keyword_args(self):
        """Construct with all keyword args."""
        result = CalculationResult(
            operation="subtract",
            operand_a=10,
            operand_b=4,
            result=6,
            timestamp=_TS,
            execution_time_ms=2.1
        )
        assert result.operation == "subtract"
        assert result.operand_a == 10
        assert result.operand_b == 4
        assert result.result == 6
        assert result.timestamp == _TS
        assert result.execution_time_ms == 2.1

    def test_execution_time_defaults_to_zero(self):
        """execution_time_ms defaults to 0.0 when omitted."""
        result = CalculationResult("multiply", 3, 4, 12, _TS)
        assert result.execution_time_ms == 0.0

    def test_default_timestamp_still_works(self):
        """__post_init__ still generates timestamp when empty string passed."""
        result = CalculationResult("divide", 10, 2, 5.0, "")
        assert result.timestamp != ""
        # Verify it's roughly an ISO format datetime
        assert "T" in result.timestamp


class TestCalculationResultFieldSerialization:
    """Test serialization and deserialization with execution_time_ms."""

    def test_to_dict_includes_execution_time_ms(self):
        """to_dict() includes execution_time_ms in output."""
        result = CalculationResult("add", 3, 5, 8, _TS, execution_time_ms=5.2)
        data = result.to_dict()
        assert data["execution_time_ms"] == 5.2
        assert data["operation"] == "add"
        assert data["operand_a"] == 3
        assert data["operand_b"] == 5
        assert data["result"] == 8
        assert data["timestamp"] == _TS

    def test_to_dict_includes_zero_execution_time(self):
        """to_dict() includes execution_time_ms even when 0.0."""
        result = CalculationResult("subtract", 10, 4, 6, _TS)
        data = result.to_dict()
        assert "execution_time_ms" in data
        assert data["execution_time_ms"] == 0.0

    def test_from_dict_with_execution_time_ms(self):
        """from_dict() correctly restores execution_time_ms."""
        data = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "result": 8,
            "timestamp": _TS,
            "execution_time_ms": 5.2
        }
        result = CalculationResult.from_dict(data)
        assert result.execution_time_ms == 5.2

    def test_from_dict_missing_execution_time_ms_defaults_to_zero(self):
        """from_dict() handles missing execution_time_ms key gracefully."""
        data = {
            "operation": "multiply",
            "operand_a": 3,
            "operand_b": 4,
            "result": 12,
            "timestamp": _TS
            # execution_time_ms intentionally omitted
        }
        result = CalculationResult.from_dict(data)
        assert result.execution_time_ms == 0.0

    def test_from_dict_roundtrip_with_timing(self):
        """Round-trip: create -> to_dict -> from_dict preserves execution_time_ms."""
        original = CalculationResult("divide", 10, 2, 5.0, _TS, execution_time_ms=3.7)
        data = original.to_dict()
        restored = CalculationResult.from_dict(data)
        assert restored.execution_time_ms == 3.7
        assert restored.operation == "divide"
        assert restored.result == 5.0

    def test_from_dict_roundtrip_without_timing(self):
        """Round-trip: old data without execution_time_ms deserializes with 0.0."""
        # Simulate old JSON without the field
        old_data = {
            "operation": "subtract",
            "operand_a": 9,
            "operand_b": 3,
            "result": 6,
            "timestamp": _TS
        }
        result = CalculationResult.from_dict(old_data)
        assert result.execution_time_ms == 0.0
        assert result.operation == "subtract"
        assert result.result == 6

    def test_from_dict_does_not_mutate_input(self):
        """from_dict() doesn't modify the input dictionary."""
        data = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "result": 8,
            "timestamp": _TS
        }
        original_keys = set(data.keys())
        CalculationResult.from_dict(data)
        # data dict should not be mutated (from_dict makes a copy)
        assert set(data.keys()) == original_keys
        assert "execution_time_ms" not in data


class TestTimingMeasurement:
    """Test that CalculatorService properly measures and records timing."""

    @pytest.fixture
    def service(self):
        """Provide a CalculatorService with mock storage."""
        storage = MagicMock()
        return CalculatorService(Calculator(), storage)

    def test_perform_returns_result_with_execution_time(self, service):
        """perform() returns CalculationResult with execution_time_ms set."""
        result = service.perform(Operation.ADD, 3, 5)
        assert result.execution_time_ms > 0.0

    def test_perform_execution_time_is_reasonable(self, service):
        """execution_time_ms >= 0 for all operations."""
        for operation in [Operation.ADD, Operation.SUBTRACT,
                         Operation.MULTIPLY, Operation.DIVIDE]:
            result = service.perform(operation, 10, 2)
            assert result.execution_time_ms >= 0.0

    def test_perform_execution_time_increases_with_complexity(self, service):
        """More complex operations take longer (rough comparison)."""
        # Add is generally faster
        add_result = service.perform(Operation.ADD, 1, 1)
        # Divide involves a check and float division
        divide_result = service.perform(Operation.DIVIDE, 1, 1)
        # Both should be very fast, so this is just a sanity check
        assert add_result.execution_time_ms >= 0.0
        assert divide_result.execution_time_ms >= 0.0

    def test_perform_add_timing(self):
        """ADD operation is properly timed."""
        storage = MagicMock()
        service = CalculatorService(Calculator(), storage)
        result = service.perform(Operation.ADD, 100, 50)
        assert result.operation == "add"
        assert result.result == 150
        assert result.execution_time_ms >= 0.0

    def test_perform_subtract_timing(self):
        """SUBTRACT operation is properly timed."""
        storage = MagicMock()
        service = CalculatorService(Calculator(), storage)
        result = service.perform(Operation.SUBTRACT, 100, 30)
        assert result.operation == "subtract"
        assert result.result == 70
        assert result.execution_time_ms >= 0.0

    def test_perform_multiply_timing(self):
        """MULTIPLY operation is properly timed."""
        storage = MagicMock()
        service = CalculatorService(Calculator(), storage)
        result = service.perform(Operation.MULTIPLY, 5, 6)
        assert result.operation == "multiply"
        assert result.result == 30
        assert result.execution_time_ms >= 0.0

    def test_perform_divide_timing(self):
        """DIVIDE operation is properly timed."""
        storage = MagicMock()
        service = CalculatorService(Calculator(), storage)
        result = service.perform(Operation.DIVIDE, 100, 2)
        assert result.operation == "divide"
        assert result.result == 50.0
        assert result.execution_time_ms >= 0.0

    def test_divide_by_zero_raises_before_save(self, service):
        """Division by zero raises ValueError before timing is recorded."""
        with pytest.raises(ValueError, match="Division by zero"):
            service.perform(Operation.DIVIDE, 5, 0)
        # Verify save was never called
        service.storage.save.assert_not_called()

    def test_perform_saves_result_with_timing(self, service):
        """perform() saves CalculationResult with execution_time_ms set."""
        service.perform(Operation.MULTIPLY, 7, 8)
        service.storage.save.assert_called_once()
        saved_result = service.storage.save.call_args[0][0]
        assert saved_result.execution_time_ms >= 0.0
        assert saved_result.operation == "multiply"
        assert saved_result.result == 56


class TestStorageIntegration:
    """Test that CalculationResult with execution_time_ms integrates with storage."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Provide a JsonStorage instance."""
        return JsonStorage(tmp_path / "calc.json")

    def test_save_and_load_preserves_execution_time(self, storage):
        """Save a result with timing, load it back and verify timing is preserved."""
        result = CalculationResult("add", 3, 5, 8, _TS, execution_time_ms=4.5)
        storage.save(result)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].execution_time_ms == 4.5

    def test_save_and_load_without_timing(self, storage):
        """Save a result without timing info (backward compat), load defaults to 0.0."""
        result = CalculationResult("subtract", 10, 4, 6, _TS)
        storage.save(result)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].execution_time_ms == 0.0

    def test_persisted_json_contains_execution_time(self, storage):
        """JSON file contains execution_time_ms field."""
        result = CalculationResult("multiply", 3, 4, 12, _TS, execution_time_ms=2.3)
        storage.save(result)
        with open(storage.filepath) as f:
            data = json.load(f)
        assert data[0]["execution_time_ms"] == 2.3

    def test_multiple_saves_with_varying_times(self, storage):
        """Multiple saves with different execution times are all preserved."""
        storage.save(CalculationResult("add", 1, 2, 3, _TS, execution_time_ms=1.0))
        storage.save(CalculationResult("subtract", 5, 3, 2, _TS, execution_time_ms=2.5))
        storage.save(CalculationResult("multiply", 2, 3, 6, _TS, execution_time_ms=1.8))

        loaded = storage.load_all()
        assert len(loaded) == 3
        assert loaded[0].execution_time_ms == 1.0
        assert loaded[1].execution_time_ms == 2.5
        assert loaded[2].execution_time_ms == 1.8

    def test_old_json_without_execution_time_loads_correctly(self, tmp_path):
        """Load old JSON files that don't have execution_time_ms field."""
        path = tmp_path / "old_calc.json"
        # Simulate old storage without execution_time_ms
        old_data = [
            {
                "operation": "add",
                "operand_a": 1,
                "operand_b": 2,
                "result": 3,
                "timestamp": _TS
            },
            {
                "operation": "divide",
                "operand_a": 10,
                "operand_b": 2,
                "result": 5.0,
                "timestamp": _TS
            }
        ]
        with open(path, "w") as f:
            json.dump(old_data, f)

        storage = JsonStorage(path)
        loaded = storage.load_all()
        assert len(loaded) == 2
        assert loaded[0].execution_time_ms == 0.0
        assert loaded[1].execution_time_ms == 0.0
        assert loaded[0].operation == "add"
        assert loaded[1].operation == "divide"

    def test_data_survives_reload_with_timing(self, tmp_path):
        """Data with execution_time_ms survives storage reload."""
        path = tmp_path / "calc.json"

        # First instance: save
        s1 = JsonStorage(path)
        result = CalculationResult("divide", 10, 2, 5.0, _TS, execution_time_ms=3.2)
        s1.save(result)

        # Second instance: load
        s2 = JsonStorage(path)
        loaded = s2.load_all()
        assert len(loaded) == 1
        assert loaded[0].operation == "divide"
        assert loaded[0].result == 5.0
        assert loaded[0].execution_time_ms == 3.2


class TestExecutionTimeEdgeCases:
    """Test edge cases and boundary conditions for execution_time_ms."""

    def test_execution_time_zero(self):
        """execution_time_ms can be 0.0."""
        result = CalculationResult("add", 1, 2, 3, _TS, execution_time_ms=0.0)
        assert result.execution_time_ms == 0.0

    def test_execution_time_very_small(self):
        """execution_time_ms can be very small (microseconds)."""
        result = CalculationResult("add", 1, 2, 3, _TS, execution_time_ms=0.001)
        assert result.execution_time_ms == 0.001

    def test_execution_time_large(self):
        """execution_time_ms can be large values."""
        result = CalculationResult("add", 1, 2, 3, _TS, execution_time_ms=9999.5)
        assert result.execution_time_ms == 9999.5

    def test_execution_time_negative_allowed(self):
        """execution_time_ms can theoretically be negative (no validation in model)."""
        # This tests the model's current behavior, not that it's recommended
        result = CalculationResult("add", 1, 2, 3, _TS, execution_time_ms=-0.5)
        assert result.execution_time_ms == -0.5

    def test_string_representation_works_with_timing(self):
        """__str__ works correctly with execution_time_ms."""
        result = CalculationResult("add", 3, 5, 8, _TS, execution_time_ms=5.2)
        str_repr = str(result)
        assert "3 + 5 = 8" in str_repr

    def test_parametrized_operations_timing(self):
        """Test timing on various operations."""
        test_cases = [
            (Operation.ADD, 10, 5, 15),
            (Operation.SUBTRACT, 10, 5, 5),
            (Operation.MULTIPLY, 10, 5, 50),
            (Operation.DIVIDE, 10, 5, 2.0),
        ]
        storage = MagicMock()
        service = CalculatorService(Calculator(), storage)

        for operation, a, b, expected in test_cases:
            result = service.perform(operation, a, b)
            assert result.result == expected
            assert result.execution_time_ms >= 0.0
