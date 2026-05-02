import pytest
from unittest.mock import MagicMock
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService


class TestMemoryService:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = MemoryService(self.storage)

    def test_store_delegates_to_storage(self):
        entry = MemoryEntry("add", 3.0, 5.0, result=8.0)
        self.service.store(entry)
        self.storage.save.assert_called_once_with(entry)

    def test_get_all_delegates_to_storage(self):
        mock_entries = [
            MemoryEntry("add", 1.0, 2.0, result=3.0),
            MemoryEntry("multiply", 3.0, 4.0, result=12.0),
        ]
        self.storage.load_all.return_value = mock_entries
        result = self.service.get_all()
        assert result == mock_entries
        self.storage.load_all.assert_called_once()

    def test_retrieve_all_delegates_to_storage(self):
        mock_entries = [
            MemoryEntry("subtract", 10.0, 4.0, result=6.0),
        ]
        self.storage.load_all.return_value = mock_entries
        result = self.service.retrieve_all()
        assert result == mock_entries
        self.storage.load_all.assert_called_once()

    def test_get_all_same_as_retrieve_all(self):
        mock_entries = [MemoryEntry("divide", 9.0, 3.0, result=3.0)]
        self.storage.load_all.return_value = mock_entries
        assert self.service.get_all() == self.service.retrieve_all()

    def test_store_successful_entry(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=5.0,
            operand_b=3.0,
            result=8.0,
            success=True,
            execution_time_ms=0.5,
        )
        self.service.store(entry)
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        assert saved.operation == "add"
        assert saved.result == 8.0
        assert saved.success is True

    def test_store_failed_entry(self):
        entry = MemoryEntry(
            operation="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero",
        )
        self.service.store(entry)
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        assert saved.success is False
        assert saved.error_message == "Division by zero"
        assert saved.result is None

    def test_retrieve_all_empty_list(self):
        self.storage.load_all.return_value = []
        result = self.service.retrieve_all()
        assert result == []

    def test_retrieve_all_multiple_entries(self):
        entries = [
            MemoryEntry("add", 1.0, 2.0, result=3.0),
            MemoryEntry("subtract", 5.0, 2.0, result=3.0),
            MemoryEntry("multiply", 3.0, 4.0, result=12.0),
        ]
        self.storage.load_all.return_value = entries
        result = self.service.retrieve_all()
        assert len(result) == 3
        assert result[0].operation == "add"
        assert result[1].operation == "subtract"
        assert result[2].operation == "multiply"
