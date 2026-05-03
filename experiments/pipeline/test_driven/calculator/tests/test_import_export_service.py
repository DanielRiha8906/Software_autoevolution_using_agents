import json
import pytest
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.services.import_export_service import ImportExportService


def _entry(operation="add"):
    return MemoryEntry(operation=operation, operands=[1, 2], result=3,
                       success=True, execution_time_ms=1)


def test_export_creates_valid_json_file(tmp_path):
    memory = MemoryService()
    memory.store(_entry())
    svc = ImportExportService()
    path = tmp_path / "export.json"
    svc.export(memory, str(path))
    data = json.loads(path.read_text())
    assert isinstance(data, list)
    assert len(data) == 1


def test_import_loads_entries(tmp_path):
    entry = _entry()
    path = tmp_path / "data.json"
    path.write_text(json.dumps([entry.to_dict()]))
    memory = MemoryService()
    svc = ImportExportService()
    svc.import_from(memory, str(path))
    assert any(e.id == entry.id for e in memory.retrieve())


def test_import_validates_structure(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([{"garbage": True}]))
    memory = MemoryService()
    with pytest.raises(Exception):
        ImportExportService().import_from(memory, str(path))


def test_import_preserves_existing_entries(tmp_path):
    existing = _entry("add")
    memory = MemoryService()
    memory.store(existing)
    new_entry = _entry("multiply")
    path = tmp_path / "data.json"
    path.write_text(json.dumps([new_entry.to_dict()]))
    ImportExportService().import_from(memory, str(path))
    ids = [e.id for e in memory.retrieve()]
    assert existing.id in ids
    assert new_entry.id in ids


def test_import_skips_duplicate_entries(tmp_path):
    entry = _entry()
    memory = MemoryService()
    memory.store(entry)
    path = tmp_path / "data.json"
    path.write_text(json.dumps([entry.to_dict()]))
    ImportExportService().import_from(memory, str(path))
    assert len(memory.retrieve()) == 1
