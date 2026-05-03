import json
import pytest
import tempfile
from pathlib import Path

from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.services.import_export_service import ImportExportService


def _make_entry(**kwargs):
    """Helper to create a MemoryEntry with defaults."""
    defaults = dict(
        operation="add",
        operands=[1, 2],
        result=3,
        success=True,
        execution_time_ms=1.0
    )
    defaults.update(kwargs)
    return MemoryEntry(**defaults)


@pytest.fixture
def memory_service():
    """Fresh MemoryService for each test."""
    return MemoryService()


@pytest.fixture
def import_export_service(memory_service):
    """ImportExportService bound to the memory_service."""
    return ImportExportService(memory_service)


@pytest.fixture
def temp_json_file():
    """Temporary JSON file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        filepath = f.name
    yield filepath
    # Cleanup
    Path(filepath).unlink(missing_ok=True)


def test_export_creates_valid_json_file(memory_service, import_export_service, temp_json_file):
    """export() must create valid JSON with a list of MemoryEntry dicts."""
    # Store some entries
    entry1 = _make_entry(id="entry-1", operation="add", result=3)
    entry2 = _make_entry(id="entry-2", operation="multiply", operands=[2, 3], result=6)
    memory_service.store(entry1)
    memory_service.store(entry2)

    # Export
    import_export_service.export(temp_json_file)

    # Verify file exists and contains valid JSON
    assert Path(temp_json_file).exists()

    with open(temp_json_file, 'r') as f:
        data = json.load(f)

    # Should be a list
    assert isinstance(data, list)
    assert len(data) == 2

    # Each item should be a dict with required fields
    for item in data:
        assert isinstance(item, dict)
        assert "id" in item
        assert "operation" in item
        assert "operands" in item
        assert "result" in item
        assert "success" in item
        assert "execution_time_ms" in item


def test_import_loads_entries(memory_service, import_export_service, temp_json_file):
    """import_from() must load entries and make them available via memory.retrieve()."""
    # Create a JSON file with entries
    entries_data = [
        {
            "id": "entry-1",
            "operation": "add",
            "operands": [1, 2],
            "result": 3,
            "success": True,
            "execution_time_ms": 1.5,
            "timestamp": "2025-01-01T00:00:00"
        },
        {
            "id": "entry-2",
            "operation": "multiply",
            "operands": [2, 3],
            "result": 6,
            "success": True,
            "execution_time_ms": 2.0,
            "timestamp": "2025-01-01T00:00:01"
        }
    ]

    with open(temp_json_file, 'w') as f:
        json.dump(entries_data, f)

    # Import
    import_export_service.import_from(temp_json_file)

    # Verify entries are now in memory
    retrieved = memory_service.retrieve()
    assert len(retrieved) == 2
    assert any(e.id == "entry-1" for e in retrieved)
    assert any(e.id == "entry-2" for e in retrieved)


def test_import_validates_structure(memory_service, import_export_service, temp_json_file):
    """import_from() must raise Exception for invalid JSON structure."""
    # Test 1: JSON is not a list
    with open(temp_json_file, 'w') as f:
        json.dump({"not": "a list"}, f)

    with pytest.raises(Exception, match="must be a list"):
        import_export_service.import_from(temp_json_file)

    # Test 2: List contains non-dict items
    with open(temp_json_file, 'w') as f:
        json.dump(["not a dict"], f)

    with pytest.raises(Exception, match="must be a dictionary"):
        import_export_service.import_from(temp_json_file)

    # Test 3: Dict missing required fields
    with open(temp_json_file, 'w') as f:
        json.dump([{"id": "test", "operation": "add"}], f)  # Missing other fields

    with pytest.raises(Exception, match="Missing required fields"):
        import_export_service.import_from(temp_json_file)


def test_import_preserves_existing_entries(memory_service, import_export_service, temp_json_file):
    """import_from() must not delete entries already in memory."""
    # Store an existing entry
    existing_entry = _make_entry(id="existing-1", operation="add")
    memory_service.store(existing_entry)

    # Import new entries
    entries_data = [
        {
            "id": "new-1",
            "operation": "subtract",
            "operands": [5, 3],
            "result": 2,
            "success": True,
            "execution_time_ms": 1.0,
            "timestamp": "2025-01-01T00:00:00"
        }
    ]

    with open(temp_json_file, 'w') as f:
        json.dump(entries_data, f)

    import_export_service.import_from(temp_json_file)

    # Verify both entries are present
    retrieved = memory_service.retrieve()
    assert len(retrieved) == 2
    assert any(e.id == "existing-1" for e in retrieved)
    assert any(e.id == "new-1" for e in retrieved)


def test_import_skips_duplicate_entries(memory_service, import_export_service, temp_json_file):
    """import_from() should not add entries with duplicate IDs."""
    # Store an existing entry
    existing_entry = _make_entry(id="duplicate-id", operation="add", result=10)
    memory_service.store(existing_entry)

    # Try to import an entry with the same ID
    entries_data = [
        {
            "id": "duplicate-id",
            "operation": "multiply",  # Different operation
            "operands": [2, 3],
            "result": 6,
            "success": True,
            "execution_time_ms": 2.0,
            "timestamp": "2025-01-01T00:00:00"
        }
    ]

    with open(temp_json_file, 'w') as f:
        json.dump(entries_data, f)

    import_export_service.import_from(temp_json_file)

    # Verify the existing entry is not overwritten
    retrieved = memory_service.retrieve()
    assert len(retrieved) == 1
    # The original entry should still be there
    assert retrieved[0].id == "duplicate-id"
    assert retrieved[0].operation == "add"
    assert retrieved[0].result == 10
