import pytest
import uuid
from datetime import datetime
from src.models.memory_entry import MemoryEntry


def test_memory_entry_has_required_fields():
    entry = MemoryEntry(
        operation="add",
        operands=[1.0, 2.0],
        result=3.0,
        success=True,
        execution_time_ms=10.5
    )
    assert hasattr(entry, "operation")
    assert hasattr(entry, "operands")
    assert hasattr(entry, "result")
    assert hasattr(entry, "success")
    assert hasattr(entry, "execution_time_ms")
    assert hasattr(entry, "id")
    assert hasattr(entry, "timestamp")


def test_memory_entry_auto_generates_uuid_id():
    entry = MemoryEntry(
        operation="add",
        operands=[1.0, 2.0],
        result=3.0,
        success=True,
        execution_time_ms=10.5
    )
    assert entry.id is not None
    assert isinstance(entry.id, str)
    try:
        uuid.UUID(entry.id)
    except ValueError:
        pytest.fail("id is not a valid UUID string")


def test_memory_entry_auto_generates_unique_uuids():
    entry1 = MemoryEntry(
        operation="add",
        operands=[1.0, 2.0],
        result=3.0,
        success=True,
        execution_time_ms=10.5
    )
    entry2 = MemoryEntry(
        operation="add",
        operands=[1.0, 2.0],
        result=3.0,
        success=True,
        execution_time_ms=10.5
    )
    assert entry1.id != entry2.id


def test_memory_entry_auto_generates_timestamp():
    before = datetime.now().isoformat()
    entry = MemoryEntry(
        operation="add",
        operands=[1.0, 2.0],
        result=3.0,
        success=True,
        execution_time_ms=10.5
    )
    after = datetime.now().isoformat()
    assert entry.timestamp is not None
    assert isinstance(entry.timestamp, str)
    assert before <= entry.timestamp <= after


def test_memory_entry_supports_failed_calculations():
    entry = MemoryEntry(
        operation="divide",
        operands=[10.0, 0.0],
        result=None,
        success=False,
        execution_time_ms=5.2
    )
    assert entry.result is None
    assert entry.success is False
    assert entry.operation == "divide"
    assert entry.operands == [10.0, 0.0]


def test_memory_entry_supports_successful_calculations():
    entry = MemoryEntry(
        operation="multiply",
        operands=[3.0, 4.0],
        result=12.0,
        success=True,
        execution_time_ms=3.1
    )
    assert entry.result == 12.0
    assert entry.success is True


def test_memory_entry_to_dict_serialization():
    entry = MemoryEntry(
        operation="subtract",
        operands=[10.0, 3.0],
        result=7.0,
        success=True,
        execution_time_ms=2.5
    )
    d = entry.to_dict()
    assert isinstance(d, dict)
    assert d["operation"] == "subtract"
    assert d["operands"] == [10.0, 3.0]
    assert d["result"] == 7.0
    assert d["success"] is True
    assert d["execution_time_ms"] == 2.5
    assert "id" in d
    assert "timestamp" in d


def test_memory_entry_from_dict_deserialization():
    data = {
        "operation": "add",
        "operands": [5.0, 6.0],
        "result": 11.0,
        "success": True,
        "execution_time_ms": 4.2,
        "id": str(uuid.uuid4()),
        "timestamp": "2024-01-01T12:00:00"
    }
    entry = MemoryEntry.from_dict(data)
    assert entry.operation == "add"
    assert entry.operands == [5.0, 6.0]
    assert entry.result == 11.0
    assert entry.success is True
    assert entry.execution_time_ms == 4.2
    assert entry.id == data["id"]
    assert entry.timestamp == "2024-01-01T12:00:00"


def test_memory_entry_round_trip_serialization():
    original = MemoryEntry(
        operation="divide",
        operands=[20.0, 4.0],
        result=5.0,
        success=True,
        execution_time_ms=7.8
    )
    serialized = original.to_dict()
    restored = MemoryEntry.from_dict(serialized)
    assert restored.operation == original.operation
    assert restored.operands == original.operands
    assert restored.result == original.result
    assert restored.success == original.success
    assert restored.execution_time_ms == original.execution_time_ms
    assert restored.id == original.id
    assert restored.timestamp == original.timestamp


def test_memory_entry_failed_calculation_serialization():
    entry = MemoryEntry(
        operation="sqrt",
        operands=[-1.0],
        result=None,
        success=False,
        execution_time_ms=1.5
    )
    d = entry.to_dict()
    assert d["result"] is None
    assert d["success"] is False
    restored = MemoryEntry.from_dict(d)
    assert restored.result is None
    assert restored.success is False


def test_memory_entry_preserves_custom_id():
    custom_id = str(uuid.uuid4())
    data = {
        "operation": "add",
        "operands": [1.0, 2.0],
        "result": 3.0,
        "success": True,
        "execution_time_ms": 10.0,
        "id": custom_id,
        "timestamp": "2024-01-01T12:00:00"
    }
    entry = MemoryEntry.from_dict(data)
    assert entry.id == custom_id


def test_memory_entry_preserves_custom_timestamp():
    custom_timestamp = "2024-01-01T12:30:45.123456"
    data = {
        "operation": "multiply",
        "operands": [2.0, 3.0],
        "result": 6.0,
        "success": True,
        "execution_time_ms": 5.0,
        "id": str(uuid.uuid4()),
        "timestamp": custom_timestamp
    }
    entry = MemoryEntry.from_dict(data)
    assert entry.timestamp == custom_timestamp


def test_memory_entry_with_multiple_operands():
    entry = MemoryEntry(
        operation="power",
        operands=[2.0, 8.0],
        result=256.0,
        success=True,
        execution_time_ms=3.7
    )
    assert len(entry.operands) == 2
    assert entry.operands[0] == 2.0
    assert entry.operands[1] == 8.0


def test_memory_entry_with_single_operand():
    entry = MemoryEntry(
        operation="square",
        operands=[5.0],
        result=25.0,
        success=True,
        execution_time_ms=2.1
    )
    assert len(entry.operands) == 1
    assert entry.operands[0] == 5.0
