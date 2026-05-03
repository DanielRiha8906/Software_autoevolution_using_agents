import pytest
from datetime import datetime
import uuid
from src.models.memory_entry import MemoryEntry


class TestMemoryEntryFieldInstantiation:
    """Test MemoryEntry field instantiation and defaults."""

    def test_instantiate_with_all_fields(self):
        """Test 1: Create MemoryEntry with all fields explicitly provided."""
        timestamp = "2026-05-03T10:00:00.000000"
        entry_id = "test-id-123"

        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_timestamp=timestamp,
            execution_time_ms=1.5,
            memory_entry_id=entry_id
        )

        assert entry.operation == "add"
        assert entry.operand_a == 1.0
        assert entry.operand_b == 2.0
        assert entry.result == 3.0
        assert entry.success is True
        assert entry.error_message is None
        assert entry.execution_timestamp == timestamp
        assert entry.execution_time_ms == 1.5
        assert entry.memory_entry_id == entry_id

    def test_instantiate_with_defaults_auto_generates_timestamp_and_id(self):
        """Test 2: Fields with defaults are auto-generated when empty/None."""
        entry = MemoryEntry(
            operation="subtract",
            operand_a=5.0,
            operand_b=3.0,
            result=2.0,
            success=True,
            error_message=None
        )

        # execution_timestamp should be auto-generated
        assert entry.execution_timestamp != ""
        assert "T" in entry.execution_timestamp

        # memory_entry_id should be auto-generated
        assert entry.memory_entry_id is not None
        # Verify it looks like a valid UUID
        uuid.UUID(entry.memory_entry_id)

        # Defaults for optional fields
        assert entry.execution_time_ms == 0.0

    def test_instantiate_with_failure_fields(self):
        """Test 3: Instantiate with failure case (result=None, success=False, error_message set)."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero"
        )

        assert entry.operation == "divide"
        assert entry.operand_a == 10.0
        assert entry.operand_b == 0.0
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message == "Division by zero"


class TestMemoryEntrySerialization:
    """Test MemoryEntry to_dict() serialization."""

    def test_to_dict_successful_calculation(self):
        """Test 1: to_dict() includes all fields for successful calculation."""
        timestamp = "2026-05-03T10:00:00"
        entry_id = "test-uuid"

        entry = MemoryEntry(
            operation="multiply",
            operand_a=3.0,
            operand_b=4.0,
            result=12.0,
            success=True,
            error_message=None,
            execution_timestamp=timestamp,
            execution_time_ms=2.3,
            memory_entry_id=entry_id
        )

        result_dict = entry.to_dict()

        assert result_dict["operation"] == "multiply"
        assert result_dict["operand_a"] == 3.0
        assert result_dict["operand_b"] == 4.0
        assert result_dict["result"] == 12.0
        assert result_dict["success"] is True
        assert result_dict["error_message"] is None
        assert result_dict["execution_timestamp"] == timestamp
        assert result_dict["execution_time_ms"] == 2.3
        assert result_dict["memory_entry_id"] == entry_id

    def test_to_dict_failed_calculation(self):
        """Test 2: to_dict() correctly serializes failed calculation with error_message."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Cannot divide by zero"
        )

        result_dict = entry.to_dict()

        assert result_dict["success"] is False
        assert result_dict["result"] is None
        assert result_dict["error_message"] == "Cannot divide by zero"

    def test_to_dict_all_keys_present(self):
        """Test 3: to_dict() contains exactly all expected keys."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=1.0,
            result=2.0,
            success=True,
            error_message=None
        )

        result_dict = entry.to_dict()

        expected_keys = {
            "operation",
            "operand_a",
            "operand_b",
            "result",
            "success",
            "error_message",
            "execution_timestamp",
            "execution_time_ms",
            "memory_entry_id",
        }

        assert set(result_dict.keys()) == expected_keys


class TestMemoryEntryDeserialization:
    """Test MemoryEntry from_dict() deserialization."""

    def test_from_dict_with_all_fields(self):
        """Test 1: from_dict() recreates entry when all fields are present."""
        data = {
            "operation": "add",
            "operand_a": 2.0,
            "operand_b": 3.0,
            "result": 5.0,
            "success": True,
            "error_message": None,
            "execution_timestamp": "2026-05-03T10:30:00",
            "execution_time_ms": 1.2,
            "memory_entry_id": "uuid-123"
        }

        entry = MemoryEntry.from_dict(data)

        assert entry.operation == "add"
        assert entry.operand_a == 2.0
        assert entry.operand_b == 3.0
        assert entry.result == 5.0
        assert entry.success is True
        assert entry.error_message is None
        assert entry.execution_timestamp == "2026-05-03T10:30:00"
        assert entry.execution_time_ms == 1.2
        assert entry.memory_entry_id == "uuid-123"

    def test_from_dict_failed_entry(self):
        """Test 2: from_dict() correctly deserializes failed calculation."""
        data = {
            "operation": "divide",
            "operand_a": 10.0,
            "operand_b": 0.0,
            "result": None,
            "success": False,
            "error_message": "Division by zero",
            "execution_timestamp": "2026-05-03T11:00:00",
            "execution_time_ms": 0.5,
            "memory_entry_id": "error-uuid"
        }

        entry = MemoryEntry.from_dict(data)

        assert entry.operation == "divide"
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message == "Division by zero"


class TestMemoryEntryBackwardCompatibility:
    """Test backward compatibility with old JSON format."""

    def test_from_dict_old_format_with_timestamp_field(self):
        """Test 1: Old JSON with 'timestamp' field maps to 'execution_timestamp'."""
        old_data = {
            "operation": "add",
            "operand_a": 1.0,
            "operand_b": 2.0,
            "result": 3.0,
            "timestamp": "2026-04-01T12:00:00"
        }

        entry = MemoryEntry.from_dict(old_data)

        assert entry.execution_timestamp == "2026-04-01T12:00:00"
        assert entry.operation == "add"
        assert entry.result == 3.0

    def test_from_dict_old_format_missing_execution_time_ms(self):
        """Test 2: Old JSON missing execution_time_ms defaults to 0.0."""
        old_data = {
            "operation": "multiply",
            "operand_a": 2.0,
            "operand_b": 3.0,
            "result": 6.0,
            "timestamp": "2026-04-01T12:00:00"
        }

        entry = MemoryEntry.from_dict(old_data)

        assert entry.execution_time_ms == 0.0

    def test_from_dict_old_format_missing_success_and_error(self):
        """Test 3: Old JSON missing success/error fields infers success=True, error_message=None."""
        old_data = {
            "operation": "subtract",
            "operand_a": 10.0,
            "operand_b": 3.0,
            "result": 7.0,
            "timestamp": "2026-04-01T12:00:00"
        }

        entry = MemoryEntry.from_dict(old_data)

        assert entry.success is True
        assert entry.error_message is None

    def test_from_dict_old_format_with_new_fields_present(self):
        """Test 4: Old JSON with all new fields present preserves them as-is."""
        old_data = {
            "operation": "divide",
            "operand_a": 10.0,
            "operand_b": 2.0,
            "result": 5.0,
            "timestamp": "2026-04-01T12:00:00",
            "execution_time_ms": 2.1,
            "success": True,
            "error_message": None,
            "memory_entry_id": "preserved-uuid"
        }

        entry = MemoryEntry.from_dict(old_data)

        assert entry.execution_timestamp == "2026-04-01T12:00:00"
        assert entry.execution_time_ms == 2.1
        assert entry.success is True
        assert entry.error_message is None
        assert entry.memory_entry_id == "preserved-uuid"

    def test_from_dict_oldest_format_missing_all_new_fields(self):
        """Test 5: Oldest possible JSON format with only base fields."""
        oldest_data = {
            "operation": "add",
            "operand_a": 5.0,
            "operand_b": 5.0,
            "result": 10.0
        }

        entry = MemoryEntry.from_dict(oldest_data)

        assert entry.operation == "add"
        assert entry.operand_a == 5.0
        assert entry.operand_b == 5.0
        assert entry.result == 10.0
        # All defaults/inferred values
        # execution_timestamp auto-generated if empty (by __post_init__)
        assert entry.execution_timestamp != ""
        assert "T" in entry.execution_timestamp
        assert entry.execution_time_ms == 0.0
        assert entry.success is True
        assert entry.error_message is None
        # memory_entry_id auto-generated if None (by __post_init__)
        assert entry.memory_entry_id is not None
        uuid.UUID(entry.memory_entry_id)


class TestMemoryEntryRoundTripSerialization:
    """Test round-trip serialization: entry -> dict -> entry."""

    @pytest.mark.parametrize("operation,a,b,result,success", [
        ("add", 1.0, 2.0, 3.0, True),
        ("subtract", 10.0, 3.0, 7.0, True),
        ("multiply", 4.0, 5.0, 20.0, True),
        ("divide", 20.0, 4.0, 5.0, True),
    ])
    def test_round_trip_successful_calculations(self, operation, a, b, result, success):
        """Test 1: Successful calculations survive round-trip serialization."""
        original = MemoryEntry(
            operation=operation,
            operand_a=a,
            operand_b=b,
            result=result,
            success=success,
            error_message=None,
            execution_timestamp="2026-05-03T10:00:00",
            execution_time_ms=1.5,
            memory_entry_id="static-uuid"
        )

        serialized = original.to_dict()
        deserialized = MemoryEntry.from_dict(serialized)

        assert deserialized.operation == original.operation
        assert deserialized.operand_a == original.operand_a
        assert deserialized.operand_b == original.operand_b
        assert deserialized.result == original.result
        assert deserialized.success == original.success
        assert deserialized.error_message == original.error_message
        assert deserialized.execution_timestamp == original.execution_timestamp
        assert deserialized.execution_time_ms == original.execution_time_ms
        assert deserialized.memory_entry_id == original.memory_entry_id

    def test_round_trip_failed_calculation(self):
        """Test 2: Failed calculations with error messages survive round-trip."""
        original = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero error",
            execution_timestamp="2026-05-03T10:15:00",
            execution_time_ms=0.8,
            memory_entry_id="error-uuid"
        )

        serialized = original.to_dict()
        deserialized = MemoryEntry.from_dict(serialized)

        assert deserialized.operation == original.operation
        assert deserialized.result is None
        assert deserialized.success is False
        assert deserialized.error_message == original.error_message
        assert deserialized.execution_time_ms == original.execution_time_ms

    def test_round_trip_with_various_execution_times(self):
        """Test 3: Various execution_time_ms values survive round-trip."""
        test_times = [0.0, 0.5, 1.25, 10.75, 999.999]

        for exec_time in test_times:
            original = MemoryEntry(
                operation="add",
                operand_a=1.0,
                operand_b=1.0,
                result=2.0,
                success=True,
                error_message=None,
                execution_time_ms=exec_time
            )

            serialized = original.to_dict()
            deserialized = MemoryEntry.from_dict(serialized)

            assert deserialized.execution_time_ms == exec_time


class TestMemoryEntryStringRepresentation:
    """Test __str__ and __repr__ methods."""

    def test_str_successful_calculation(self):
        """Test 1: __str__ produces human-readable format for successful calculation."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            error_message=None
        )

        str_repr = str(entry)

        assert "add" in str_repr
        assert "3" in str_repr or "3.0" in str_repr
        assert "5" in str_repr or "5.0" in str_repr
        assert "8" in str_repr or "8.0" in str_repr
        # Should not contain error indicator
        assert "Error" not in str_repr

    def test_str_failed_calculation(self):
        """Test 2: __str__ includes error message for failed calculation."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Cannot divide by zero"
        )

        str_repr = str(entry)

        assert "divide" in str_repr
        assert "Error" in str_repr
        assert "Cannot divide by zero" in str_repr

    def test_repr_contains_all_field_names(self):
        """Test 3: __repr__ contains field names for debugging."""
        entry = MemoryEntry(
            operation="multiply",
            operand_a=2.0,
            operand_b=3.0,
            result=6.0,
            success=True,
            error_message=None
        )

        repr_str = repr(entry)

        # Check that it's a proper repr (starts with classname)
        assert repr_str.startswith("MemoryEntry(")
        # Check that field names are present
        assert "operation" in repr_str
        assert "operand_a" in repr_str
        assert "operand_b" in repr_str
        assert "result" in repr_str
        assert "success" in repr_str
        assert "error_message" in repr_str
