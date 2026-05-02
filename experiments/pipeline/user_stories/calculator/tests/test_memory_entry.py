import pytest
from datetime import datetime
from uuid import UUID

from src.models.memory_entry import MemoryEntry


class TestMemoryEntryCreation:
    """Test MemoryEntry creation with various inputs."""

    def test_memory_entry_with_success(self):
        """Test creating a successful MemoryEntry."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            success=True,
            error_message=None,
        )
        assert entry.operation == "add"
        assert entry.operand_a == 3
        assert entry.operand_b == 5
        assert entry.result == 8
        assert entry.success is True
        assert entry.error_message is None

    def test_memory_entry_with_failure(self):
        """Test creating a failed MemoryEntry."""
        entry = MemoryEntry(
            operation="sqrt",
            operand_a=-1,
            operand_b=0,
            result=None,
            success=False,
            error_message="Square root of negative",
        )
        assert entry.operation == "sqrt"
        assert entry.operand_a == -1
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message == "Square root of negative"

    def test_memory_entry_success_true(self):
        """Test that success field is correctly set to True."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            success=True,
            error_message=None,
        )
        assert entry.success is True
        assert isinstance(entry.success, bool)

    def test_memory_entry_success_false(self):
        """Test that success field is correctly set to False."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=1,
            operand_b=0,
            result=None,
            success=False,
            error_message="Divide by zero",
        )
        assert entry.success is False
        assert isinstance(entry.success, bool)


class TestMemoryEntryID:
    """Test MemoryEntry ID generation and handling."""

    def test_memory_entry_has_unique_id(self):
        """Test that each MemoryEntry has a unique entry_id."""
        entry1 = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        entry2 = MemoryEntry(
            operation="add",
            operand_a=2,
            operand_b=2,
            result=4,
            success=True,
            error_message=None,
        )
        entry3 = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=3,
            result=6,
            success=True,
            error_message=None,
        )
        assert entry1.entry_id != entry2.entry_id
        assert entry2.entry_id != entry3.entry_id
        assert entry1.entry_id != entry3.entry_id

    def test_memory_entry_id_is_uuid_string(self):
        """Test that entry_id is a valid UUID4 format string."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        # Verify it's a valid UUID by trying to create a UUID from it
        uuid_obj = UUID(entry.entry_id)
        assert str(uuid_obj) == entry.entry_id
        assert len(entry.entry_id) == 36  # UUID4 string with hyphens

    def test_memory_entry_id_can_be_set_explicitly(self):
        """Test that entry_id can be set explicitly."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
            entry_id="test-id-123",
        )
        assert entry.entry_id == "test-id-123"

    def test_memory_entry_id_is_set_on_creation(self):
        """Test that entry_id is auto-generated on creation."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        assert entry.entry_id is not None
        assert entry.entry_id != ""


class TestMemoryEntryTimestamp:
    """Test MemoryEntry timestamp generation and handling."""

    def test_memory_entry_timestamp_auto_generated(self):
        """Test that timestamp is auto-generated in ISO format."""
        before = datetime.now()
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        after = datetime.now()

        # Verify timestamp is valid ISO format
        entry_time = datetime.fromisoformat(entry.timestamp)

        # Verify timestamp is within reasonable bounds
        assert before <= entry_time <= after

    def test_memory_entry_timestamp_can_be_explicit(self):
        """Test that timestamp can be set explicitly."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
            timestamp="2026-05-02T10:30:00",
        )
        assert entry.timestamp == "2026-05-02T10:30:00"

    def test_memory_entry_timestamp_format(self):
        """Test that default timestamp is in ISO 8601 format."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        # Should not raise an exception if format is valid
        datetime.fromisoformat(entry.timestamp)
        assert "T" in entry.timestamp  # ISO format has T separator


class TestMemoryEntrySerialization:
    """Test MemoryEntry serialization to/from dict."""

    def test_memory_entry_to_dict_success(self):
        """Test serializing a successful MemoryEntry to dict."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            success=True,
            error_message=None,
            entry_id="test1",
            timestamp="2026-05-02T10:30:00",
            execution_time_ms=1.5,
        )
        result = entry.to_dict()

        assert isinstance(result, dict)
        assert "entry_id" in result
        assert "operation" in result
        assert "operand_a" in result
        assert "operand_b" in result
        assert "result" in result
        assert "success" in result
        assert "error_message" in result
        assert "timestamp" in result
        assert "execution_time_ms" in result
        assert len(result) == 9

        assert result["entry_id"] == "test1"
        assert result["operation"] == "add"
        assert result["operand_a"] == 1
        assert result["operand_b"] == 2
        assert result["result"] == 3
        assert result["success"] is True
        assert result["error_message"] is None
        assert result["timestamp"] == "2026-05-02T10:30:00"
        assert result["execution_time_ms"] == 1.5

    def test_memory_entry_to_dict_failure(self):
        """Test serializing a failed MemoryEntry to dict."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=1,
            operand_b=0,
            result=None,
            success=False,
            error_message="Error msg",
            entry_id="test2",
            timestamp="2026-05-02T10:30:00",
            execution_time_ms=0.5,
        )
        result = entry.to_dict()

        assert result["success"] is False
        assert result["result"] is None
        assert result["error_message"] == "Error msg"

    def test_memory_entry_from_dict_success(self):
        """Test deserializing a successful MemoryEntry from dict."""
        data = {
            "operation": "add",
            "operand_a": 5,
            "operand_b": 3,
            "result": 8,
            "success": True,
            "error_message": None,
            "entry_id": "test-id-1",
            "timestamp": "2026-05-02T10:30:00",
            "execution_time_ms": 0.2,
        }
        entry = MemoryEntry.from_dict(data)

        assert entry.operation == "add"
        assert entry.operand_a == 5
        assert entry.operand_b == 3
        assert entry.result == 8
        assert entry.success is True
        assert entry.error_message is None
        assert entry.entry_id == "test-id-1"
        assert entry.timestamp == "2026-05-02T10:30:00"
        assert entry.execution_time_ms == 0.2

    def test_memory_entry_from_dict_failure(self):
        """Test deserializing a failed MemoryEntry from dict."""
        data = {
            "operation": "sqrt",
            "operand_a": -1,
            "operand_b": 0,
            "result": None,
            "success": False,
            "error_message": "Error",
            "entry_id": "test-id-2",
            "timestamp": "2026-05-02T10:30:00",
            "execution_time_ms": 0.1,
        }
        entry = MemoryEntry.from_dict(data)

        assert entry.success is False
        assert entry.result is None
        assert entry.error_message == "Error"

    def test_memory_entry_round_trip(self):
        """Test round-trip serialization: entry -> dict -> entry."""
        original = MemoryEntry(
            operation="multiply",
            operand_a=4,
            operand_b=5,
            result=20,
            success=True,
            error_message=None,
            entry_id="round-trip-test",
            timestamp="2026-05-02T10:30:00",
            execution_time_ms=0.3,
        )

        # Convert to dict and back
        dict_repr = original.to_dict()
        restored = MemoryEntry.from_dict(dict_repr)

        # Verify all fields match
        assert restored.operation == original.operation
        assert restored.operand_a == original.operand_a
        assert restored.operand_b == original.operand_b
        assert restored.result == original.result
        assert restored.success == original.success
        assert restored.error_message == original.error_message
        assert restored.entry_id == original.entry_id
        assert restored.timestamp == original.timestamp
        assert restored.execution_time_ms == original.execution_time_ms


class TestMemoryEntryFields:
    """Test MemoryEntry field values and defaults."""

    def test_memory_entry_with_zero_operands(self):
        """Test MemoryEntry with zero operands."""
        entry = MemoryEntry(
            operation="add",
            operand_a=0,
            operand_b=0,
            result=0,
            success=True,
            error_message=None,
        )
        assert entry.operand_a == 0
        assert entry.operand_b == 0

    def test_memory_entry_with_negative_operands(self):
        """Test MemoryEntry with negative operands."""
        entry = MemoryEntry(
            operation="add",
            operand_a=-5,
            operand_b=-10,
            result=-15,
            success=True,
            error_message=None,
        )
        assert entry.operand_a == -5
        assert entry.operand_b == -10

    def test_memory_entry_with_large_numbers(self):
        """Test MemoryEntry with very large numbers."""
        entry = MemoryEntry(
            operation="multiply",
            operand_a=1e100,
            operand_b=1e200,
            result=1e300,
            success=True,
            error_message=None,
        )
        assert entry.operand_a == pytest.approx(1e100)
        assert entry.operand_b == pytest.approx(1e200)
        assert entry.result == pytest.approx(1e300)

    def test_memory_entry_none_result_on_failure(self):
        """Test that result is None for failed operations."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=1,
            operand_b=0,
            result=None,
            success=False,
            error_message="Division by zero",
        )
        assert entry.result is None

    def test_memory_entry_float_result_on_success(self):
        """Test that result is float for successful operations."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3.5,
            operand_b=4.5,
            result=8.0,
            success=True,
            error_message=None,
        )
        assert entry.result == 8.0
        assert isinstance(entry.result, float)

    def test_memory_entry_execution_time_optional(self):
        """Test that execution_time_ms defaults to 0.0."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        assert entry.execution_time_ms == 0.0


class TestMemoryEntryFieldTypes:
    """Test that MemoryEntry field types are correct."""

    def test_memory_entry_operation_string(self):
        """Test that operation is string type."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        assert entry.operation == "add"
        assert isinstance(entry.operation, str)

    def test_memory_entry_operand_a_float(self):
        """Test that operand_a is float type."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3.5,
            operand_b=1,
            result=4.5,
            success=True,
            error_message=None,
        )
        assert entry.operand_a == 3.5
        assert isinstance(entry.operand_a, float)

    def test_memory_entry_operand_b_float(self):
        """Test that operand_b is float type."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2.7,
            result=3.7,
            success=True,
            error_message=None,
        )
        assert entry.operand_b == 2.7
        assert isinstance(entry.operand_b, float)

    def test_memory_entry_result_optional_float(self):
        """Test that result is Optional[float] (None or float)."""
        # Test with float
        entry1 = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=5.5,
            success=True,
            error_message=None,
        )
        assert entry1.result == 5.5
        assert isinstance(entry1.result, float)

        # Test with None
        entry2 = MemoryEntry(
            operation="sqrt",
            operand_a=-1,
            operand_b=0,
            result=None,
            success=False,
            error_message="Error",
        )
        assert entry2.result is None

    def test_memory_entry_success_boolean(self):
        """Test that success is boolean type."""
        # Test True
        entry1 = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        assert entry1.success is True
        assert isinstance(entry1.success, bool)

        # Test False
        entry2 = MemoryEntry(
            operation="divide",
            operand_a=1,
            operand_b=0,
            result=None,
            success=False,
            error_message="Error",
        )
        assert entry2.success is False
        assert isinstance(entry2.success, bool)

    def test_memory_entry_error_message_optional_string(self):
        """Test that error_message is Optional[str] (None or str)."""
        # Test with string
        entry1 = MemoryEntry(
            operation="sqrt",
            operand_a=-1,
            operand_b=0,
            result=None,
            success=False,
            error_message="msg",
        )
        assert entry1.error_message == "msg"
        assert isinstance(entry1.error_message, str)

        # Test with None
        entry2 = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        assert entry2.error_message is None

    def test_memory_entry_timestamp_string(self):
        """Test that timestamp is string type."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
            timestamp="2026-05-02T10:30:00",
        )
        assert entry.timestamp == "2026-05-02T10:30:00"
        assert isinstance(entry.timestamp, str)

    def test_memory_entry_entry_id_string(self):
        """Test that entry_id is string type."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
            entry_id="test-id",
        )
        assert entry.entry_id == "test-id"
        assert isinstance(entry.entry_id, str)

    def test_memory_entry_execution_time_float(self):
        """Test that execution_time_ms is float type."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
            execution_time_ms=2.5,
        )
        assert entry.execution_time_ms == 2.5
        assert isinstance(entry.execution_time_ms, float)
