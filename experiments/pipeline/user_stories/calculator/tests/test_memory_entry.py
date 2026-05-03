import pytest
from uuid import UUID
from datetime import datetime
from src.models.memory_entry import MemoryEntry


class TestMemoryEntryConstruction:
    """Test basic construction and auto-generation of UUID and timestamp."""

    def test_construction_with_success(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            error=None,
            error_type=None,
        )
        assert entry.operation == "add"
        assert entry.operand_a == 3
        assert entry.operand_b == 5
        assert entry.result == 8
        assert entry.error is None
        assert entry.error_type is None

    def test_uuid_auto_generated(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            error=None,
            error_type=None,
        )
        assert entry.uuid != ""
        # Verify it's a valid UUID
        UUID(entry.uuid)

    def test_timestamp_auto_generated(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            error=None,
            error_type=None,
        )
        assert entry.timestamp != ""
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(entry.timestamp)

    def test_uuid_different_for_different_entries(self):
        entry1 = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            error=None,
            error_type=None,
        )
        entry2 = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            error=None,
            error_type=None,
        )
        assert entry1.uuid != entry2.uuid

    def test_timestamp_is_reasonable(self):
        before = datetime.now()
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            error=None,
            error_type=None,
        )
        after = datetime.now()
        entry_time = datetime.fromisoformat(entry.timestamp)
        assert before <= entry_time <= after

    def test_explicit_uuid_respected(self):
        explicit_uuid = "550e8400-e29b-41d4-a716-446655440000"
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            error=None,
            error_type=None,
            uuid=explicit_uuid,
        )
        assert entry.uuid == explicit_uuid

    def test_explicit_timestamp_respected(self):
        explicit_ts = "2026-05-03T14:30:00"
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            error=None,
            error_type=None,
            timestamp=explicit_ts,
        )
        assert entry.timestamp == explicit_ts

    def test_construction_with_error(self):
        entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            result=None,
            error="Division by zero is not allowed",
            error_type="ValueError",
        )
        assert entry.operation == "divide"
        assert entry.result is None
        assert entry.error == "Division by zero is not allowed"
        assert entry.error_type == "ValueError"

    def test_construction_with_float_operands(self):
        entry = MemoryEntry(
            operation="divide",
            operand_a=10.5,
            operand_b=2.5,
            result=4.2,
            error=None,
            error_type=None,
        )
        assert entry.operand_a == 10.5
        assert entry.operand_b == 2.5
        assert entry.result == 4.2


class TestMemoryEntrySerialization:
    """Test to_dict and from_dict methods."""

    def test_to_dict_success(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            error=None,
            error_type=None,
            timestamp="2026-05-03T14:30:00",
            uuid="550e8400-e29b-41d4-a716-446655440000",
        )
        d = entry.to_dict()
        assert d["operation"] == "add"
        assert d["operand_a"] == 3
        assert d["operand_b"] == 5
        assert d["result"] == 8
        assert d["error"] is None
        assert d["error_type"] is None
        assert d["timestamp"] == "2026-05-03T14:30:00"
        assert d["uuid"] == "550e8400-e29b-41d4-a716-446655440000"

    def test_to_dict_error(self):
        entry = MemoryEntry(
            operation="sqrt",
            operand_a=-1,
            operand_b=0,
            result=None,
            error="Cannot take square root of negative number",
            error_type="ValueError",
            timestamp="2026-05-03T14:30:00",
            uuid="550e8400-e29b-41d4-a716-446655440000",
        )
        d = entry.to_dict()
        assert d["result"] is None
        assert d["error"] == "Cannot take square root of negative number"
        assert d["error_type"] == "ValueError"

    def test_from_dict_success(self):
        data = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "result": 8,
            "error": None,
            "error_type": None,
            "timestamp": "2026-05-03T14:30:00",
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.operation == "add"
        assert entry.operand_a == 3
        assert entry.operand_b == 5
        assert entry.result == 8
        assert entry.error is None
        assert entry.error_type is None
        assert entry.timestamp == "2026-05-03T14:30:00"
        assert entry.uuid == "550e8400-e29b-41d4-a716-446655440000"

    def test_from_dict_error(self):
        data = {
            "operation": "sqrt",
            "operand_a": -1,
            "operand_b": 0,
            "result": None,
            "error": "Cannot take square root of negative number",
            "error_type": "ValueError",
            "timestamp": "2026-05-03T14:30:00",
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.error == "Cannot take square root of negative number"
        assert entry.error_type == "ValueError"

    def test_from_dict_missing_uuid_generates_new(self):
        data = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "result": 8,
            "error": None,
            "error_type": None,
            "timestamp": "2026-05-03T14:30:00",
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.uuid != ""
        UUID(entry.uuid)

    def test_from_dict_missing_error_defaults_to_none(self):
        data = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "result": 8,
            "timestamp": "2026-05-03T14:30:00",
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.error is None
        assert entry.error_type is None

    def test_from_dict_missing_error_type_defaults_to_none(self):
        data = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "result": 8,
            "error": None,
            "timestamp": "2026-05-03T14:30:00",
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.error_type is None

    def test_round_trip_success(self):
        original = MemoryEntry(
            operation="divide",
            operand_a=10,
            operand_b=2,
            result=5.0,
            error=None,
            error_type=None,
            timestamp="2026-05-03T14:30:00",
            uuid="550e8400-e29b-41d4-a716-446655440000",
        )
        d = original.to_dict()
        restored = MemoryEntry.from_dict(d)
        assert restored.operation == original.operation
        assert restored.operand_a == original.operand_a
        assert restored.operand_b == original.operand_b
        assert restored.result == original.result
        assert restored.error == original.error
        assert restored.error_type == original.error_type
        assert restored.timestamp == original.timestamp
        assert restored.uuid == original.uuid

    def test_round_trip_error(self):
        original = MemoryEntry(
            operation="sqrt",
            operand_a=-5,
            operand_b=0,
            result=None,
            error="Cannot take square root of negative number",
            error_type="ValueError",
            timestamp="2026-05-03T14:30:00",
            uuid="550e8400-e29b-41d4-a716-446655440000",
        )
        d = original.to_dict()
        restored = MemoryEntry.from_dict(d)
        assert restored.error == original.error
        assert restored.error_type == original.error_type


class TestMemoryEntryBackwardCompatibility:
    """Test backward compatibility with old JSON format."""

    def test_from_dict_preserves_execution_time_ms(self):
        """Old CalculationResult format had execution_time_ms field, now preserved."""
        data = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "result": 8,
            "timestamp": "2026-05-03T14:30:00",
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "execution_time_ms": 5.5,
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.operation == "add"
        assert entry.execution_time_ms == 5.5

    def test_from_dict_old_format_missing_error_fields(self):
        """Old format may not have error and error_type fields."""
        data = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "result": 8,
            "timestamp": "2026-05-03T14:30:00",
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.error is None
        assert entry.error_type is None

    def test_from_dict_old_format_with_execution_time_and_missing_errors(self):
        """Realistic old format, execution_time_ms now preserved."""
        data = {
            "operation": "multiply",
            "operand_a": 4,
            "operand_b": 5,
            "result": 20,
            "timestamp": "2026-01-01T00:00:00",
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "execution_time_ms": 2.1,
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.operation == "multiply"
        assert entry.result == 20
        assert entry.error is None
        assert entry.error_type is None
        assert entry.execution_time_ms == 2.1

    def test_from_dict_does_not_mutate_input(self):
        """from_dict should not mutate the input dictionary."""
        data = {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "result": 8,
            "timestamp": "2026-05-03T14:30:00",
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "execution_time_ms": 5.5,
        }
        original_keys = set(data.keys())
        MemoryEntry.from_dict(data)
        assert set(data.keys()) == original_keys
        assert data["execution_time_ms"] == 5.5


class TestMemoryEntryStringRepresentation:
    """Test __str__ method for display."""

    def test_str_success_simple_integers(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            error=None,
            error_type=None,
        )
        assert str(entry) == "3 + 5 = 8"

    def test_str_success_floats(self):
        entry = MemoryEntry(
            operation="divide",
            operand_a=10,
            operand_b=2,
            result=5.0,
            error=None,
            error_type=None,
        )
        assert str(entry) == "10 ÷ 2 = 5"

    def test_str_error(self):
        entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            result=None,
            error="Division by zero is not allowed",
            error_type="ValueError",
        )
        assert "Division by zero is not allowed" in str(entry)
        assert "ERROR" in str(entry)

    def test_str_uses_symbols(self):
        test_cases = [
            ("add", "+"),
            ("subtract", "-"),
            ("multiply", "×"),
            ("divide", "÷"),
            ("square", "²"),
            ("sqrt", "√"),
            ("power", "^"),
            ("modulo", "%"),
        ]
        for op, symbol in test_cases:
            entry = MemoryEntry(
                operation=op,
                operand_a=2,
                operand_b=3,
                result=5,
                error=None,
                error_type=None,
            )
            assert symbol in str(entry)

    def test_str_converts_float_integers(self):
        """Numbers like 5.0 should display as 5."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            error=None,
            error_type=None,
        )
        assert str(entry) == "3 + 5 = 8"

    def test_str_preserves_true_floats(self):
        """Numbers like 5.5 should display as 5.5."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=11.0,
            operand_b=2.0,
            result=5.5,
            error=None,
            error_type=None,
        )
        assert "5.5" in str(entry)

    def test_str_with_negative_operands(self):
        entry = MemoryEntry(
            operation="multiply",
            operand_a=-3,
            operand_b=5,
            result=-15,
            error=None,
            error_type=None,
        )
        assert "-3" in str(entry)
        assert "-15" in str(entry)


class TestMemoryEntryEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_operands(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=0,
            operand_b=0,
            result=0,
            error=None,
            error_type=None,
        )
        assert entry.operand_a == 0
        assert entry.operand_b == 0
        assert entry.result == 0

    def test_very_large_numbers(self):
        entry = MemoryEntry(
            operation="multiply",
            operand_a=1e308,
            operand_b=1e308,
            result=1e616,
            error=None,
            error_type=None,
        )
        assert entry.operand_a == 1e308
        assert entry.operand_b == 1e308

    def test_very_small_numbers(self):
        entry = MemoryEntry(
            operation="divide",
            operand_a=1e-308,
            operand_b=2,
            result=5e-309,
            error=None,
            error_type=None,
        )
        assert entry.operand_a == 1e-308

    def test_negative_zero(self):
        entry = MemoryEntry(
            operation="subtract",
            operand_a=0.0,
            operand_b=0.0,
            result=-0.0,
            error=None,
            error_type=None,
        )
        assert entry.result == 0.0

    def test_error_with_special_characters(self):
        entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            result=None,
            error="Error: Can't divide by zero! 🔥",
            error_type="ValueError",
        )
        assert "Can't divide by zero!" in entry.error

    def test_multiple_entries_with_same_values_have_different_uuids(self):
        """Even with identical calculation values, entries should be unique."""
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=1,
                operand_b=1,
                result=2,
                error=None,
                error_type=None,
            )
            for _ in range(5)
        ]
        uuids = [e.uuid for e in entries]
        assert len(uuids) == len(set(uuids))  # All unique


class TestMemoryEntryFieldValidation:
    """Test field types and values."""

    def test_operation_is_string(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
        )
        assert isinstance(entry.operation, str)

    def test_operand_a_is_float(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
        )
        assert isinstance(entry.operand_a, (int, float))

    def test_operand_b_is_float(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
        )
        assert isinstance(entry.operand_b, (int, float))

    def test_result_can_be_none(self):
        entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            result=None,
            error="Division by zero",
            error_type="ValueError",
        )
        assert entry.result is None

    def test_result_can_be_float(self):
        entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=2,
            result=2.5,
            error=None,
            error_type=None,
        )
        assert entry.result == 2.5

    def test_error_can_be_none(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
        )
        assert entry.error is None

    def test_error_can_be_string(self):
        entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            result=None,
            error="Division by zero",
            error_type="ValueError",
        )
        assert isinstance(entry.error, str)

    def test_uuid_is_string(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
        )
        assert isinstance(entry.uuid, str)

    def test_timestamp_is_string(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
        )
        assert isinstance(entry.timestamp, str)
