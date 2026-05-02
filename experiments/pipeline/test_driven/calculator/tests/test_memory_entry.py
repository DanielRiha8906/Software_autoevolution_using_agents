import uuid
import pytest
from src.models.memory_entry import MemoryEntry


def test_memory_entry_can_be_created():
    entry = MemoryEntry(
        operation="add", operands=[1.0, 2.0], result=3.0,
        success=True, execution_time_ms=5.0,
    )
    assert entry is not None


def test_memory_entry_has_unique_id():
    a = MemoryEntry(operation="add", operands=[1, 2], result=3, success=True, execution_time_ms=1)
    b = MemoryEntry(operation="add", operands=[1, 2], result=3, success=True, execution_time_ms=1)
    assert a.id != b.id


def test_memory_entry_id_is_uuid_string():
    entry = MemoryEntry(operation="add", operands=[1, 2], result=3, success=True, execution_time_ms=1)
    parsed = uuid.UUID(entry.id)
    assert str(parsed) == entry.id


def test_memory_entry_has_timestamp():
    entry = MemoryEntry(operation="add", operands=[1, 2], result=3, success=True, execution_time_ms=1)
    assert entry.timestamp is not None


def test_memory_entry_supports_failed_calculation():
    entry = MemoryEntry(operation="sqrt", operands=[-1], result=None, success=False, execution_time_ms=0)
    assert entry.success is False
    assert entry.result is None


def test_memory_entry_serializes_to_dict():
    entry = MemoryEntry(operation="add", operands=[1, 2], result=3, success=True, execution_time_ms=5)
    d = entry.to_dict()
    assert isinstance(d, dict)
    assert d["operation"] == "add"
    assert d["success"] is True
    assert "id" in d
    assert "timestamp" in d
    assert "execution_time_ms" in d


def test_memory_entry_serializes_timestamp_as_string():
    entry = MemoryEntry(operation="add", operands=[1, 2], result=3, success=True, execution_time_ms=5)
    d = entry.to_dict()
    assert isinstance(d["timestamp"], str)


def test_memory_entry_round_trips_via_dict():
    entry = MemoryEntry(operation="add", operands=[1, 2], result=3, success=True, execution_time_ms=5)
    restored = MemoryEntry.from_dict(entry.to_dict())
    assert restored.operation == entry.operation
    assert restored.result == entry.result
    assert restored.id == entry.id
    assert restored.timestamp == entry.timestamp
    assert restored.execution_time_ms == entry.execution_time_ms


def test_memory_entry_contains_no_formatting_logic():
    import inspect
    from src.models import memory_entry as mod
    source = inspect.getsource(mod)
    assert "print(" not in source
