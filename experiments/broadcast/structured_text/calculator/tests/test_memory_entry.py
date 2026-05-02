import pytest
from datetime import datetime
from src.models.memory_entry import MemoryEntry


class TestMemoryEntry:
    def test_successful_calculation_entry(self):
        """Test creating a MemoryEntry for a successful calculation."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3.0,
            operand_b=5.0,
            result=8.0,
            success=True,
            execution_time_ms=1.5
        )
        assert entry.operation == "add"
        assert entry.operand_a == 3.0
        assert entry.operand_b == 5.0
        assert entry.result == 8.0
        assert entry.success is True
        assert entry.error_message is None
        assert entry.execution_time_ms == 1.5

    def test_failed_calculation_entry(self):
        """Test creating a MemoryEntry for a failed calculation."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero",
            execution_time_ms=0.5
        )
        assert entry.operation == "divide"
        assert entry.operand_a == 10.0
        assert entry.operand_b == 0.0
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message == "Division by zero"
        assert entry.execution_time_ms == 0.5

    def test_default_execution_time_ms(self):
        """Test that execution_time_ms defaults to 0.0."""
        entry = MemoryEntry(
            operation="multiply",
            operand_a=2.0,
            operand_b=3.0,
            result=6.0
        )
        assert entry.execution_time_ms == 0.0

    def test_default_success_state(self):
        """Test that success defaults to True."""
        entry = MemoryEntry(
            operation="subtract",
            operand_a=10.0,
            operand_b=3.0,
            result=7.0
        )
        assert entry.success is True

    def test_timestamp_auto_generation(self):
        """Test that timestamp is auto-generated if not provided."""
        before = datetime.now().isoformat()
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0
        )
        after = datetime.now().isoformat()

        assert entry.timestamp != ""
        # Timestamp should be between before and after (approximately)
        assert before <= entry.timestamp <= after

    def test_timestamp_preserved(self):
        """Test that provided timestamp is preserved."""
        fixed_timestamp = "2026-05-02T10:30:00.000000"
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            timestamp=fixed_timestamp
        )
        assert entry.timestamp == fixed_timestamp

    def test_entry_id_auto_generation(self):
        """Test that entry_id is auto-generated with UUID."""
        entry1 = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0
        )
        entry2 = MemoryEntry(
            operation="subtract",
            operand_a=10.0,
            operand_b=5.0,
            result=5.0
        )
        # Each entry should have a unique ID
        assert entry1.entry_id != entry2.entry_id
        # IDs should be non-empty strings
        assert isinstance(entry1.entry_id, str)
        assert len(entry1.entry_id) > 0

    def test_entry_id_preserved(self):
        """Test that provided entry_id is preserved."""
        custom_id = "custom-entry-123"
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            entry_id=custom_id
        )
        assert entry.entry_id == custom_id

    def test_to_dict_successful_entry(self):
        """Test serialization of successful MemoryEntry to dict."""
        entry = MemoryEntry(
            operation="multiply",
            operand_a=4.0,
            operand_b=5.0,
            result=20.0,
            success=True,
            execution_time_ms=2.0,
            timestamp="2026-05-02T12:00:00",
            entry_id="test-id-123"
        )
        data = entry.to_dict()

        assert data["operation"] == "multiply"
        assert data["operand_a"] == 4.0
        assert data["operand_b"] == 5.0
        assert data["result"] == 20.0
        assert data["success"] is True
        assert data["error_message"] is None
        assert data["execution_time_ms"] == 2.0
        assert data["timestamp"] == "2026-05-02T12:00:00"
        assert data["entry_id"] == "test-id-123"

    def test_to_dict_failed_entry(self):
        """Test serialization of failed MemoryEntry to dict."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Cannot divide by zero",
            execution_time_ms=0.3,
            timestamp="2026-05-02T12:00:00",
            entry_id="error-id-456"
        )
        data = entry.to_dict()

        assert data["operation"] == "divide"
        assert data["operand_a"] == 10.0
        assert data["operand_b"] == 0.0
        assert data["result"] is None
        assert data["success"] is False
        assert data["error_message"] == "Cannot divide by zero"
        assert data["execution_time_ms"] == 0.3
        assert data["timestamp"] == "2026-05-02T12:00:00"
        assert data["entry_id"] == "error-id-456"

    def test_from_dict_successful_entry(self):
        """Test deserialization of successful MemoryEntry from dict."""
        data = {
            "operation": "add",
            "operand_a": 5.0,
            "operand_b": 3.0,
            "result": 8.0,
            "success": True,
            "error_message": None,
            "execution_time_ms": 1.5,
            "timestamp": "2026-05-02T12:00:00",
            "entry_id": "test-id-789"
        }
        entry = MemoryEntry.from_dict(data)

        assert entry.operation == "add"
        assert entry.operand_a == 5.0
        assert entry.operand_b == 3.0
        assert entry.result == 8.0
        assert entry.success is True
        assert entry.error_message is None
        assert entry.execution_time_ms == 1.5
        assert entry.timestamp == "2026-05-02T12:00:00"
        assert entry.entry_id == "test-id-789"

    def test_from_dict_failed_entry(self):
        """Test deserialization of failed MemoryEntry from dict."""
        data = {
            "operation": "sqrt",
            "operand_a": -5.0,
            "operand_b": 0.0,
            "result": None,
            "success": False,
            "error_message": "Cannot compute square root of negative number",
            "execution_time_ms": 0.2,
            "timestamp": "2026-05-02T12:00:00",
            "entry_id": "error-id-999"
        }
        entry = MemoryEntry.from_dict(data)

        assert entry.operation == "sqrt"
        assert entry.operand_a == -5.0
        assert entry.operand_b == 0.0
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message == "Cannot compute square root of negative number"
        assert entry.execution_time_ms == 0.2
        assert entry.timestamp == "2026-05-02T12:00:00"
        assert entry.entry_id == "error-id-999"

    def test_round_trip_serialization_successful(self):
        """Test that to_dict and from_dict are inverse operations for successful entry."""
        original = MemoryEntry(
            operation="power",
            operand_a=2.0,
            operand_b=3.0,
            result=8.0,
            success=True,
            execution_time_ms=0.8,
            timestamp="2026-05-02T12:00:00",
            entry_id="roundtrip-1"
        )
        data = original.to_dict()
        reconstructed = MemoryEntry.from_dict(data)

        assert reconstructed.operation == original.operation
        assert reconstructed.operand_a == original.operand_a
        assert reconstructed.operand_b == original.operand_b
        assert reconstructed.result == original.result
        assert reconstructed.success == original.success
        assert reconstructed.error_message == original.error_message
        assert reconstructed.execution_time_ms == original.execution_time_ms
        assert reconstructed.timestamp == original.timestamp
        assert reconstructed.entry_id == original.entry_id

    def test_round_trip_serialization_failed(self):
        """Test that to_dict and from_dict are inverse operations for failed entry."""
        original = MemoryEntry(
            operation="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero",
            execution_time_ms=0.5,
            timestamp="2026-05-02T12:00:00",
            entry_id="roundtrip-2"
        )
        data = original.to_dict()
        reconstructed = MemoryEntry.from_dict(data)

        assert reconstructed.operation == original.operation
        assert reconstructed.operand_a == original.operand_a
        assert reconstructed.operand_b == original.operand_b
        assert reconstructed.result == original.result
        assert reconstructed.success == original.success
        assert reconstructed.error_message == original.error_message
        assert reconstructed.execution_time_ms == original.execution_time_ms
        assert reconstructed.timestamp == original.timestamp
        assert reconstructed.entry_id == original.entry_id

    def test_from_dict_minimal_data(self):
        """Test from_dict with only required fields."""
        data = {
            "operation": "add",
            "operand_a": 1.0,
            "operand_b": 2.0
        }
        entry = MemoryEntry.from_dict(data)

        assert entry.operation == "add"
        assert entry.operand_a == 1.0
        assert entry.operand_b == 2.0
        assert entry.result is None
        assert entry.success is True
        assert entry.error_message is None
        assert entry.execution_time_ms == 0.0
