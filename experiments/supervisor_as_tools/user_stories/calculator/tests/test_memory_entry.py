import pytest
import json
from datetime import datetime
from src.models.memory_entry import MemoryEntry


class TestMemoryEntry:
    def test_basic_instantiation_successful(self):
        """Test creating a successful MemoryEntry."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            error_message=None,
            execution_time_ms=0.5
        )
        assert entry.operation == "add"
        assert entry.operand_a == 3.0
        assert entry.operand_b == 5.0
        assert entry.result == 8.0
        assert entry.success is True
        assert entry.error_message is None
        assert entry.execution_time_ms == 0.5

    def test_basic_instantiation_failed(self):
        """Test creating a failed MemoryEntry."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero",
            execution_time_ms=0.1
        )
        assert entry.operation == "divide"
        assert entry.operand_a == 5.0
        assert entry.operand_b == 0.0
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message == "Division by zero"
        assert entry.execution_time_ms == 0.1

    def test_execution_time_tracking(self):
        """Test that execution time is properly tracked."""
        entry = MemoryEntry(
            operation="multiply",
            operand_a=2.5,
            operand_b=4.0,
            result=10.0,
            success=True,
            error_message=None,
            execution_time_ms=1.23
        )
        assert entry.execution_time_ms == 1.23

    def test_timestamp_auto_generation(self):
        """Test that timestamp is auto-generated if not provided."""
        before = datetime.now().isoformat()
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_time_ms=0.1
        )
        after = datetime.now().isoformat()
        assert before <= entry.timestamp <= after
        assert "T" in entry.timestamp  # ISO format check

    def test_timestamp_provided(self):
        """Test that provided timestamp is not overwritten."""
        custom_time = "2026-05-02T10:30:45.123456"
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_time_ms=0.1,
            timestamp=custom_time
        )
        assert entry.timestamp == custom_time

    def test_unique_entry_ids(self):
        """Test that each entry gets a unique UUID."""
        entry1 = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_time_ms=0.1
        )
        entry2 = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_time_ms=0.1
        )
        assert entry1.entry_id != entry2.entry_id
        assert len(entry1.entry_id) == 36  # UUID4 string format

    def test_serialize_to_dict_successful(self):
        """Test serializing a successful entry to dict."""
        entry = MemoryEntry(
            operation="subtract",
            operand_a=10.0,
            operand_b=4.0,
            result=6.0,
            success=True,
            error_message=None,
            execution_time_ms=0.2,
            timestamp="2026-05-02T10:00:00"
        )
        result_dict = entry.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["operation"] == "subtract"
        assert result_dict["operand_a"] == 10.0
        assert result_dict["operand_b"] == 4.0
        assert result_dict["result"] == 6.0
        assert result_dict["success"] is True
        assert result_dict["error_message"] is None
        assert result_dict["execution_time_ms"] == 0.2
        assert "entry_id" in result_dict
        assert result_dict["timestamp"] == "2026-05-02T10:00:00"

    def test_serialize_to_dict_failed(self):
        """Test serializing a failed entry to dict."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Cannot divide by zero",
            execution_time_ms=0.15,
            timestamp="2026-05-02T11:00:00"
        )
        result_dict = entry.to_dict()
        assert result_dict["result"] is None
        assert result_dict["success"] is False
        assert result_dict["error_message"] == "Cannot divide by zero"

    def test_deserialize_from_dict_successful(self):
        """Test deserializing a successful entry from dict."""
        data = {
            "operation": "add",
            "operand_a": 3.0,
            "operand_b": 5.0,
            "result": 8.0,
            "success": True,
            "error_message": None,
            "execution_time_ms": 0.5,
            "entry_id": "550e8400-e29b-41d4-a716-446655440000",
            "timestamp": "2026-05-02T12:00:00"
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.operation == "add"
        assert entry.operand_a == 3.0
        assert entry.operand_b == 5.0
        assert entry.result == 8.0
        assert entry.success is True
        assert entry.error_message is None
        assert entry.execution_time_ms == 0.5
        assert entry.entry_id == "550e8400-e29b-41d4-a716-446655440000"
        assert entry.timestamp == "2026-05-02T12:00:00"

    def test_deserialize_from_dict_failed(self):
        """Test deserializing a failed entry from dict."""
        data = {
            "operation": "divide",
            "operand_a": 5.0,
            "operand_b": 0.0,
            "result": None,
            "success": False,
            "error_message": "Division by zero",
            "execution_time_ms": 0.1,
            "entry_id": "550e8400-e29b-41d4-a716-446655440001",
            "timestamp": "2026-05-02T13:00:00"
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.operation == "divide"
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message == "Division by zero"

    def test_round_trip_serialization_successful(self):
        """Test round-trip serialization for successful entry."""
        original = MemoryEntry(
            operation="multiply",
            operand_a=2.5,
            operand_b=4.0,
            result=10.0,
            success=True,
            error_message=None,
            execution_time_ms=0.8,
            timestamp="2026-05-02T14:00:00"
        )
        data = original.to_dict()
        restored = MemoryEntry.from_dict(data)

        assert restored.operation == original.operation
        assert restored.operand_a == original.operand_a
        assert restored.operand_b == original.operand_b
        assert restored.result == original.result
        assert restored.success == original.success
        assert restored.error_message == original.error_message
        assert restored.execution_time_ms == original.execution_time_ms
        assert restored.entry_id == original.entry_id
        assert restored.timestamp == original.timestamp

    def test_round_trip_serialization_failed(self):
        """Test round-trip serialization for failed entry."""
        original = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero error",
            execution_time_ms=0.05,
            timestamp="2026-05-02T15:00:00"
        )
        data = original.to_dict()
        restored = MemoryEntry.from_dict(data)

        assert restored.operation == original.operation
        assert restored.result is None
        assert restored.success == original.success
        assert restored.error_message == original.error_message
        assert restored.entry_id == original.entry_id

    def test_no_str_method(self):
        """Test that __str__ method is not defined."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_time_ms=0.1
        )
        # The default __str__ should be from the dataclass, not a custom one
        str_repr = str(entry)
        assert "MemoryEntry" in str_repr  # Should contain class name from default repr

    def test_json_serialization_compatibility(self):
        """Test that to_dict() produces JSON-compatible output."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            error_message=None,
            execution_time_ms=0.5,
            timestamp="2026-05-02T16:00:00"
        )
        data = entry.to_dict()
        # This should not raise an exception
        json_str = json.dumps(data)
        assert isinstance(json_str, str)
        # Verify we can parse it back
        parsed = json.loads(json_str)
        assert parsed["operation"] == "add"
        assert parsed["result"] == 8.0

    def test_field_type_verification(self):
        """Test that field types are correctly defined."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            error_message=None,
            execution_time_ms=0.5
        )
        # Verify types
        assert isinstance(entry.operation, str)
        assert isinstance(entry.operand_a, float)
        assert isinstance(entry.operand_b, float)
        assert isinstance(entry.result, (float, type(None)))
        assert isinstance(entry.success, bool)
        assert isinstance(entry.error_message, (str, type(None)))
        assert isinstance(entry.execution_time_ms, (float, int))
        assert isinstance(entry.entry_id, str)
        assert isinstance(entry.timestamp, str)
