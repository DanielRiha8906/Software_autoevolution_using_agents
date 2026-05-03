import json
import pytest
from pathlib import Path

from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.services.import_export_service import ImportExportService


def _entry(**kwargs):
    """Helper to create MemoryEntry with sensible defaults."""
    defaults = dict(operation="add", operands=[1, 2], result=3, success=True, execution_time_ms=1.0)
    defaults.update(kwargs)
    return MemoryEntry(**defaults)


def test_export_writes_json_file(tmp_path):
    """Test that export() writes a valid JSON file with all entries."""
    service = ImportExportService()
    memory = MemoryService()

    memory.store(_entry(operation="add", operands=[1, 2], result=3))
    memory.store(_entry(operation="multiply", operands=[2, 3], result=6))

    filepath = tmp_path / "export.json"
    count = service.export(memory, filepath)

    assert count == 2
    assert filepath.exists()

    # Verify JSON content
    data = json.loads(filepath.read_text())
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["operation"] == "add"
    assert data[1]["operation"] == "multiply"


def test_export_creates_parent_directories(tmp_path):
    """Test that export() creates parent directories if needed."""
    service = ImportExportService()
    memory = MemoryService()
    memory.store(_entry())

    deep_path = tmp_path / "a" / "b" / "c" / "export.json"
    service.export(memory, deep_path)

    assert deep_path.exists()
    data = json.loads(deep_path.read_text())
    assert len(data) == 1


def test_import_reads_json_file(tmp_path):
    """Test that import_from() reads and imports entries from JSON file."""
    service = ImportExportService()
    memory = MemoryService()

    # Create a JSON file with entries
    filepath = tmp_path / "import.json"
    entries = [
        {"operation": "add", "operands": [1, 2], "result": 3, "success": True,
         "execution_time_ms": 1.0, "id": "test-id-1", "timestamp": "2026-01-01T00:00:00"},
        {"operation": "subtract", "operands": [5, 3], "result": 2, "success": True,
         "execution_time_ms": 2.0, "id": "test-id-2", "timestamp": "2026-01-01T00:00:01"},
    ]
    filepath.write_text(json.dumps(entries))

    # Import
    count = service.import_from(memory, filepath)

    assert count == 2
    retrieved = memory.retrieve()
    assert len(retrieved) == 2
    assert retrieved[0].operation == "add"
    assert retrieved[1].operation == "subtract"


def test_import_validates_json_structure(tmp_path):
    """Test that import_from() validates JSON structure and raises on invalid data."""
    service = ImportExportService()
    memory = MemoryService()

    # Test: not a list
    filepath = tmp_path / "not_list.json"
    filepath.write_text('{"operation": "add"}')

    with pytest.raises(Exception, match="JSON must be a list"):
        service.import_from(memory, filepath)


def test_import_skips_duplicate_ids(tmp_path):
    """Test that import_from() skips entries with duplicate IDs."""
    service = ImportExportService()
    memory = MemoryService()

    # Add an entry with ID "dup-id"
    entry1 = _entry(operation="add")
    entry1.id = "dup-id"
    memory.store(entry1)

    # Try to import same ID
    filepath = tmp_path / "dupes.json"
    entries = [
        {"operation": "multiply", "operands": [2, 3], "result": 6, "success": True,
         "execution_time_ms": 1.5, "id": "dup-id", "timestamp": "2026-01-01T00:00:00"},
    ]
    filepath.write_text(json.dumps(entries))

    # Import should skip the duplicate
    count = service.import_from(memory, filepath)
    assert count == 0

    # Verify original entry unchanged
    retrieved = memory.retrieve()
    assert len(retrieved) == 1
    assert retrieved[0].operation == "add"
