import pytest
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService


def _make_entry(**kwargs):
    defaults = dict(operation="add", operands=[1, 2], result=3, success=True, execution_time_ms=1)
    defaults.update(kwargs)
    return MemoryEntry(**defaults)


def test_memory_service_can_store_entry():
    service = MemoryService()
    service.store(_make_entry())


def test_memory_service_retrieve_returns_stored_entries():
    service = MemoryService()
    entry = _make_entry()
    service.store(entry)
    assert any(e.id == entry.id for e in service.retrieve())


def test_memory_service_stores_multiple_entries():
    service = MemoryService()
    for i in range(3):
        service.store(_make_entry(result=float(i)))
    assert len(service.retrieve()) == 3


def test_memory_service_retrieve_returns_list():
    service = MemoryService()
    assert isinstance(service.retrieve(), list)


def test_memory_service_does_not_contain_file_io():
    import inspect
    from src.services import memory_service as mod
    source = inspect.getsource(mod)
    assert "open(" not in source
    assert "json.dump" not in source
