import pytest
from src.models.memory_entry import MemoryEntry
from datetime import datetime
import json

_TS = "2026-01-01T00:00:00"


class TestSuccessfulCalculations:
    """Test Class 1: Successful calculations (3 tests)."""

    def test_successful_addition(self):
        """Create and verify a successful addition MemoryEntry."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=1.5,
        )
        assert entry.operation == "add"
        assert entry.operand_a == 3.0
        assert entry.operand_b == 5.0
        assert entry.result == 8.0
        assert entry.success is True
        assert entry.error_message is None

    def test_successful_division(self):
        """Create and verify a successful division MemoryEntry."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=2.0,
            result=5.0,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=2.3,
        )
        assert entry.operation == "divide"
        assert entry.result == 5.0
        assert entry.success is True

    def test_successful_with_float_result(self):
        """Verify successful calculation with floating point result."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=3.0,
            result=3.3333333,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=0.5,
        )
        assert entry.result == 3.3333333
        assert entry.success is True


class TestFailedCalculations:
    """Test Class 2: Failed calculations (3 tests)."""

    def test_failed_division_by_zero(self):
        """Create and verify a failed division by zero MemoryEntry."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="division by zero",
            timestamp=_TS,
            execution_time_ms=0.1,
        )
        assert entry.operation == "divide"
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message == "division by zero"

    def test_failed_sqrt_negative(self):
        """Create and verify a failed square root of negative MemoryEntry."""
        entry = MemoryEntry(
            operation="sqrt",
            operand_a=-4.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="cannot take sqrt of negative number",
            timestamp=_TS,
            execution_time_ms=0.1,
        )
        assert entry.result is None
        assert entry.success is False
        assert "negative" in entry.error_message.lower()

    def test_failed_modulo_by_zero(self):
        """Create and verify a failed modulo by zero MemoryEntry."""
        entry = MemoryEntry(
            operation="modulo",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="modulo by zero",
            timestamp=_TS,
            execution_time_ms=0.05,
        )
        assert entry.success is False
        assert entry.error_message == "modulo by zero"


class TestBackwardCompatibility:
    """Test Class 3: Backward compatibility with legacy format (3 tests)."""

    def test_from_dict_old_format_defaults_to_success(self):
        """Load legacy CalculationResult format and default success=True."""
        old_data = {
            "operation": "add",
            "operand_a": 3.0,
            "operand_b": 5.0,
            "result": 8.0,
            "timestamp": _TS,
            "execution_time_ms": 1.5,
        }
        entry = MemoryEntry.from_dict(old_data)
        assert entry.success is True
        assert entry.error_message is None
        assert entry.result == 8.0

    def test_from_dict_old_format_generates_entry_id(self):
        """Verify legacy format generates entry_id on load."""
        old_data = {
            "operation": "divide",
            "operand_a": 10.0,
            "operand_b": 2.0,
            "result": 5.0,
            "timestamp": _TS,
            "execution_time_ms": 0.5,
        }
        entry = MemoryEntry.from_dict(old_data)
        assert entry.entry_id is not None
        assert isinstance(entry.entry_id, str)
        assert len(entry.entry_id) > 0

    def test_from_dict_old_format_partial_fields(self):
        """Load legacy format that may be missing execution_time_ms."""
        old_data = {
            "operation": "add",
            "operand_a": 2.0,
            "operand_b": 3.0,
            "result": 5.0,
            "timestamp": _TS,
        }
        entry = MemoryEntry.from_dict(old_data)
        assert entry.success is True
        assert entry.error_message is None
        assert entry.execution_time_ms == 0.0 or "execution_time_ms" not in old_data


class TestForwardCompatibility:
    """Test Class 4: Forward compatibility with new fields (2 tests)."""

    def test_new_format_with_all_fields(self):
        """Load new format with all fields including success and error_message."""
        new_data = {
            "operation": "divide",
            "operand_a": 10.0,
            "operand_b": 0.0,
            "result": None,
            "success": False,
            "error_message": "division by zero",
            "timestamp": _TS,
            "execution_time_ms": 0.1,
            "entry_id": "550e8400-e29b-41d4-a716-446655440000",
        }
        entry = MemoryEntry.from_dict(new_data)
        assert entry.operation == "divide"
        assert entry.success is False
        assert entry.error_message == "division by zero"
        assert entry.entry_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_new_format_successful_with_explicit_entry_id(self):
        """Load new successful format with explicit entry_id."""
        new_data = {
            "operation": "add",
            "operand_a": 3.0,
            "operand_b": 5.0,
            "result": 8.0,
            "success": True,
            "error_message": None,
            "timestamp": _TS,
            "execution_time_ms": 1.5,
            "entry_id": "test-id-123",
        }
        entry = MemoryEntry.from_dict(new_data)
        assert entry.entry_id == "test-id-123"
        assert entry.success is True


class TestRoundTripSerialization:
    """Test Class 5: Round-trip serialization (2 tests)."""

    def test_successful_round_trip(self):
        """Serialize and deserialize successful entry without data loss."""
        original = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=1.5,
            entry_id="test-id-001",
        )
        data = original.to_dict()
        restored = MemoryEntry.from_dict(data)
        assert restored.operation == original.operation
        assert restored.operand_a == original.operand_a
        assert restored.operand_b == original.operand_b
        assert restored.result == original.result
        assert restored.success == original.success
        assert restored.error_message == original.error_message
        assert restored.timestamp == original.timestamp
        assert restored.execution_time_ms == original.execution_time_ms
        assert restored.entry_id == original.entry_id

    def test_failed_round_trip(self):
        """Serialize and deserialize failed entry without data loss."""
        original = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="division by zero",
            timestamp=_TS,
            execution_time_ms=0.1,
            entry_id="test-id-002",
        )
        data = original.to_dict()
        restored = MemoryEntry.from_dict(data)
        assert restored.operation == original.operation
        assert restored.operand_a == original.operand_a
        assert restored.operand_b == original.operand_b
        assert restored.result == original.result
        assert restored.success == original.success
        assert restored.error_message == original.error_message
        assert restored.entry_id == original.entry_id


class TestValidation:
    """Test Class 6: Validation of state consistency (4 tests)."""

    def test_error_when_success_true_but_error_message_set(self):
        """Reject state: success=True with error_message not None."""
        with pytest.raises(ValueError, match="error_message must be None"):
            MemoryEntry(
                operation="add",
                operand_a=3.0,
                operand_b=5.0,
                result=8.0,
                success=True,
                error_message="some error",
                timestamp=_TS,
                execution_time_ms=1.5,
            )

    def test_error_when_success_false_but_result_set(self):
        """Reject state: success=False with result not None."""
        with pytest.raises(ValueError, match="result must be None"):
            MemoryEntry(
                operation="divide",
                operand_a=10.0,
                operand_b=0.0,
                result=5.0,
                success=False,
                error_message="division by zero",
                timestamp=_TS,
                execution_time_ms=0.1,
            )

    def test_error_when_success_true_but_result_none(self):
        """Reject state: success=True with result=None."""
        with pytest.raises(ValueError, match="result must not be None"):
            MemoryEntry(
                operation="add",
                operand_a=3.0,
                operand_b=5.0,
                result=None,
                success=True,
                error_message=None,
                timestamp=_TS,
                execution_time_ms=1.5,
            )

    def test_error_when_success_false_but_error_message_none(self):
        """Reject state: success=False with error_message=None."""
        with pytest.raises(ValueError, match="error_message must not be None"):
            MemoryEntry(
                operation="divide",
                operand_a=10.0,
                operand_b=0.0,
                result=None,
                success=False,
                error_message=None,
                timestamp=_TS,
                execution_time_ms=0.1,
            )


class TestTimestampGeneration:
    """Test Class 7: Timestamp generation (2 tests)."""

    def test_timestamp_auto_generated_if_empty(self):
        """Verify timestamp is auto-generated when not provided."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            error_message=None,
            timestamp="",
            execution_time_ms=1.5,
        )
        assert entry.timestamp != ""
        # Verify it's valid ISO 8601 format
        assert "T" in entry.timestamp
        # Verify it's parseable
        datetime.fromisoformat(entry.timestamp)

    def test_timestamp_preserved_if_provided(self):
        """Verify provided timestamp is not overwritten."""
        provided_ts = "2026-01-01T12:34:56.789000"
        entry = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            error_message=None,
            timestamp=provided_ts,
            execution_time_ms=1.5,
        )
        assert entry.timestamp == provided_ts


class TestEntryIdGeneration:
    """Test Class 8: Entry ID generation (3 tests)."""

    def test_entry_id_auto_generated_if_not_provided(self):
        """Verify entry_id is auto-generated using uuid4."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=1.5,
        )
        assert entry.entry_id is not None
        assert isinstance(entry.entry_id, str)
        # Verify it looks like a UUID (rough check)
        assert len(entry.entry_id) == 36  # UUID string format with hyphens
        assert entry.entry_id.count("-") == 4

    def test_entry_id_preserved_if_provided(self):
        """Verify provided entry_id is not overwritten."""
        custom_id = "custom-entry-id-001"
        entry = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=1.5,
            entry_id=custom_id,
        )
        assert entry.entry_id == custom_id

    def test_entry_id_unique_across_instances(self):
        """Verify each new instance gets a unique entry_id."""
        entry1 = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=1.5,
        )
        entry2 = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            error_message=None,
            timestamp=_TS,
            execution_time_ms=1.5,
        )
        assert entry1.entry_id != entry2.entry_id
