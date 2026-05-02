import pytest
from unittest.mock import Mock
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService
from src.storage.memory_storage import MemoryEntryStorage


class TestMemoryServiceStore:
    """Test cases for MemoryService.store() method."""

    def test_store_adds_entry_to_collection(self):
        """Test that store() adds a single entry to the collection."""
        service = MemoryService()
        entry = MemoryEntry(
            operation="add",
            operand_a=2,
            operand_b=3,
            result=5,
            success=True,
            error_message=None,
        )
        service.store(entry)
        assert len(service.retrieve()) == 1
        assert service.retrieve()[0] == entry

    def test_store_multiple_entries(self):
        """Test that store() can add multiple entries sequentially."""
        service = MemoryService()
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=1,
                operand_b=2,
                result=3,
                success=True,
                error_message=None,
            ),
            MemoryEntry(
                operation="subtract",
                operand_a=5,
                operand_b=3,
                result=2,
                success=True,
                error_message=None,
            ),
            MemoryEntry(
                operation="multiply",
                operand_a=4,
                operand_b=5,
                result=20,
                success=True,
                error_message=None,
            ),
        ]
        for entry in entries:
            service.store(entry)
        assert len(service.retrieve()) == 3
        assert service.retrieve() == entries

    def test_store_successful_operation(self):
        """Test storing an entry with success=True."""
        service = MemoryService()
        entry = MemoryEntry(
            operation="divide",
            operand_a=10,
            operand_b=2,
            result=5.0,
            success=True,
            error_message=None,
        )
        service.store(entry)
        retrieved = service.retrieve()[0]
        assert retrieved.success is True
        assert retrieved.result == 5.0

    def test_store_failed_operation(self):
        """Test storing an entry with success=False and error_message."""
        service = MemoryService()
        entry = MemoryEntry(
            operation="divide",
            operand_a=10,
            operand_b=0,
            result=None,
            success=False,
            error_message="Division by zero",
        )
        service.store(entry)
        retrieved = service.retrieve()[0]
        assert retrieved.success is False
        assert retrieved.error_message == "Division by zero"

    def test_store_preserves_entry_fields(self):
        """Test that store() preserves all 9 fields of the entry."""
        service = MemoryService()
        entry = MemoryEntry(
            operation="sqrt",
            operand_a=16,
            operand_b=0,
            result=4.0,
            success=True,
            error_message=None,
            entry_id="test-id-123",
        )
        service.store(entry)
        retrieved = service.retrieve()[0]
        assert retrieved.operation == "sqrt"
        assert retrieved.operand_a == 16
        assert retrieved.operand_b == 0
        assert retrieved.result == 4.0
        assert retrieved.success is True
        assert retrieved.error_message is None
        assert retrieved.entry_id == "test-id-123"
        assert retrieved.timestamp is not None
        assert retrieved.execution_time_ms == 0.0

    def test_store_delegates_to_storage_if_provided(self):
        """Test that store() calls storage.save() when storage is provided."""
        mock_storage = Mock(spec=MemoryEntryStorage)
        service = MemoryService(storage=mock_storage)
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        service.store(entry)
        mock_storage.save.assert_called_once_with(entry)

    def test_store_does_not_call_storage_if_none(self):
        """Test that store() does not error when storage=None."""
        service = MemoryService(storage=None)
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        # Should not raise
        service.store(entry)
        assert len(service.retrieve()) == 1

    def test_store_raises_type_error_on_invalid_input(self):
        """Test that store() raises TypeError for non-MemoryEntry input."""
        service = MemoryService()
        with pytest.raises(TypeError):
            service.store("not an entry")
        with pytest.raises(TypeError):
            service.store(123)
        with pytest.raises(TypeError):
            service.store(None)
        with pytest.raises(TypeError):
            service.store({})


class TestMemoryServiceRetrieve:
    """Test cases for MemoryService.retrieve() method."""

    def test_retrieve_empty_initially(self):
        """Test that retrieve() returns empty list on fresh service."""
        service = MemoryService()
        assert service.retrieve() == []
        assert isinstance(service.retrieve(), list)

    def test_retrieve_returns_all_stored_entries(self):
        """Test that retrieve() returns all entries that were stored."""
        service = MemoryService()
        entries = [
            MemoryEntry(
                operation="add",
                operand_a=i,
                operand_b=i + 1,
                result=2 * i + 1,
                success=True,
                error_message=None,
            )
            for i in range(3)
        ]
        for entry in entries:
            service.store(entry)
        retrieved = service.retrieve()
        assert len(retrieved) == 3
        assert retrieved == entries

    def test_retrieve_returns_entries_in_order(self):
        """Test that retrieve() returns entries in the order they were stored."""
        service = MemoryService()
        entries = []
        for i in range(5):
            entry = MemoryEntry(
                operation=f"op{i}",
                operand_a=float(i),
                operand_b=float(i + 1),
                result=float(2 * i + 1),
                success=True,
                error_message=None,
                entry_id=f"entry-{i}",
            )
            entries.append(entry)
            service.store(entry)
        retrieved = service.retrieve()
        for i, entry in enumerate(retrieved):
            assert entry.entry_id == f"entry-{i}"

    def test_retrieve_includes_successful_entries(self):
        """Test that retrieve() includes all successful entries."""
        service = MemoryService()
        for i in range(3):
            entry = MemoryEntry(
                operation="add",
                operand_a=float(i),
                operand_b=float(i + 1),
                result=float(2 * i + 1),
                success=True,
                error_message=None,
            )
            service.store(entry)
        retrieved = service.retrieve()
        assert len(retrieved) == 3
        assert all(entry.success for entry in retrieved)

    def test_retrieve_includes_failed_entries(self):
        """Test that retrieve() includes all failed entries."""
        service = MemoryService()
        for i in range(3):
            entry = MemoryEntry(
                operation="divide",
                operand_a=1,
                operand_b=0,
                result=None,
                success=False,
                error_message=f"Error {i}",
            )
            service.store(entry)
        retrieved = service.retrieve()
        assert len(retrieved) == 3
        assert all(not entry.success for entry in retrieved)

    def test_retrieve_does_not_call_storage(self):
        """Test that retrieve() does not call storage.load_all()."""
        mock_storage = Mock(spec=MemoryEntryStorage)
        service = MemoryService(storage=mock_storage)
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        service.store(entry)
        service.retrieve()
        mock_storage.load_all.assert_not_called()

    def test_retrieve_returns_list_type(self):
        """Test that retrieve() always returns a list."""
        service = MemoryService()
        assert isinstance(service.retrieve(), list)
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        service.store(entry)
        assert isinstance(service.retrieve(), list)


class TestMemoryServiceConstruction:
    """Test cases for MemoryService initialization."""

    def test_init_with_no_storage(self):
        """Test that MemoryService initializes without storage parameter."""
        service = MemoryService()
        assert service._storage is None
        assert service._entries == []

    def test_init_with_storage(self):
        """Test that MemoryService initializes with storage backend."""
        mock_storage = Mock(spec=MemoryEntryStorage)
        service = MemoryService(storage=mock_storage)
        assert service._storage is mock_storage
        assert service._entries == []

    def test_init_creates_empty_collection(self):
        """Test that initialization creates an empty internal list."""
        service1 = MemoryService()
        service2 = MemoryService()
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        service1.store(entry)
        # Verify service2 is independent
        assert len(service1.retrieve()) == 1
        assert len(service2.retrieve()) == 0


class TestMemoryServiceEdgeCases:
    """Test edge cases and special scenarios."""

    def test_store_entry_with_none_result(self):
        """Test storing an entry where result=None (failed operation)."""
        service = MemoryService()
        entry = MemoryEntry(
            operation="sqrt",
            operand_a=-4,
            operand_b=0,
            result=None,
            success=False,
            error_message="Cannot compute square root of negative number",
        )
        service.store(entry)
        retrieved = service.retrieve()[0]
        assert retrieved.result is None
        assert retrieved.success is False

    def test_store_entry_with_none_error_message(self):
        """Test storing an entry where error_message=None (successful operation)."""
        service = MemoryService()
        entry = MemoryEntry(
            operation="multiply",
            operand_a=7,
            operand_b=8,
            result=56,
            success=True,
            error_message=None,
        )
        service.store(entry)
        retrieved = service.retrieve()[0]
        assert retrieved.error_message is None
        assert retrieved.success is True

    def test_store_entry_with_large_operands(self):
        """Test storing an entry with very large numbers."""
        service = MemoryService()
        large_num = 1e308
        entry = MemoryEntry(
            operation="add",
            operand_a=large_num,
            operand_b=large_num,
            result=2 * large_num,
            success=True,
            error_message=None,
        )
        service.store(entry)
        retrieved = service.retrieve()[0]
        assert retrieved.operand_a == large_num
        assert retrieved.operand_b == large_num
        assert retrieved.result == 2 * large_num

    def test_store_many_entries(self):
        """Test storing over 100 entries sequentially."""
        service = MemoryService()
        num_entries = 150
        for i in range(num_entries):
            entry = MemoryEntry(
                operation="add",
                operand_a=float(i),
                operand_b=float(i + 1),
                result=float(2 * i + 1),
                success=True,
                error_message=None,
            )
            service.store(entry)
        retrieved = service.retrieve()
        assert len(retrieved) == num_entries

    def test_retrieve_after_multiple_stores(self):
        """Test alternating store and retrieve operations."""
        service = MemoryService()
        for i in range(5):
            entry = MemoryEntry(
                operation="add",
                operand_a=float(i),
                operand_b=1,
                result=float(i + 1),
                success=True,
                error_message=None,
            )
            service.store(entry)
            retrieved = service.retrieve()
            assert len(retrieved) == i + 1

    def test_storage_exception_propagates(self):
        """Test that exceptions from storage.save() propagate to caller."""
        mock_storage = Mock(spec=MemoryEntryStorage)
        mock_storage.save.side_effect = RuntimeError("Storage error")
        service = MemoryService(storage=mock_storage)
        entry = MemoryEntry(
            operation="add",
            operand_a=1,
            operand_b=1,
            result=2,
            success=True,
            error_message=None,
        )
        with pytest.raises(RuntimeError, match="Storage error"):
            service.store(entry)
