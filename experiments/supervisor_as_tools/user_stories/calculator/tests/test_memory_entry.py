import pytest
from datetime import datetime
from uuid import uuid4
from src.models.memory_entry import MemoryEntry


class TestMemoryEntryCreation:
    """Test MemoryEntry instance creation with all fields."""

    def test_successful_entry_creation_with_all_fields(self):
        """Test creating a successful MemoryEntry with all required fields."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            entry_id="test-id-123",
            error_message=None,
            timestamp="2026-01-01T12:00:00",
            execution_time_ms=2.5,
        )
        assert entry.operation_name == "add"
        assert entry.operand_a == 3.0
        assert entry.operand_b == 5.0
        assert entry.result == 8.0
        assert entry.success is True
        assert entry.entry_id == "test-id-123"
        assert entry.error_message is None
        assert entry.timestamp == "2026-01-01T12:00:00"
        assert entry.execution_time_ms == 2.5

    def test_failed_entry_creation_with_error_message(self):
        """Test creating a failed MemoryEntry with error_message and result=None."""
        entry = MemoryEntry(
            operation_name="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            success=False,
            entry_id="test-id-456",
            error_message="Division by zero",
            timestamp="2026-01-01T12:00:01",
            execution_time_ms=1.0,
        )
        assert entry.operation_name == "divide"
        assert entry.operand_a == 5.0
        assert entry.operand_b == 0.0
        assert entry.result is None
        assert entry.success is False
        assert entry.entry_id == "test-id-456"
        assert entry.error_message == "Division by zero"
        assert entry.timestamp == "2026-01-01T12:00:01"
        assert entry.execution_time_ms == 1.0


class TestMemoryEntryAutoGeneration:
    """Test auto-generation of entry_id and timestamp."""

    def test_unique_entry_id_generation(self):
        """Test that multiple entries get unique entry_id values."""
        entry1 = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
        )
        entry2 = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
        )
        assert entry1.entry_id != entry2.entry_id
        assert len(entry1.entry_id) == 32  # hex UUID is 32 chars
        assert len(entry2.entry_id) == 32

    def test_entry_id_is_hex_string(self):
        """Test that auto-generated entry_id is a valid hex string."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
        )
        # Should be valid hex
        int(entry.entry_id, 16)
        assert entry.entry_id == entry.entry_id.lower()

    def test_timestamp_is_iso_format(self):
        """Test that auto-generated timestamp is ISO format (parseable)."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
        )
        # Should be parseable as ISO datetime
        parsed = datetime.fromisoformat(entry.timestamp)
        assert isinstance(parsed, datetime)

    def test_timestamp_generated_automatically(self):
        """Test that timestamp is auto-generated if not provided."""
        before = datetime.now().isoformat()
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
        )
        after = datetime.now().isoformat()
        # Timestamp should be between before and after
        assert before <= entry.timestamp <= after

    def test_entry_id_generated_automatically(self):
        """Test that entry_id is auto-generated if not provided."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
        )
        assert entry.entry_id != ""
        assert len(entry.entry_id) == 32


class TestMemoryEntrySerialization:
    """Test to_dict() and from_dict() serialization."""

    def test_to_dict_successful_entry_includes_all_fields(self):
        """Test to_dict() includes all 9 fields for a successful entry."""
        entry = MemoryEntry(
            operation_name="multiply",
            operand_a=3.0,
            operand_b=4.0,
            result=12.0,
            success=True,
            entry_id="id-123",
            error_message=None,
            timestamp="2026-01-01T12:00:00",
            execution_time_ms=3.5,
        )
        d = entry.to_dict()
        assert d["operation_name"] == "multiply"
        assert d["operand_a"] == 3.0
        assert d["operand_b"] == 4.0
        assert d["result"] == 12.0
        assert d["success"] is True
        assert d["entry_id"] == "id-123"
        assert d["error_message"] is None
        assert d["timestamp"] == "2026-01-01T12:00:00"
        assert d["execution_time_ms"] == 3.5
        assert len(d) == 9

    def test_to_dict_failed_entry_includes_all_fields(self):
        """Test to_dict() includes all 9 fields for a failed entry."""
        entry = MemoryEntry(
            operation_name="sqrt",
            operand_a=-4.0,
            operand_b=0.0,
            result=None,
            success=False,
            entry_id="id-456",
            error_message="Square root of negative",
            timestamp="2026-01-01T12:00:01",
            execution_time_ms=2.0,
        )
        d = entry.to_dict()
        assert d["operation_name"] == "sqrt"
        assert d["operand_a"] == -4.0
        assert d["operand_b"] == 0.0
        assert d["result"] is None
        assert d["success"] is False
        assert d["entry_id"] == "id-456"
        assert d["error_message"] == "Square root of negative"
        assert d["timestamp"] == "2026-01-01T12:00:01"
        assert d["execution_time_ms"] == 2.0
        assert len(d) == 9

    def test_from_dict_successful_entry(self):
        """Test from_dict() deserialization for a successful entry."""
        d = {
            "operation_name": "power",
            "operand_a": 2.0,
            "operand_b": 3.0,
            "result": 8.0,
            "success": True,
            "entry_id": "id-789",
            "error_message": None,
            "timestamp": "2026-01-01T12:00:02",
            "execution_time_ms": 1.5,
        }
        entry = MemoryEntry.from_dict(d)
        assert entry.operation_name == "power"
        assert entry.operand_a == 2.0
        assert entry.operand_b == 3.0
        assert entry.result == 8.0
        assert entry.success is True
        assert entry.entry_id == "id-789"
        assert entry.error_message is None
        assert entry.timestamp == "2026-01-01T12:00:02"
        assert entry.execution_time_ms == 1.5

    def test_from_dict_failed_entry(self):
        """Test from_dict() deserialization for a failed entry."""
        d = {
            "operation_name": "modulo",
            "operand_a": 10.0,
            "operand_b": 0.0,
            "result": None,
            "success": False,
            "entry_id": "id-999",
            "error_message": "Modulo by zero",
            "timestamp": "2026-01-01T12:00:03",
            "execution_time_ms": 0.8,
        }
        entry = MemoryEntry.from_dict(d)
        assert entry.operation_name == "modulo"
        assert entry.operand_a == 10.0
        assert entry.operand_b == 0.0
        assert entry.result is None
        assert entry.success is False
        assert entry.entry_id == "id-999"
        assert entry.error_message == "Modulo by zero"
        assert entry.timestamp == "2026-01-01T12:00:03"
        assert entry.execution_time_ms == 0.8

    def test_round_trip_successful(self):
        """Test round-trip to_dict() -> from_dict() for successful entry."""
        entry1 = MemoryEntry(
            operation_name="add",
            operand_a=10.0,
            operand_b=20.0,
            result=30.0,
            success=True,
            entry_id="id-rt1",
            error_message=None,
            timestamp="2026-01-01T12:00:04",
            execution_time_ms=5.0,
        )
        d = entry1.to_dict()
        entry2 = MemoryEntry.from_dict(d)
        assert entry1.operation_name == entry2.operation_name
        assert entry1.operand_a == entry2.operand_a
        assert entry1.operand_b == entry2.operand_b
        assert entry1.result == entry2.result
        assert entry1.success == entry2.success
        assert entry1.entry_id == entry2.entry_id
        assert entry1.error_message == entry2.error_message
        assert entry1.timestamp == entry2.timestamp
        assert entry1.execution_time_ms == entry2.execution_time_ms

    def test_round_trip_failed(self):
        """Test round-trip to_dict() -> from_dict() for failed entry."""
        entry1 = MemoryEntry(
            operation_name="divide",
            operand_a=99.0,
            operand_b=0.0,
            result=None,
            success=False,
            entry_id="id-rt2",
            error_message="Division error",
            timestamp="2026-01-01T12:00:05",
            execution_time_ms=2.2,
        )
        d = entry1.to_dict()
        entry2 = MemoryEntry.from_dict(d)
        assert entry1.operation_name == entry2.operation_name
        assert entry1.operand_a == entry2.operand_a
        assert entry1.operand_b == entry2.operand_b
        assert entry1.result == entry2.result
        assert entry1.success == entry2.success
        assert entry1.entry_id == entry2.entry_id
        assert entry1.error_message == entry2.error_message
        assert entry1.timestamp == entry2.timestamp
        assert entry1.execution_time_ms == entry2.execution_time_ms


class TestMemoryEntryExecutionTime:
    """Test execution_time_ms field behavior."""

    def test_custom_execution_time_ms_value(self):
        """Test setting custom execution_time_ms values."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            execution_time_ms=10.5,
        )
        assert entry.execution_time_ms == 10.5

    def test_zero_execution_time_ms_is_allowed(self):
        """Test that execution_time_ms=0 is valid."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            execution_time_ms=0.0,
        )
        assert entry.execution_time_ms == 0.0

    def test_default_execution_time_ms_is_zero(self):
        """Test that execution_time_ms defaults to 0.0 when not provided."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
        )
        assert entry.execution_time_ms == 0.0

    def test_large_execution_time_ms(self):
        """Test that large execution_time_ms values are handled."""
        entry = MemoryEntry(
            operation_name="power",
            operand_a=2.0,
            operand_b=100.0,
            result=1.26765e+30,
            success=True,
            execution_time_ms=1000000.0,
        )
        assert entry.execution_time_ms == 1000000.0


class TestMemoryEntryDefaultValues:
    """Test default value generation."""

    def test_default_entry_id_generated(self):
        """Test that entry_id is auto-generated when empty string provided."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            entry_id="",
        )
        assert entry.entry_id != ""
        assert len(entry.entry_id) == 32

    def test_default_timestamp_generated(self):
        """Test that timestamp is auto-generated when empty string provided."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            timestamp="",
        )
        assert entry.timestamp != ""
        # Should be parseable as ISO
        datetime.fromisoformat(entry.timestamp)

    def test_default_error_message_is_none(self):
        """Test that error_message defaults to None."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
        )
        assert entry.error_message is None


class TestMemoryEntryNoFormatting:
    """Verify no __str__() or __repr__() formatting logic exists."""

    def test_no_str_method(self):
        """Test that MemoryEntry doesn't override __str__()."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            entry_id="test-id",
            timestamp="2026-01-01T12:00:00",
        )
        # str() should use default dataclass representation
        s = str(entry)
        assert "MemoryEntry" in s or "operation_name" in s
        # Not a fancy formatted string like "1 + 2 = 3"
        assert "+" not in s or "operation_name" in s

    def test_no_repr_method(self):
        """Test that MemoryEntry doesn't override __repr__()."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            entry_id="test-id",
            timestamp="2026-01-01T12:00:00",
        )
        # repr() should use default dataclass representation
        r = repr(entry)
        assert "MemoryEntry" in r or "operation_name" in r
        # Not a fancy formatted string like "1 + 2 = 3"
        assert "+" not in r or "operation_name" in r


class TestMemoryEntryEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_negative_operands(self):
        """Test that negative operands are handled."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=-5.0,
            operand_b=-3.0,
            result=-8.0,
            success=True,
        )
        assert entry.operand_a == -5.0
        assert entry.operand_b == -3.0
        assert entry.result == -8.0

    def test_float_operands_and_result(self):
        """Test that float operands and results preserve precision."""
        entry = MemoryEntry(
            operation_name="divide",
            operand_a=10.0,
            operand_b=3.0,
            result=3.3333333333,
            success=True,
        )
        assert entry.operand_a == 10.0
        assert entry.operand_b == 3.0
        assert abs(entry.result - 3.3333333333) < 1e-9

    def test_zero_operands(self):
        """Test that zero operands are allowed."""
        entry = MemoryEntry(
            operation_name="square",
            operand_a=0.0,
            operand_b=0.0,
            result=0.0,
            success=True,
        )
        assert entry.operand_a == 0.0
        assert entry.operand_b == 0.0
        assert entry.result == 0.0

    def test_very_large_numbers(self):
        """Test that very large numbers are handled."""
        entry = MemoryEntry(
            operation_name="multiply",
            operand_a=1e100,
            operand_b=1e100,
            result=1e200,
            success=True,
        )
        assert entry.operand_a == 1e100
        assert entry.operand_b == 1e100
        assert entry.result == 1e200

    def test_long_error_message(self):
        """Test that long error messages are stored."""
        long_msg = "A" * 1000
        entry = MemoryEntry(
            operation_name="divide",
            operand_a=1.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message=long_msg,
        )
        assert entry.error_message == long_msg
        assert len(entry.error_message) == 1000
