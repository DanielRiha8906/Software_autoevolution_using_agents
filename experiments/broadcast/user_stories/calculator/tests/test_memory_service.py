import pytest
from src.models.memory_entry import MemoryEntry
from src.services.memory_service import MemoryService


class TestMemoryServiceBasic:
    """Tests for basic MemoryService functionality."""

    def test_create_memory_service(self):
        """MemoryService can be instantiated."""
        service = MemoryService()
        assert service is not None

    def test_memory_service_starts_empty(self):
        """A new MemoryService has no entries."""
        service = MemoryService()
        assert service.retrieve() == []
        assert service.count() == 0

    def test_store_single_entry(self):
        """MemoryService can store a single entry."""
        service = MemoryService()
        entry = MemoryEntry(
            operation="add",
            operand_a=3,
            operand_b=5,
            result=8,
        )
        service.store(entry)
        assert service.count() == 1

    def test_retrieve_returns_stored_entry(self):
        """retrieve() returns the entry that was stored."""
        service = MemoryService()
        entry = MemoryEntry(
            operation="multiply",
            operand_a=2,
            operand_b=4,
            result=8,
        )
        service.store(entry)
        retrieved = service.retrieve()
        assert len(retrieved) == 1
        assert retrieved[0] == entry

    def test_store_multiple_entries(self):
        """MemoryService can store multiple entries."""
        service = MemoryService()
        entry1 = MemoryEntry("add", 1, 2, 3)
        entry2 = MemoryEntry("subtract", 5, 2, 3)
        entry3 = MemoryEntry("multiply", 3, 4, 12)

        service.store(entry1)
        service.store(entry2)
        service.store(entry3)

        assert service.count() == 3
        retrieved = service.retrieve()
        assert len(retrieved) == 3
        assert retrieved[0] == entry1
        assert retrieved[1] == entry2
        assert retrieved[2] == entry3

    def test_retrieve_preserves_order(self):
        """retrieve() returns entries in the order they were stored."""
        service = MemoryService()
        entries = [
            MemoryEntry("add", 1, 1, 2),
            MemoryEntry("subtract", 5, 1, 4),
            MemoryEntry("divide", 10, 2, 5.0),
        ]
        for entry in entries:
            service.store(entry)

        retrieved = service.retrieve()
        assert retrieved == entries


class TestMemoryServiceSuccessfulEntries:
    """Tests for storing successful calculation entries."""

    def test_store_successful_entry(self):
        """MemoryService can store a successful calculation entry."""
        service = MemoryService()
        entry = MemoryEntry(
            operation="divide",
            operand_a=10,
            operand_b=2,
            result=5.0,
            success=True,
        )
        service.store(entry)
        retrieved = service.retrieve()
        assert retrieved[0].success is True
        assert retrieved[0].result == 5.0
        assert retrieved[0].error_message is None

    def test_store_multiple_successful_entries(self):
        """MemoryService can store multiple successful entries."""
        service = MemoryService()
        for i in range(5):
            entry = MemoryEntry(
                operation="add",
                operand_a=i,
                operand_b=1,
                result=i + 1,
                success=True,
            )
            service.store(entry)

        assert service.count() == 5
        retrieved = service.retrieve()
        for entry in retrieved:
            assert entry.success is True


class TestMemoryServiceFailedEntries:
    """Tests for storing failed calculation entries."""

    def test_store_failed_entry(self):
        """MemoryService can store a failed calculation entry."""
        service = MemoryService()
        entry = MemoryEntry(
            operation="divide",
            operand_a=5,
            operand_b=0,
            result=None,
            success=False,
            error_message="Division by zero is not allowed",
        )
        service.store(entry)
        retrieved = service.retrieve()
        assert retrieved[0].success is False
        assert retrieved[0].result is None
        assert retrieved[0].error_message == "Division by zero is not allowed"

    def test_store_multiple_failed_entries(self):
        """MemoryService can store multiple failed entries."""
        service = MemoryService()
        errors = [
            ("divide", "Division by zero is not allowed"),
            ("sqrt", "Cannot take square root of negative number"),
            ("modulo", "Modulo by zero is not allowed"),
        ]
        for operation, error_msg in errors:
            entry = MemoryEntry(
                operation=operation,
                operand_a=1,
                operand_b=0,
                result=None,
                success=False,
                error_message=error_msg,
            )
            service.store(entry)

        assert service.count() == 3
        retrieved = service.retrieve()
        for entry in retrieved:
            assert entry.success is False


class TestMemoryServiceMixed:
    """Tests for storing a mix of successful and failed entries."""

    def test_store_mixed_entries(self):
        """MemoryService can store both successful and failed entries."""
        service = MemoryService()

        # Successful entry
        entry1 = MemoryEntry("add", 1, 2, 3, success=True)
        service.store(entry1)

        # Failed entry
        entry2 = MemoryEntry(
            "divide", 5, 0, None, success=False,
            error_message="Division by zero is not allowed"
        )
        service.store(entry2)

        # Another successful entry
        entry3 = MemoryEntry("multiply", 3, 4, 12, success=True)
        service.store(entry3)

        assert service.count() == 3
        retrieved = service.retrieve()
        assert retrieved[0].success is True
        assert retrieved[1].success is False
        assert retrieved[2].success is True


class TestMemoryServiceClear:
    """Tests for clearing entries."""

    def test_clear_removes_all_entries(self):
        """clear() removes all stored entries."""
        service = MemoryService()
        service.store(MemoryEntry("add", 1, 2, 3))
        service.store(MemoryEntry("subtract", 5, 1, 4))
        assert service.count() == 2

        service.clear()
        assert service.count() == 0
        assert service.retrieve() == []

    def test_clear_on_empty_service(self):
        """clear() on an empty service does not raise an error."""
        service = MemoryService()
        service.clear()
        assert service.count() == 0

    def test_can_store_after_clear(self):
        """Entries can be stored after clearing."""
        service = MemoryService()
        service.store(MemoryEntry("add", 1, 2, 3))
        service.clear()

        new_entry = MemoryEntry("subtract", 5, 2, 3)
        service.store(new_entry)
        assert service.count() == 1
        assert service.retrieve()[0] == new_entry


class TestMemoryServiceCount:
    """Tests for the count() operation."""

    def test_count_empty_service(self):
        """count() returns 0 for empty service."""
        service = MemoryService()
        assert service.count() == 0

    def test_count_after_stores(self):
        """count() reflects the number of stored entries."""
        service = MemoryService()
        assert service.count() == 0

        service.store(MemoryEntry("add", 1, 2, 3))
        assert service.count() == 1

        service.store(MemoryEntry("subtract", 5, 1, 4))
        assert service.count() == 2

        service.store(MemoryEntry("multiply", 2, 3, 6))
        assert service.count() == 3

    def test_count_after_clear(self):
        """count() returns 0 after clear()."""
        service = MemoryService()
        service.store(MemoryEntry("add", 1, 2, 3))
        service.store(MemoryEntry("subtract", 5, 1, 4))
        assert service.count() == 2

        service.clear()
        assert service.count() == 0


class TestMemoryServiceRetrieveIsolation:
    """Tests for retrieve() isolation and immutability."""

    def test_retrieve_returns_copy(self):
        """retrieve() returns a copy, not a reference to internal list."""
        service = MemoryService()
        entry = MemoryEntry("add", 1, 2, 3)
        service.store(entry)

        retrieved1 = service.retrieve()
        retrieved2 = service.retrieve()

        # Should be equal but different list objects
        assert retrieved1 == retrieved2
        assert retrieved1 is not retrieved2

    def test_modifying_retrieved_list_does_not_affect_service(self):
        """Modifying the returned list does not affect the service."""
        service = MemoryService()
        entry1 = MemoryEntry("add", 1, 2, 3)
        service.store(entry1)

        retrieved = service.retrieve()
        assert len(retrieved) == 1

        # Try to modify the returned list
        entry2 = MemoryEntry("subtract", 5, 1, 4)
        retrieved.append(entry2)

        # Service should still have only 1 entry
        assert service.count() == 1
        service_retrieved = service.retrieve()
        assert len(service_retrieved) == 1
        assert service_retrieved[0] == entry1


class TestMemoryServiceEntryAttributes:
    """Tests for entries being stored with all attributes intact."""

    def test_entry_attributes_preserved(self):
        """All MemoryEntry attributes are preserved when stored."""
        service = MemoryService()
        entry = MemoryEntry(
            operation="power",
            operand_a=2,
            operand_b=8,
            result=256,
            success=True,
            error_message=None,
            timestamp="2026-01-01T12:00:00",
            execution_time_ms=0.75,
            entry_id="test-id-123",
        )
        service.store(entry)

        retrieved = service.retrieve()
        stored_entry = retrieved[0]

        assert stored_entry.operation == "power"
        assert stored_entry.operand_a == 2
        assert stored_entry.operand_b == 8
        assert stored_entry.result == 256
        assert stored_entry.success is True
        assert stored_entry.error_message is None
        assert stored_entry.timestamp == "2026-01-01T12:00:00"
        assert stored_entry.execution_time_ms == 0.75
        assert stored_entry.entry_id == "test-id-123"

    def test_failed_entry_attributes_preserved(self):
        """All attributes are preserved for failed entries."""
        service = MemoryService()
        entry = MemoryEntry(
            operation="sqrt",
            operand_a=-1,
            operand_b=0,
            result=None,
            success=False,
            error_message="Cannot take square root of negative number",
            timestamp="2026-01-01T12:00:00",
            execution_time_ms=0.2,
            entry_id="failed-test-id",
        )
        service.store(entry)

        retrieved = service.retrieve()
        stored_entry = retrieved[0]

        assert stored_entry.operation == "sqrt"
        assert stored_entry.operand_a == -1
        assert stored_entry.operand_b == 0
        assert stored_entry.result is None
        assert stored_entry.success is False
        assert stored_entry.error_message == "Cannot take square root of negative number"
        assert stored_entry.timestamp == "2026-01-01T12:00:00"
        assert stored_entry.execution_time_ms == 0.2
        assert stored_entry.entry_id == "failed-test-id"


class TestMemoryServiceEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_store_entry_with_zero_operands(self):
        """MemoryService can store entries with zero operands."""
        service = MemoryService()
        entry = MemoryEntry("add", 0, 0, 0)
        service.store(entry)
        assert service.count() == 1
        assert service.retrieve()[0].operand_a == 0
        assert service.retrieve()[0].operand_b == 0

    def test_store_entry_with_negative_operands(self):
        """MemoryService can store entries with negative operands."""
        service = MemoryService()
        entry = MemoryEntry("subtract", -5, -3, -2)
        service.store(entry)
        assert service.count() == 1
        assert service.retrieve()[0].operand_a == -5
        assert service.retrieve()[0].operand_b == -3

    def test_store_entry_with_large_numbers(self):
        """MemoryService can store entries with large numbers."""
        service = MemoryService()
        large_num = 1e100
        entry = MemoryEntry("multiply", large_num, 2, large_num * 2)
        service.store(entry)
        assert service.count() == 1
        assert service.retrieve()[0].result == large_num * 2

    def test_store_entry_with_float_result(self):
        """MemoryService can store entries with float results."""
        service = MemoryService()
        entry = MemoryEntry("divide", 1, 3, 0.3333333)
        service.store(entry)
        assert service.count() == 1
        assert abs(service.retrieve()[0].result - 0.3333333) < 0.0001

    def test_store_many_entries(self):
        """MemoryService can handle many entries."""
        service = MemoryService()
        for i in range(1000):
            entry = MemoryEntry("add", i, 1, i + 1)
            service.store(entry)

        assert service.count() == 1000
        retrieved = service.retrieve()
        assert len(retrieved) == 1000
        assert retrieved[0].operand_a == 0
        assert retrieved[999].operand_a == 999
