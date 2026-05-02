from unittest.mock import MagicMock
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService


class TestMemoryService:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = MemoryService(self.storage)

    def test_init_accepts_storage(self):
        assert self.service.storage is self.storage

    def test_store_calls_storage_save(self):
        entry = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_time_ms=10.0,
        )
        self.service.store(entry)
        self.storage.save.assert_called_once_with(entry)

    def test_store_with_failed_operation(self):
        entry = MemoryEntry(
            operation="divide",
            operand_a=5.0,
            operand_b=0.0,
            result=None,
            success=False,
            error_message="Division by zero",
            execution_time_ms=5.0,
        )
        self.service.store(entry)
        self.storage.save.assert_called_once_with(entry)

    def test_retrieve_calls_storage_load_all(self):
        self.storage.load_all.return_value = []
        self.service.retrieve()
        self.storage.load_all.assert_called_once()

    def test_retrieve_returns_list_of_entries(self):
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=1.0,
                operand_b=2.0,
                result=3.0,
                success=True,
                error_message=None,
                execution_time_ms=10.0,
            )
        ]
        self.storage.load_all.return_value = entries
        result = self.service.retrieve()
        assert result == entries

    def test_retrieve_returns_empty_list(self):
        self.storage.load_all.return_value = []
        result = self.service.retrieve()
        assert result == []

    def test_retrieve_returns_multiple_entries(self):
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=1.0,
                operand_b=2.0,
                result=3.0,
                success=True,
                error_message=None,
                execution_time_ms=10.0,
            ),
            MemoryEntry(
                operation="multiply",
                operand_a=3.0,
                operand_b=4.0,
                result=12.0,
                success=True,
                error_message=None,
                execution_time_ms=5.0,
            ),
        ]
        self.storage.load_all.return_value = entries
        result = self.service.retrieve()
        assert len(result) == 2
        assert result[0].operation == "add"
        assert result[1].operation == "multiply"

    def test_store_and_retrieve_round_trip(self):
        entry = MemoryEntry(
            operation="subtract",
            operand_a=10.0,
            operand_b=4.0,
            result=6.0,
            success=True,
            error_message=None,
            execution_time_ms=8.0,
        )
        self.service.store(entry)
        self.storage.load_all.return_value = [entry]
        retrieved = self.service.retrieve()
        assert retrieved[0].operation == "subtract"
        assert retrieved[0].result == 6.0

    def test_store_multiple_entries_independently(self):
        entry1 = MemoryEntry(
            operation="add",
            operand_a=1.0,
            operand_b=2.0,
            result=3.0,
            success=True,
            error_message=None,
            execution_time_ms=10.0,
        )
        entry2 = MemoryEntry(
            operation="divide",
            operand_a=10.0,
            operand_b=2.0,
            result=5.0,
            success=True,
            error_message=None,
            execution_time_ms=12.0,
        )
        self.service.store(entry1)
        self.service.store(entry2)
        assert self.storage.save.call_count == 2
