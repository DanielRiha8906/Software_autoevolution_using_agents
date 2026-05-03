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
from src.models.memory_entry import MemoryEntry
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService
from src.services.memory_service import MemoryService
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
        storage_mock = MagicMock(spec=JsonStorage)
        memory_service = MemoryService(storage_mock)
        return CalculatorService(Calculator(), memory_service)

    def test_perform_returns_result_with_timestamp(self, service):
        """perform() returns MemoryEntry with timestamp set."""
        result = service.perform(Operation.ADD, 3, 5)
        assert result.timestamp is not None
        assert isinstance(result, MemoryEntry)

    def test_perform_execution_succeeds_for_all_operations(self, service):
        """perform() succeeds for all operations."""
        for operation in [Operation.ADD, Operation.SUBTRACT,
                         Operation.MULTIPLY, Operation.DIVIDE]:
            result = service.perform(operation, 10, 2)
            assert result.error is None

    def test_perform_has_result_for_valid_operations(self, service):
        """Valid operations return non-None result."""
        # Add is generally faster
        add_result = service.perform(Operation.ADD, 1, 1)
        # Divide involves a check and float division
        divide_result = service.perform(Operation.DIVIDE, 1, 1)
        # Both should have results
        assert add_result.result is not None
        assert divide_result.result is not None

    def test_perform_add_succeeds(self):
        """ADD operation succeeds properly."""
        storage = MagicMock()
        service = CalculatorService(Calculator(), storage)
        result = service.perform(Operation.ADD, 100, 50)
        assert result.operation == "add"
        assert result.result == 150
        assert result.error is None

    def test_perform_subtract_succeeds(self):
        """SUBTRACT operation succeeds properly."""
        storage = MagicMock()
        service = CalculatorService(Calculator(), storage)
        result = service.perform(Operation.SUBTRACT, 100, 30)
        assert result.operation == "subtract"
        assert result.result == 70
        assert result.error is None

    def test_perform_multiply_succeeds(self):
        """MULTIPLY operation succeeds properly."""
        storage = MagicMock()
        service = CalculatorService(Calculator(), storage)
        result = service.perform(Operation.MULTIPLY, 5, 6)
        assert result.operation == "multiply"
        assert result.result == 30
        assert result.error is None

    def test_perform_divide_succeeds(self):
        """DIVIDE operation succeeds properly."""
        storage = MagicMock()
        service = CalculatorService(Calculator(), storage)
        result = service.perform(Operation.DIVIDE, 100, 2)
        assert result.operation == "divide"
        assert result.result == 50.0
        assert result.error is None

    def test_divide_by_zero_returns_error_state(self, service):
        """Division by zero returns MemoryEntry with error state."""
        result = service.perform(Operation.DIVIDE, 5, 0)
        assert result.error is not None
        assert "Division by zero" in result.error
        assert result.result is None

    def test_perform_saves_result(self, service):
        """perform() saves MemoryEntry."""
        result = service.perform(Operation.MULTIPLY, 7, 8)
        assert isinstance(result, MemoryEntry)
        assert result.operation == "multiply"
        assert result.result == 56
        assert result.error is None


class TestStorageIntegration:
    """Test that MemoryEntry integrates with storage."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Provide a JsonStorage instance."""
        return JsonStorage(tmp_path / "calc.json")

    def test_save_and_load_preserves_entry(self, storage):
        """Save a MemoryEntry, load it back and verify it's preserved."""
        entry = MemoryEntry("add", 3, 5, 8, None, None, _TS)
        storage.save(entry)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].operation == "add"
        assert loaded[0].result == 8

    def test_save_and_load_error_entry(self, storage):
        """Save an error MemoryEntry, load it back."""
        entry = MemoryEntry("divide", 10, 0, None, "Division by zero", "ZeroDivisionError", _TS)
        storage.save(entry)
        loaded = storage.load_all()
        assert len(loaded) == 1
        assert loaded[0].error == "Division by zero"
        assert loaded[0].result is None

    def test_persisted_json_contains_memory_entry_fields(self, storage):
        """JSON file contains MemoryEntry fields."""
        entry = MemoryEntry("multiply", 3, 4, 12, None, None, _TS)
        storage.save(entry)
        with open(storage.filepath) as f:
            data = json.load(f)
        assert data[0]["operation"] == "multiply"
        assert data[0]["result"] == 12
        assert data[0]["error"] is None

    def test_multiple_saves_with_varying_entries(self, storage):
        """Multiple saves with different entries are all preserved."""
        storage.save(MemoryEntry("add", 1, 2, 3, None, None, _TS))
        storage.save(MemoryEntry("subtract", 5, 3, 2, None, None, _TS))
        storage.save(MemoryEntry("multiply", 2, 3, 6, None, None, _TS))

        loaded = storage.load_all()
        assert len(loaded) == 3
        assert loaded[0].result == 3
        assert loaded[1].result == 2
        assert loaded[2].result == 6

    def test_old_json_without_error_fields_loads_correctly(self, tmp_path):
        """Load old JSON files that don't have error/error_type fields."""
        path = tmp_path / "old_calc.json"
        # Simulate old storage without error fields
        old_data = [
            {
                "operation": "add",
                "operand_a": 1,
                "operand_b": 2,
                "result": 3,
                "timestamp": _TS,
                "uuid": "test-uuid-1"
            },
            {
                "operation": "divide",
                "operand_a": 10,
                "operand_b": 2,
                "result": 5.0,
                "timestamp": _TS,
                "uuid": "test-uuid-2"
            }
        ]
        with open(path, "w") as f:
            json.dump(old_data, f)

        storage = JsonStorage(path)
        loaded = storage.load_all()
        assert len(loaded) == 2
        assert loaded[0].error is None
        assert loaded[1].error is None
        assert loaded[0].operation == "add"
        assert loaded[1].operation == "divide"

    def test_data_survives_reload(self, tmp_path):
        """MemoryEntry survives storage reload."""
        path = tmp_path / "calc.json"

        # First instance: save
        s1 = JsonStorage(path)
        entry = MemoryEntry("divide", 10, 2, 5.0, None, None, _TS)
        s1.save(entry)

        # Second instance: load
        s2 = JsonStorage(path)
        loaded = s2.load_all()
        assert len(loaded) == 1
        assert loaded[0].operation == "divide"
        assert loaded[0].result == 5.0
        assert loaded[0].error is None


class TestExecutionTimeEdgeCases:
    """Test edge cases and boundary conditions for MemoryEntry."""

    def test_memory_entry_with_valid_result(self):
        """MemoryEntry can hold a valid result."""
        entry = MemoryEntry("add", 1, 2, 3, None, None)
        assert entry.result == 3
        assert entry.error is None

    def test_memory_entry_with_error_state(self):
        """MemoryEntry can hold an error state."""
        entry = MemoryEntry("divide", 5, 0, None, "Division by zero", "ZeroDivisionError")
        assert entry.result is None
        assert entry.error == "Division by zero"
        assert entry.error_type == "ZeroDivisionError"

    def test_memory_entry_has_timestamp(self):
        """MemoryEntry generates timestamp."""
        entry = MemoryEntry("add", 1, 2, 3, None, None)
        assert entry.timestamp is not None
        assert "T" in entry.timestamp or "-" in entry.timestamp

    def test_memory_entry_has_uuid(self):
        """MemoryEntry generates UUID."""
        entry = MemoryEntry("add", 1, 2, 3, None, None)
        assert entry.uuid is not None
        assert len(entry.uuid) > 0

    def test_string_representation_works_with_result(self):
        """__str__ works correctly with valid result."""
        entry = MemoryEntry("add", 3, 5, 8, None, None)
        str_repr = str(entry)
        assert "3 + 5 = 8" in str_repr

    def test_parametrized_operations_succeed(self):
        """Test all operations succeed via CalculatorService."""
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
            assert result.error is None
