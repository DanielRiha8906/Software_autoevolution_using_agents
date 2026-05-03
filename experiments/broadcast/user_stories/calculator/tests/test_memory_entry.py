import pytest
from src.models.memory_entry import (
    MemoryEntry,
    ResultEntry,
    ErrorEntry,
    _reset_id_counter,
)


class TestResultEntry:
    def setup_method(self):
        _reset_id_counter()

    def test_create_result_entry(self):
        entry = ResultEntry(
            operation="add",
            operands=[3, 5],
            result=8,
        )
        assert entry.operation == "add"
        assert entry.operands == [3, 5]
        assert entry.result == 8
        assert entry.entry_id == 1
        assert entry.timestamp != ""
        assert entry.execution_time_ms == 0.0

    def test_result_entry_is_error_false(self):
        entry = ResultEntry(
            operation="multiply",
            operands=[2, 3],
            result=6,
        )
        assert entry.is_error() is False

    def test_result_entry_to_dict(self):
        entry = ResultEntry(
            operation="divide",
            operands=[10, 2],
            result=5.0,
            timestamp="2026-01-01T00:00:00",
            execution_time_ms=1.5,
        )
        data = entry.to_dict()
        assert data["type"] == "result"
        assert data["operation"] == "divide"
        assert data["operands"] == [10, 2]
        assert data["result"] == 5.0
        assert data["timestamp"] == "2026-01-01T00:00:00"
        assert data["execution_time_ms"] == 1.5
        assert "entry_id" in data

    def test_result_entry_from_dict(self):
        data = {
            "type": "result",
            "entry_id": 42,
            "operation": "subtract",
            "operands": [10, 3],
            "result": 7,
            "timestamp": "2026-01-01T12:00:00",
            "execution_time_ms": 0.5,
        }
        entry = ResultEntry.from_dict(data)
        assert entry.entry_id == 42
        assert entry.operation == "subtract"
        assert entry.operands == [10, 3]
        assert entry.result == 7
        assert entry.timestamp == "2026-01-01T12:00:00"
        assert entry.execution_time_ms == 0.5

    def test_result_entry_roundtrip(self):
        original = ResultEntry(
            operation="power",
            operands=[2, 8],
            result=256.0,
            timestamp="2026-02-01T10:30:00",
            execution_time_ms=2.0,
        )
        data = original.to_dict()
        restored = ResultEntry.from_dict(data)
        assert restored.operation == original.operation
        assert restored.operands == original.operands
        assert restored.result == original.result
        assert restored.timestamp == original.timestamp
        assert restored.execution_time_ms == original.execution_time_ms

    def test_result_entry_sequential_ids(self):
        entry1 = ResultEntry(operation="add", operands=[1, 1], result=2)
        entry2 = ResultEntry(operation="subtract", operands=[5, 2], result=3)
        entry3 = ResultEntry(operation="multiply", operands=[2, 2], result=4)
        assert entry1.entry_id == 1
        assert entry2.entry_id == 2
        assert entry3.entry_id == 3


class TestErrorEntry:
    def setup_method(self):
        _reset_id_counter()

    def test_create_error_entry(self):
        entry = ErrorEntry(
            operation="divide",
            operands=[5, 0],
            error_message="Division by zero is not allowed",
        )
        assert entry.operation == "divide"
        assert entry.operands == [5, 0]
        assert entry.error_message == "Division by zero is not allowed"
        assert entry.entry_id == 1
        assert entry.timestamp != ""
        assert entry.execution_time_ms == 0.0

    def test_error_entry_is_error_true(self):
        entry = ErrorEntry(
            operation="sqrt",
            operands=[-1, 0],
            error_message="Square root of a negative number is not allowed",
        )
        assert entry.is_error() is True

    def test_error_entry_to_dict(self):
        entry = ErrorEntry(
            operation="modulo",
            operands=[10, 0],
            error_message="Modulo by zero is not allowed",
            timestamp="2026-01-01T00:00:00",
            execution_time_ms=0.2,
        )
        data = entry.to_dict()
        assert data["type"] == "error"
        assert data["operation"] == "modulo"
        assert data["operands"] == [10, 0]
        assert data["error_message"] == "Modulo by zero is not allowed"
        assert data["timestamp"] == "2026-01-01T00:00:00"
        assert data["execution_time_ms"] == 0.2
        assert "entry_id" in data

    def test_error_entry_from_dict(self):
        data = {
            "type": "error",
            "entry_id": 99,
            "operation": "divide",
            "operands": [7, 0],
            "error_message": "Cannot divide by zero",
            "timestamp": "2026-01-02T15:30:00",
            "execution_time_ms": 0.3,
        }
        entry = ErrorEntry.from_dict(data)
        assert entry.entry_id == 99
        assert entry.operation == "divide"
        assert entry.operands == [7, 0]
        assert entry.error_message == "Cannot divide by zero"
        assert entry.timestamp == "2026-01-02T15:30:00"
        assert entry.execution_time_ms == 0.3

    def test_error_entry_roundtrip(self):
        original = ErrorEntry(
            operation="sqrt",
            operands=[-5, 0],
            error_message="Square root of negative not allowed",
            timestamp="2026-02-01T09:00:00",
            execution_time_ms=0.1,
        )
        data = original.to_dict()
        restored = ErrorEntry.from_dict(data)
        assert restored.operation == original.operation
        assert restored.operands == original.operands
        assert restored.error_message == original.error_message
        assert restored.timestamp == original.timestamp
        assert restored.execution_time_ms == original.execution_time_ms

    def test_error_entry_sequential_ids(self):
        _reset_id_counter()
        entry1 = ErrorEntry(operation="divide", operands=[1, 0], error_message="error1")
        entry2 = ErrorEntry(operation="sqrt", operands=[-1, 0], error_message="error2")
        assert entry1.entry_id == 1
        assert entry2.entry_id == 2


class TestMemoryEntryPolymorphism:
    def setup_method(self):
        _reset_id_counter()

    def test_from_dict_result_entry(self):
        data = {
            "type": "result",
            "entry_id": 1,
            "operation": "add",
            "operands": [1, 2],
            "result": 3,
            "timestamp": "2026-01-01T00:00:00",
            "execution_time_ms": 1.0,
        }
        entry = MemoryEntry.from_dict(data)
        assert isinstance(entry, ResultEntry)
        assert entry.result == 3

    def test_from_dict_error_entry(self):
        data = {
            "type": "error",
            "entry_id": 2,
            "operation": "divide",
            "operands": [5, 0],
            "error_message": "Division by zero",
            "timestamp": "2026-01-01T00:00:00",
            "execution_time_ms": 0.5,
        }
        entry = MemoryEntry.from_dict(data)
        assert isinstance(entry, ErrorEntry)
        assert entry.error_message == "Division by zero"

    def test_from_dict_invalid_type_raises(self):
        data = {
            "type": "unknown",
            "entry_id": 3,
            "operation": "add",
            "operands": [1, 2],
        }
        with pytest.raises(ValueError, match="Unknown entry type"):
            MemoryEntry.from_dict(data)

    def test_mixed_list_roundtrip(self):
        _reset_id_counter()
        entries_original = [
            ResultEntry(operation="add", operands=[1, 1], result=2),
            ErrorEntry(operation="divide", operands=[5, 0], error_message="divide by zero"),
            ResultEntry(operation="multiply", operands=[3, 4], result=12),
        ]
        data_list = [e.to_dict() for e in entries_original]
        restored_list = [MemoryEntry.from_dict(d) for d in data_list]

        assert len(restored_list) == 3
        assert isinstance(restored_list[0], ResultEntry)
        assert isinstance(restored_list[1], ErrorEntry)
        assert isinstance(restored_list[2], ResultEntry)
        assert restored_list[0].result == 2
        assert restored_list[1].error_message == "divide by zero"
        assert restored_list[2].result == 12


class TestMemoryEntryIdCounter:
    def test_id_counter_increments(self):
        _reset_id_counter()
        e1 = ResultEntry(operation="add", operands=[1, 1], result=2)
        e2 = ResultEntry(operation="sub", operands=[5, 3], result=2)
        e3 = ErrorEntry(operation="div", operands=[1, 0], error_message="error")
        assert e1.entry_id == 1
        assert e2.entry_id == 2
        assert e3.entry_id == 3

    def test_id_counter_reset(self):
        _reset_id_counter()
        e1 = ResultEntry(operation="add", operands=[1, 1], result=2)
        assert e1.entry_id == 1
        _reset_id_counter()
        e2 = ResultEntry(operation="add", operands=[1, 1], result=2)
        assert e2.entry_id == 1


class TestMemoryEntryDefaults:
    def setup_method(self):
        _reset_id_counter()

    def test_result_entry_default_result(self):
        entry = ResultEntry(operation="add", operands=[])
        assert entry.result == 0.0

    def test_error_entry_default_error_message(self):
        entry = ErrorEntry(operation="divide", operands=[])
        assert entry.error_message == ""

    def test_execution_time_defaults(self):
        result = ResultEntry(operation="add", operands=[1, 1], result=2)
        error = ErrorEntry(operation="divide", operands=[1, 0], error_message="error")
        assert result.execution_time_ms == 0.0
        assert error.execution_time_ms == 0.0

    def test_timestamp_auto_generated(self):
        entry = ResultEntry(operation="add", operands=[1, 1], result=2)
        assert entry.timestamp != ""
        assert "T" in entry.timestamp  # ISO format check

    def test_timestamp_explicit(self):
        ts = "2026-05-03T10:00:00"
        entry = ResultEntry(
            operation="add", operands=[1, 1], result=2, timestamp=ts
        )
        assert entry.timestamp == ts


class TestMemoryEntryFieldValidation:
    def setup_method(self):
        _reset_id_counter()

    def test_result_entry_with_float_result(self):
        entry = ResultEntry(
            operation="divide", operands=[10, 3], result=3.3333333
        )
        assert entry.result == 3.3333333

    def test_operands_list_flexibility(self):
        # One operand
        entry1 = ResultEntry(operation="square", operands=[5], result=25)
        assert entry1.operands == [5]
        # Two operands
        entry2 = ResultEntry(operation="add", operands=[3, 5], result=8)
        assert entry2.operands == [3, 5]
        # Multiple operands (even if not used by calculator)
        entry3 = ResultEntry(operation="custom", operands=[1, 2, 3], result=6)
        assert entry3.operands == [1, 2, 3]

    def test_error_message_preserves_details(self):
        msg = "Division by zero is not allowed"
        entry = ErrorEntry(
            operation="divide", operands=[5, 0], error_message=msg
        )
        assert entry.error_message == msg
