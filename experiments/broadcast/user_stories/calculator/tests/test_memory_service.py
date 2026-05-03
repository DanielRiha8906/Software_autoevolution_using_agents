import pytest
from unittest.mock import MagicMock
from src.models.memory_entry import ResultEntry, ErrorEntry, _reset_id_counter
from src.services.memory_service import MemoryService


class TestMemoryService:
    def setup_method(self):
        _reset_id_counter()
        self.storage = MagicMock()
        self.service = MemoryService(self.storage)

    def test_store_result_entry(self):
        """Test storing a successful calculation result."""
        entry = ResultEntry(
            operation="add",
            operands=[3, 5],
            result=8,
        )
        self.service.store(entry)
        self.storage.save.assert_called_once_with(entry)

    def test_store_error_entry(self):
        """Test storing a failed calculation error."""
        entry = ErrorEntry(
            operation="divide",
            operands=[5, 0],
            error_message="Division by zero is not allowed",
        )
        self.service.store(entry)
        self.storage.save.assert_called_once_with(entry)

    def test_retrieve_empty(self):
        """Test retrieving when no entries exist."""
        self.storage.load_memory_all.return_value = []
        result = self.service.retrieve()
        assert result == []
        self.storage.load_memory_all.assert_called_once()

    def test_retrieve_multiple_entries(self):
        """Test retrieving multiple entries."""
        entries = [
            ResultEntry(operation="add", operands=[1, 2], result=3),
            ErrorEntry(operation="divide", operands=[5, 0], error_message="error"),
            ResultEntry(operation="multiply", operands=[2, 3], result=6),
        ]
        self.storage.load_memory_all.return_value = entries
        result = self.service.retrieve()
        assert len(result) == 3
        assert result == entries
        self.storage.load_memory_all.assert_called_once()

    def test_store_delegates_to_storage(self):
        """Verify store() delegates to storage.save()."""
        entry = ResultEntry(operation="add", operands=[1, 2], result=3)
        self.service.store(entry)
        assert self.storage.save.called

    def test_retrieve_delegates_to_storage(self):
        """Verify retrieve() delegates to storage.load_memory_all()."""
        self.storage.load_memory_all.return_value = []
        self.service.retrieve()
        assert self.storage.load_memory_all.called

    def test_multiple_stores(self):
        """Test storing multiple entries sequentially."""
        entry1 = ResultEntry(operation="add", operands=[1, 2], result=3)
        entry2 = ErrorEntry(operation="divide", operands=[5, 0], error_message="error")
        
        self.service.store(entry1)
        self.service.store(entry2)
        
        assert self.storage.save.call_count == 2
        calls = self.storage.save.call_args_list
        assert calls[0][0][0] == entry1
        assert calls[1][0][0] == entry2

    def test_retrieve_preserves_entry_types(self):
        """Verify that retrieved entries maintain their types."""
        result_entry = ResultEntry(operation="add", operands=[1, 2], result=3)
        error_entry = ErrorEntry(operation="divide", operands=[5, 0], error_message="error")
        
        self.storage.load_memory_all.return_value = [result_entry, error_entry]
        entries = self.service.retrieve()
        
        assert isinstance(entries[0], ResultEntry)
        assert isinstance(entries[1], ErrorEntry)
        assert not entries[0].is_error()
        assert entries[1].is_error()
