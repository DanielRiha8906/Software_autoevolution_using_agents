import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.models.memory_entry import MemoryEntry
from src.storage.json_storage import JsonStorage
from src.services.memory_service import MemoryService


class TestMemoryServiceStore:
    """Test MemoryService.store() method."""

    def setup_method(self):
        """Setup a fresh MemoryService with mocked storage for each test."""
        self.storage_mock = MagicMock(spec=JsonStorage)
        self.service = MemoryService(self.storage_mock)

    def test_store_calls_storage_save(self):
        """store() should delegate to storage.save()."""
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
            error=None,
            error_type=None,
        )
        self.service.store(entry)
        self.storage_mock.save.assert_called_once_with(entry)

    def test_store_with_success_entry(self):
        """store() should handle successful calculation entries."""
        entry = MemoryEntry(
            operation="multiply",
            operand_a=4,
            operand_b=7,
            result=28,
            error=None,
            error_type=None,
        )
        self.service.store(entry)
        self.storage_mock.save.assert_called_once()
        called_entry = self.storage_mock.save.call_args[0][0]
        assert called_entry.result == 28
        assert called_entry.error is None

    def test_store_with_error_entry(self):
        """store() should handle error entries."""
        entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            result=None,
            error="Division by zero is not allowed",
            error_type="ValueError",
        )
        self.service.store(entry)
        self.storage_mock.save.assert_called_once()
        called_entry = self.storage_mock.save.call_args[0][0]
        assert called_entry.result is None
        assert called_entry.error == "Division by zero is not allowed"
        assert called_entry.error_type == "ValueError"

    def test_store_passes_entry_unchanged(self):
        """store() should pass the entry object as-is to storage."""
        entry = MemoryEntry(
            operation="sqrt",
            operand_a=16,
            operand_b=0,
            result=4.0,
            error=None,
            error_type=None,
            uuid="test-uuid-123",
            timestamp="2026-05-03T14:30:00",
        )
        self.service.store(entry)
        called_entry = self.storage_mock.save.call_args[0][0]
        assert called_entry is entry
        assert called_entry.uuid == "test-uuid-123"
        assert called_entry.timestamp == "2026-05-03T14:30:00"


class TestMemoryServiceRetrieve:
    """Test MemoryService.retrieve() method."""

    def setup_method(self):
        """Setup a fresh MemoryService with mocked storage for each test."""
        self.storage_mock = MagicMock(spec=JsonStorage)
        self.service = MemoryService(self.storage_mock)

    def test_retrieve_calls_storage_load_all(self):
        """retrieve() should delegate to storage.load_all()."""
        self.storage_mock.load_all.return_value = []
        self.service.retrieve()
        self.storage_mock.load_all.assert_called_once()

    def test_retrieve_returns_empty_list(self):
        """retrieve() should return empty list when storage is empty."""
        self.storage_mock.load_all.return_value = []
        result = self.service.retrieve()
        assert result == []

    def test_retrieve_returns_list_of_entries(self):
        """retrieve() should return list of MemoryEntry objects."""
        entry1 = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
        )
        entry2 = MemoryEntry(
            operation="subtract",
            operand_a=5,
            operand_b=3,
            result=2,
            error=None,
            error_type=None,
        )
        self.storage_mock.load_all.return_value = [entry1, entry2]
        result = self.service.retrieve()
        assert len(result) == 2
        assert result[0] is entry1
        assert result[1] is entry2

    def test_retrieve_with_mixed_entries(self):
        """retrieve() should handle mix of success and error entries."""
        success_entry = MemoryEntry(
            operation="multiply",
            operand_a=3,
            operand_b=4,
            result=12,
            error=None,
            error_type=None,
        )
        error_entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            result=None,
            error="Division by zero",
            error_type="ValueError",
        )
        self.storage_mock.load_all.return_value = [success_entry, error_entry]
        result = self.service.retrieve()
        assert len(result) == 2
        assert result[0].error is None
        assert result[1].error is not None


class TestMemoryServiceIntegrationWithRealStorage:
    """Integration tests with real JsonStorage using temp files."""

    def test_store_and_retrieve_single_entry(self):
        """Test full round-trip: store and retrieve a single entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(filepath)
            service = MemoryService(storage)

            # Store an entry
            entry = MemoryEntry(
                operation="add",
                operand_a=10,
                operand_b=20,
                result=30,
                error=None,
                error_type=None,
                uuid="test-uuid-001",
                timestamp="2026-05-03T10:00:00",
            )
            service.store(entry)

            # Retrieve and verify
            retrieved = service.retrieve()
            assert len(retrieved) == 1
            assert retrieved[0].operation == "add"
            assert retrieved[0].operand_a == 10
            assert retrieved[0].operand_b == 20
            assert retrieved[0].result == 30
            assert retrieved[0].uuid == "test-uuid-001"

    def test_store_and_retrieve_multiple_entries(self):
        """Test storing and retrieving multiple entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(filepath)
            service = MemoryService(storage)

            # Store multiple entries
            entries = [
                MemoryEntry(
                    operation="add",
                    operand_a=1,
                    operand_b=2,
                    result=3,
                    error=None,
                    error_type=None,
                ),
                MemoryEntry(
                    operation="subtract",
                    operand_a=10,
                    operand_b=3,
                    result=7,
                    error=None,
                    error_type=None,
                ),
                MemoryEntry(
                    operation="divide",
                    operand_a=5,
                    operand_b=0,
                    result=None,
                    error="Division by zero",
                    error_type="ValueError",
                ),
            ]

            for entry in entries:
                service.store(entry)

            # Retrieve and verify
            retrieved = service.retrieve()
            assert len(retrieved) == 3
            assert retrieved[0].operation == "add"
            assert retrieved[1].operation == "subtract"
            assert retrieved[2].operation == "divide"
            assert retrieved[2].error is not None

    def test_retrieve_from_existing_file(self):
        """Test retrieving from a file with pre-existing entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(filepath)
            service = MemoryService(storage)

            # Store first set of entries
            entry1 = MemoryEntry(
                operation="add",
                operand_a=1,
                operand_b=1,
                result=2,
                error=None,
                error_type=None,
            )
            service.store(entry1)

            # Create new service instance (simulating app restart)
            service2 = MemoryService(JsonStorage(filepath))

            # Store another entry
            entry2 = MemoryEntry(
                operation="multiply",
                operand_a=3,
                operand_b=4,
                result=12,
                error=None,
                error_type=None,
            )
            service2.store(entry2)

            # Retrieve all - should have both
            retrieved = service2.retrieve()
            assert len(retrieved) == 2
            assert retrieved[0].operation == "add"
            assert retrieved[1].operation == "multiply"

    def test_store_and_retrieve_preserves_entry_fields(self):
        """Test that all fields are preserved through store/retrieve cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(filepath)
            service = MemoryService(storage)

            # Store entry with all fields
            entry = MemoryEntry(
                operation="power",
                operand_a=2.5,
                operand_b=3.0,
                result=15.625,
                error=None,
                error_type=None,
                uuid="550e8400-e29b-41d4-a716-446655440000",
                timestamp="2026-05-03T14:30:00.123456",
            )
            service.store(entry)

            # Retrieve and verify all fields
            retrieved = service.retrieve()
            assert len(retrieved) == 1
            restored = retrieved[0]
            assert restored.operation == "power"
            assert restored.operand_a == 2.5
            assert restored.operand_b == 3.0
            assert restored.result == 15.625
            assert restored.error is None
            assert restored.error_type is None
            assert restored.uuid == "550e8400-e29b-41d4-a716-446655440000"
            assert restored.timestamp == "2026-05-03T14:30:00.123456"

    def test_storage_file_is_json(self):
        """Test that storage produces valid JSON file."""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_storage.json"
            storage = JsonStorage(filepath)
            service = MemoryService(storage)

            # Store an entry
            entry = MemoryEntry(
                operation="add",
                operand_a=5,
                operand_b=3,
                result=8,
                error=None,
                error_type=None,
            )
            service.store(entry)

            # Verify file is valid JSON
            with open(filepath) as f:
                data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["operation"] == "add"
            assert data[0]["result"] == 8


class TestMemoryServiceEdgeCases:
    """Test edge cases and error handling."""

    def test_store_multiple_times_same_entry(self):
        """Test storing the same entry object multiple times."""
        storage_mock = MagicMock(spec=JsonStorage)
        service = MemoryService(storage_mock)

        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
        )

        service.store(entry)
        service.store(entry)
        service.store(entry)

        assert storage_mock.save.call_count == 3

    def test_retrieve_multiple_calls(self):
        """Test that multiple retrieve() calls work correctly."""
        storage_mock = MagicMock(spec=JsonStorage)
        service = MemoryService(storage_mock)

        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
        )
        storage_mock.load_all.return_value = [entry]

        result1 = service.retrieve()
        result2 = service.retrieve()

        assert result1 == result2
        assert storage_mock.load_all.call_count == 2

    def test_store_with_none_result_error_path(self):
        """Test storing error entry with None result."""
        storage_mock = MagicMock(spec=JsonStorage)
        service = MemoryService(storage_mock)

        entry = MemoryEntry(
            operation="sqrt",
            operand_a=-5,
            operand_b=0,
            result=None,
            error="Cannot take square root of negative number",
            error_type="ValueError",
        )
        service.store(entry)

        called_entry = storage_mock.save.call_args[0][0]
        assert called_entry.result is None
        assert called_entry.error is not None


class TestMemoryServiceStorageInteraction:
    """Test interactions between MemoryService and JsonStorage."""

    def test_service_delegates_to_storage(self):
        """Verify MemoryService is a proper facade over JsonStorage."""
        storage_mock = MagicMock(spec=JsonStorage)
        service = MemoryService(storage_mock)

        # store() calls storage.save()
        entry1 = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=2,
            result=3,
            error=None,
            error_type=None,
        )
        service.store(entry1)
        storage_mock.save.assert_called_with(entry1)

        # retrieve() calls storage.load_all()
        entry2 = MemoryEntry(
            operation="subtract",
            operand_a=5,
            operand_b=3,
            result=2,
            error=None,
            error_type=None,
        )
        storage_mock.load_all.return_value = [entry2]
        result = service.retrieve()
        storage_mock.load_all.assert_called_once()
        assert result == [entry2]
