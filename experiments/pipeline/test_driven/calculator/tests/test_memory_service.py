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


def _entry(operation="add", success=True):
    return MemoryEntry(
        operation=operation,
        operands=[1, 2],
        result=3,
        success=success,
        execution_time_ms=1,
    )


@pytest.fixture
def populated_service():
    service = MemoryService()
    service.store(_entry("add", success=True))
    service.store(_entry("multiply", success=True))
    service.store(_entry("divide", success=False))
    return service


def test_filter_by_operation(populated_service):
    results = populated_service.query(operation="add")
    assert len(results) > 0
    assert all(e.operation == "add" for e in results)


def test_filter_by_success_state(populated_service):
    results = populated_service.query(success=True)
    assert all(e.success is True for e in results)


def test_filter_by_error_state(populated_service):
    results = populated_service.query(success=False)
    assert all(e.success is False for e in results)


def test_combined_filters(populated_service):
    results = populated_service.query(operation="add", success=True)
    assert all(e.operation == "add" and e.success for e in results)


def test_query_returns_list(populated_service):
    assert isinstance(populated_service.query(), list)


def test_query_no_match_returns_empty_list(populated_service):
    assert populated_service.query(operation="nonexistent") == []
