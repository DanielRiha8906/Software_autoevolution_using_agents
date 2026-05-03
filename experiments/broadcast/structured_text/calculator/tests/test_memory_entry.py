import pytest
from datetime import datetime
from src.models.memory_entry import MemoryEntry


class TestMemoryEntry:
    """Test suite for MemoryEntry domain class."""

    def test_successful_calculation_entry(self):
        """Test creating a MemoryEntry for a successful calculation."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=5.0,
            operand_b=3.0,
            result=8.0,
            success=True,
        )
        assert entry.operation_name == "add"
        assert entry.operand_a == 5.0
        assert entry.operand_b == 3.0
        assert entry.result == 8.0
        assert entry.success is True
        assert entry.error_message is None

    def test_failed_calculation_entry(self):
        """Test creating a MemoryEntry for a failed calculation."""
        entry = MemoryEntry(
            operation_name="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero",
        )
        assert entry.operation_name == "divide"
        assert entry.operand_a == 5.0
        assert entry.operand_b == 0.0
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message == "Division by zero"

    def test_execution_timestamp_auto_set(self):
        """Test that execution_timestamp is auto-set if not provided."""
        before = datetime.now().isoformat()
        entry = MemoryEntry(
            operation_name="multiply",
            operand_a=2.0,
            operand_b=3.0,
            result=6.0,
        )
        after = datetime.now().isoformat()

        assert entry.execution_timestamp is not None
        assert entry.execution_timestamp >= before
        assert entry.execution_timestamp <= after

    def test_execution_timestamp_explicit(self):
        """Test that provided execution_timestamp is preserved."""
        timestamp = "2026-05-03T12:30:45.123456"
        entry = MemoryEntry(
            operation_name="subtract",
            operand_a=10.0,
            operand_b=3.0,
            result=7.0,
            execution_timestamp=timestamp,
        )
        assert entry.execution_timestamp == timestamp

    def test_execution_time_ms_default(self):
        """Test that execution_time_ms defaults to 0.0."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
        )
        assert entry.execution_time_ms == 0.0

    def test_execution_time_ms_explicit(self):
        """Test that provided execution_time_ms is preserved."""
        entry = MemoryEntry(
            operation_name="square",
            operand_a=5.0,
            operand_b=0.0,
            result=25.0,
            execution_time_ms=1.5,
        )
        assert entry.execution_time_ms == 1.5

    def test_to_dict_successful_entry(self):
        """Test to_dict() for a successful calculation entry."""
        timestamp = "2026-05-03T12:30:45"
        entry = MemoryEntry(
            operation_name="add",
            operand_a=5.0,
            operand_b=3.0,
            result=8.0,
            success=True,
            error_message=None,
            execution_timestamp=timestamp,
            execution_time_ms=2.5,
        )

        result_dict = entry.to_dict()

        assert result_dict["operation_name"] == "add"
        assert result_dict["operand_a"] == 5.0
        assert result_dict["operand_b"] == 3.0
        assert result_dict["result"] == 8.0
        assert result_dict["success"] is True
        assert result_dict["error_message"] is None
        assert result_dict["execution_timestamp"] == timestamp
        assert result_dict["execution_time_ms"] == 2.5

    def test_to_dict_failed_entry(self):
        """Test to_dict() for a failed calculation entry."""
        timestamp = "2026-05-03T12:30:45"
        entry = MemoryEntry(
            operation_name="sqrt",
            operand_a=-4.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Square root of a negative number",
            execution_timestamp=timestamp,
            execution_time_ms=0.8,
        )

        result_dict = entry.to_dict()

        assert result_dict["operation_name"] == "sqrt"
        assert result_dict["operand_a"] == -4.0
        assert result_dict["operand_b"] == 0.0
        assert result_dict["result"] is None
        assert result_dict["success"] is False
        assert result_dict["error_message"] == "Square root of a negative number"
        assert result_dict["execution_timestamp"] == timestamp
        assert result_dict["execution_time_ms"] == 0.8

    def test_from_dict_successful_entry(self):
        """Test from_dict() for a successful calculation entry."""
        data = {
            "operation_name": "multiply",
            "operand_a": 4.0,
            "operand_b": 5.0,
            "result": 20.0,
            "success": True,
            "error_message": None,
            "execution_timestamp": "2026-05-03T12:30:45",
            "execution_time_ms": 1.2,
        }

        entry = MemoryEntry.from_dict(data)

        assert entry.operation_name == "multiply"
        assert entry.operand_a == 4.0
        assert entry.operand_b == 5.0
        assert entry.result == 20.0
        assert entry.success is True
        assert entry.error_message is None
        assert entry.execution_timestamp == "2026-05-03T12:30:45"
        assert entry.execution_time_ms == 1.2

    def test_from_dict_failed_entry(self):
        """Test from_dict() for a failed calculation entry."""
        data = {
            "operation_name": "divide",
            "operand_a": 10.0,
            "operand_b": 0.0,
            "result": None,
            "success": False,
            "error_message": "Division by zero",
            "execution_timestamp": "2026-05-03T12:30:45",
            "execution_time_ms": 0.5,
        }

        entry = MemoryEntry.from_dict(data)

        assert entry.operation_name == "divide"
        assert entry.operand_a == 10.0
        assert entry.operand_b == 0.0
        assert entry.result is None
        assert entry.success is False
        assert entry.error_message == "Division by zero"
        assert entry.execution_timestamp == "2026-05-03T12:30:45"
        assert entry.execution_time_ms == 0.5

    def test_serialization_roundtrip_successful(self):
        """Test that serialization and deserialization preserves successful entry."""
        timestamp = "2026-05-03T12:30:45.123456"
        original = MemoryEntry(
            operation_name="power",
            operand_a=2.0,
            operand_b=8.0,
            result=256.0,
            success=True,
            error_message=None,
            execution_timestamp=timestamp,
            execution_time_ms=3.7,
        )

        # Serialize and deserialize
        serialized = original.to_dict()
        restored = MemoryEntry.from_dict(serialized)

        assert restored.operation_name == original.operation_name
        assert restored.operand_a == original.operand_a
        assert restored.operand_b == original.operand_b
        assert restored.result == original.result
        assert restored.success == original.success
        assert restored.error_message == original.error_message
        assert restored.execution_timestamp == original.execution_timestamp
        assert restored.execution_time_ms == original.execution_time_ms

    def test_serialization_roundtrip_failed(self):
        """Test that serialization and deserialization preserves failed entry."""
        timestamp = "2026-05-03T12:30:45.123456"
        original = MemoryEntry(
            operation_name="modulo",
            operand_a=10.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Modulo by zero",
            execution_timestamp=timestamp,
            execution_time_ms=0.3,
        )

        # Serialize and deserialize
        serialized = original.to_dict()
        restored = MemoryEntry.from_dict(serialized)

        assert restored.operation_name == original.operation_name
        assert restored.operand_a == original.operand_a
        assert restored.operand_b == original.operand_b
        assert restored.result == original.result
        assert restored.success == original.success
        assert restored.error_message == original.error_message
        assert restored.execution_timestamp == original.execution_timestamp
        assert restored.execution_time_ms == original.execution_time_ms

    def test_float_operands_with_integers(self):
        """Test that integer operands are handled as floats."""
        entry = MemoryEntry(
            operation_name="add",
            operand_a=5,
            operand_b=3,
            result=8,
        )
        # Verify they are stored as provided (floats)
        assert isinstance(entry.operand_a, (int, float))
        assert isinstance(entry.operand_b, (int, float))
        assert isinstance(entry.result, (int, float))

    def test_various_operation_names(self):
        """Test creating entries for various operation types."""
        operations = ["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"]

        for op_name in operations:
            entry = MemoryEntry(
                operation_name=op_name,
                operand_a=5.0,
                operand_b=3.0,
                result=8.0,
            )
            assert entry.operation_name == op_name

    def test_complex_result_value(self):
        """Test that complex numbers can be stored as result."""
        entry = MemoryEntry(
            operation_name="power",
            operand_a=-4.0,
            operand_b=0.5,
            result=None,  # Complex result or could be stored as tuple/string representation
            success=False,
            error_message="Complex result not supported",
        )
        assert entry.result is None
        assert entry.success is False
