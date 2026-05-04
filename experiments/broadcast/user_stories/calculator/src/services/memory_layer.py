"""
Memory Layer - Data Persistence and History Management

This layer handles all persistence, history, filtering, and statistics operations.
It is completely independent of the calculation engine and operates only on
MemoryEntry objects that are passed to it.
"""

from pathlib import Path
from typing import Optional
from ..models.memory_entry import MemoryEntry
from ..storage.json_storage import JsonStorage
from .filter_service import FilterService
from .history_export_service import HistoryExportService
from .statistics_service import StatisticsService


class MemoryLayer:
    """Service layer for managing calculation memory and history.

    This layer:
    - Stores and retrieves calculation entries
    - Filters entries by operation type and state
    - Computes statistics over stored entries
    - Exports and imports history to/from files
    - Maintains entry IDs and timestamps

    It does NOT:
    - Perform any calculations
    - Define business logic for operations
    - Interact with the calculation engine
    """

    def __init__(self, storage: JsonStorage) -> None:
        """Initialize with a storage backend.

        Args:
            storage: JsonStorage instance for persistence
        """
        self.storage = storage
        self._filter_service = FilterService()
        self._export_service = HistoryExportService()

    def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry via the storage layer.

        Args:
            entry: MemoryEntry (ResultEntry or ErrorEntry) to store
        """
        self.storage.save(entry)

    def retrieve(self) -> list[MemoryEntry]:
        """Retrieve all stored memory entries.

        Returns:
            List of MemoryEntry objects (ResultEntry or ErrorEntry)
        """
        return self.storage.load_memory_all()

    def filter_entries(
        self,
        operation: Optional[str] = None,
        state: Optional[str] = None,
    ) -> list[MemoryEntry]:
        """Filter stored memory entries by operation type and/or result state.

        Args:
            operation: Operation type to filter by (e.g., 'add', 'subtract')
                      None means no operation filter
            state: Result state to filter by ('success' or 'error')
                  None means no state filter

        Returns:
            List of MemoryEntry objects matching all specified criteria

        Raises:
            ValueError: If state is not 'success', 'error', or None
        """
        entries = self.retrieve()
        return self._filter_service.filter_entries(entries, operation=operation, state=state)

    def get_valid_operations(self) -> list[str]:
        """Get all unique operation types present in stored entries.

        Returns:
            Sorted list of unique operation names
        """
        entries = self.retrieve()
        return self._filter_service.get_valid_operations(entries)

    def export_history(self, filepath: str | Path) -> None:
        """Export all memory entries to a JSON file.

        Args:
            filepath: Path to the output JSON file

        Raises:
            IOError: If the file cannot be written
        """
        entries = self.retrieve()
        self._export_service.export_history(entries, filepath)

    def import_history(
        self,
        filepath: str | Path,
        overwrite: bool = False,
    ) -> tuple[int, list[str]]:
        """Import memory entries from a JSON file.

        Validates imported data structure before applying.
        Skips invalid or duplicate entries individually.

        Args:
            filepath: Path to the input JSON file
            overwrite: If False (default), skip entries with duplicate IDs.
                      If True, accept all entries regardless of existing IDs.

        Returns:
            A tuple of:
            - Number of successfully imported entries
            - List of validation error messages for skipped entries

        Raises:
            IOError: If the file cannot be read
            ValueError: If the JSON structure is invalid
        """
        existing_entries = self.retrieve() if not overwrite else []
        existing_ids = {e.entry_id for e in existing_entries}

        entries, errors = self._export_service.import_history(
            filepath,
            skip_duplicates=not overwrite,
            existing_ids=existing_ids,
        )

        # Store imported entries
        for entry in entries:
            self.store(entry)

        return len(entries), errors

    def get_statistics(self) -> dict:
        """Compute and return statistics over stored entries.

        Returns:
            A dictionary containing:
            - operation_counts: dict of operation -> count
            - total_errors: int
            - error_rate_percentage: float
            - average_execution_time_ms: float
        """
        from .memory_service import MemoryService
        # Create a temporary memory service for statistics computation
        # (StatisticsService requires a MemoryService interface)
        memory_service = MemoryService(self.storage)
        stats_service = StatisticsService(memory_service)
        stats = stats_service.compute_statistics()
        return {
            "operation_counts": stats.operation_counts,
            "total_errors": stats.total_errors,
            "error_rate_percentage": stats.error_rate_percentage,
            "average_execution_time_ms": stats.average_execution_time_ms,
        }
