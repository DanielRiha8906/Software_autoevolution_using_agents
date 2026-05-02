import pytest
from datetime import datetime
from src.models.memory_entry import MemoryEntry


class TestMemoryEntrySuccess:
    """Tests for successful calculation entries."""

    def test_create_successful_entry(self):
        """MemoryEntry can be created for a successful calculation."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            success=True,
        )
        assert entry.operation == "add"
        assert entry.operand_a == 3
        assert entry.operand_b == 5
        assert entry.result == 8
        assert entry.success is True
        assert entry.error_message is None

    def test_successful_entry_has_timestamp(self):
        """Successful entry gets a timestamp if not provided."""
        entry = MemoryEntry(
            operation="multiply",
            operand_a=2,
            operand_b=4,
            result=8,
        )
        assert entry.timestamp != ""
        # Verify it's a valid ISO format datetime
        datetime.fromisoformat(entry.timestamp)

    def test_successful_entry_custom_timestamp(self):
        """Successful entry can use a custom timestamp."""
        custom_ts = "2026-01-01T12:00:00"
        entry = MemoryEntry(
            operation="divide",
            operand_a=10,
            operand_b=2,
            result=5.0,
            timestamp=custom_ts,
        )
        assert entry.timestamp == custom_ts

    def test_successful_entry_execution_time(self):
        """Successful entry tracks execution time in milliseconds."""
        entry = MemoryEntry(
            operation="subtract",
            operand_a=10,
            operand_b=3,
            result=7,
            execution_time_ms=1.5,
        )
        assert entry.execution_time_ms == 1.5

    def test_successful_entry_default_execution_time(self):
        """Execution time defaults to 0.0 if not provided."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
        )
        assert entry.execution_time_ms == 0.0


class TestMemoryEntryError:
    """Tests for failed calculation entries."""

    def test_create_failed_entry(self):
        """MemoryEntry can be created for a failed calculation."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            result=None,
            success=False,
            error_message="Division by zero is not allowed",
        )
        assert entry.operation == "divide"
        assert entry.operand_a == 5
        assert entry.operand_b == 0
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message == "Division by zero is not allowed"

    def test_failed_entry_has_timestamp(self):
        """Failed entry gets a timestamp if not provided."""
        entry = MemoryEntry(
            operation="sqrt",
            operand_a=-1,
            operand_b=0,
            result=None,
            success=False,
            error_message="Cannot take square root of negative number",
        )
        assert entry.timestamp != ""
        datetime.fromisoformat(entry.timestamp)

    def test_failed_entry_execution_time(self):
        """Failed entry can track execution time before failure."""
        entry = MemoryEntry(
            operation="modulo",
            operand_a=5,
            operand_b=0,
            result=None,
            success=False,
            error_message="Modulo by zero is not allowed",
            execution_time_ms=0.8,
        )
        assert entry.execution_time_ms == 0.8


class TestMemoryEntryUniqueId:
    """Tests for unique identifier generation."""

    def test_each_entry_has_unique_id(self):
        """Each MemoryEntry gets a unique entry_id."""
        entry1 = MemoryEntry("add", 1, 2, 3)
        entry2 = MemoryEntry("subtract", 5, 2, 3)
        assert entry1.entry_id != entry2.entry_id

    def test_entry_id_is_string(self):
        """entry_id is a string (UUID)."""
        entry = MemoryEntry("add", 1, 2, 3)
        assert isinstance(entry.entry_id, str)
        # Verify it's a valid UUID format
        assert len(entry.entry_id) == 36  # Standard UUID string length
        assert entry.entry_id.count("-") == 4

    def test_custom_entry_id(self):
        """entry_id can be provided explicitly."""
        custom_id = "my-custom-id-12345"
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            entry_id=custom_id,
        )
        assert entry.entry_id == custom_id


class TestMemoryEntrySerialization:
    """Tests for JSON serialization and deserialization."""

    def test_to_dict_successful_entry(self):
        """to_dict() serializes a successful entry to a dictionary."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            success=True,
            timestamp="2026-01-01T12:00:00",
            execution_time_ms=0.5,
            entry_id="test-id-123",
        )
        data = entry.to_dict()
        assert data == {
            "operation": "add",
            "operand_a": 3,
            "operand_b": 5,
            "result": 8,
            "success": True,
            "error_message": None,
            "timestamp": "2026-01-01T12:00:00",
            "execution_time_ms": 0.5,
            "entry_id": "test-id-123",
        }

    def test_to_dict_failed_entry(self):
        """to_dict() serializes a failed entry to a dictionary."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            result=None,
            success=False,
            error_message="Division by zero",
            timestamp="2026-01-01T12:00:00",
            execution_time_ms=0.3,
            entry_id="test-id-456",
        )
        data = entry.to_dict()
        assert data == {
            "operation": "divide",
            "operand_a": 5,
            "operand_b": 0,
            "result": None,
            "success": False,
            "error_message": "Division by zero",
            "timestamp": "2026-01-01T12:00:00",
            "execution_time_ms": 0.3,
            "entry_id": "test-id-456",
        }

    def test_from_dict_successful_entry(self):
        """from_dict() deserializes a successful entry."""
        data = {
            "operation": "multiply",
            "operand_a": 3,
            "operand_b": 4,
            "result": 12,
            "success": True,
            "error_message": None,
            "timestamp": "2026-01-01T12:00:00",
            "execution_time_ms": 1.2,
            "entry_id": "test-id-789",
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.operation == "multiply"
        assert entry.operand_a == 3
        assert entry.operand_b == 4
        assert entry.result == 12
        assert entry.success is True
        assert entry.error_message is None
        assert entry.timestamp == "2026-01-01T12:00:00"
        assert entry.execution_time_ms == 1.2
        assert entry.entry_id == "test-id-789"

    def test_from_dict_failed_entry(self):
        """from_dict() deserializes a failed entry."""
        data = {
            "operation": "sqrt",
            "operand_a": -1,
            "operand_b": 0,
            "result": None,
            "success": False,
            "error_message": "Cannot take square root of negative number",
            "timestamp": "2026-01-01T12:00:00",
            "execution_time_ms": 0.5,
            "entry_id": "test-id-999",
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.operation == "sqrt"
        assert entry.operand_a == -1
        assert entry.operand_b == 0
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message == "Cannot take square root of negative number"
        assert entry.entry_id == "test-id-999"

    def test_roundtrip_serialization(self):
        """to_dict() and from_dict() roundtrip correctly."""
        original = MemoryEntry(
            operation="power",
            operand_a=2,
            operand_b=8,
            result=256,
            success=True,
            timestamp="2026-01-01T12:00:00",
            execution_time_ms=0.7,
            entry_id="roundtrip-id",
        )
        data = original.to_dict()
        restored = MemoryEntry.from_dict(data)
        assert restored == original

    def test_roundtrip_serialization_failed(self):
        """Roundtrip works for failed entries too."""
        original = MemoryEntry(
            operation="modulo",
            operand_a=5,
            operand_b=0,
            result=None,
            success=False,
            error_message="Modulo by zero is not allowed",
            timestamp="2026-01-01T12:00:00",
            execution_time_ms=0.2,
            entry_id="failed-roundtrip",
        )
        data = original.to_dict()
        restored = MemoryEntry.from_dict(data)
        assert restored == original


class TestMemoryEntryDefaults:
    """Tests for default values and field behavior."""

    def test_defaults_for_successful_entry(self):
        """Successful entry has sensible defaults."""
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
        )
        assert entry.success is True
        assert entry.error_message is None
        assert entry.execution_time_ms == 0.0
        assert entry.timestamp != ""
        assert entry.entry_id != ""

    def test_defaults_for_failed_entry(self):
        """Failed entry can omit result and error_message defaults."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            success=False,
        )
        assert entry.result is None
        assert entry.error_message is None
        assert entry.success is False

    def test_various_operation_names(self):
        """MemoryEntry accepts any operation name."""
        operations = ["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"]
        for op in operations:
            entry = MemoryEntry(op, 1, 2, 3)
            assert entry.operation == op
