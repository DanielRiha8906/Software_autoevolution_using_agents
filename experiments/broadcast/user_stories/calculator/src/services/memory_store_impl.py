"""
Memory Store Implementation - Concrete implementation of MemoryStore protocol

This module provides a concrete implementation that satisfies the MemoryStore protocol,
delegating to the existing MemoryService, FilterService, and HistoryExportService
while maintaining backward compatibility.
"""

from pathlib import Path
from typing import Optional
from ..models.memory_entry import MemoryEntry
from ..storage.json_storage import JsonStorage
from .memory_service import MemoryService
from .statistics_service import StatisticsService


class MemoryStoreImpl:
    """Concrete implementation of the MemoryStore interface.

    This implementation wraps the existing MemoryService and related services
    to provide a unified interface for all memory/history operations.
    """

    def __init__(self, storage: JsonStorage) -> None:
        """Initialize the memory store implementation.

        Args:
            storage: JsonStorage instance for persistence
        """
        self.storage = storage
        self._memory_service = MemoryService(storage)
        self._statistics_service = StatisticsService(self._memory_service)

    def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry.

        Args:
            entry: MemoryEntry (ResultEntry or ErrorEntry) to store

        Raises:
            IOError: If the entry cannot be persisted
        """
        self._memory_service.store(entry)

    def retrieve(self) -> list[MemoryEntry]:
        """Retrieve all stored memory entries.

        Returns:
            List of MemoryEntry objects (ResultEntry or ErrorEntry)
        """
        return self._memory_service.retrieve()

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
        return self._memory_service.filter_entries(operation=operation, state=state)

    def get_valid_operations(self) -> list[str]:
        """Get all unique operation types present in stored entries.

        Returns:
            Sorted list of unique operation names
        """
        return self._memory_service.get_valid_operations()

    def export_history(self, filepath: str | Path) -> None:
        """Export all memory entries to a JSON file.

        Args:
            filepath: Path to the output JSON file

        Raises:
            IOError: If the file cannot be written
        """
        self._memory_service.export_history(filepath)

    def import_history(
        self,
        filepath: str | Path,
        overwrite: bool = False,
    ) -> tuple[int, list[str]]:
        """Import memory entries from a JSON file.

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
        return self._memory_service.import_history(filepath, overwrite=overwrite)

    def get_statistics(self) -> dict:
        """Compute and return statistics over stored entries.

        Returns:
            A dictionary containing:
            - operation_counts: dict of operation -> count
            - total_errors: int
            - error_rate_percentage: float
            - average_execution_time_ms: float
        """
        stats = self._statistics_service.compute_statistics()
        return {
            "operation_counts": stats.operation_counts,
            "total_errors": stats.total_errors,
            "error_rate_percentage": stats.error_rate_percentage,
            "average_execution_time_ms": stats.average_execution_time_ms,
        }

    # ---- Convenience methods for backward compatibility ----

    def get_memory_service(self) -> MemoryService:
        """Get the underlying MemoryService for direct access if needed.

        Returns:
            The MemoryService instance
        """
        return self._memory_service

    def get_statistics_service(self) -> StatisticsService:
        """Get the underlying StatisticsService for direct access if needed.

        Returns:
            The StatisticsService instance
        """
        return self._statistics_service
