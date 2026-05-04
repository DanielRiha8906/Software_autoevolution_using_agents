from typing import Protocol

from ..models.memory_entry import MemoryEntry
from ..models.memory_statistics import MemoryStatistics


class MemoryRepository(Protocol):
    """Protocol for memory service operations.

    This protocol defines the interface that any memory repository implementation
    must follow. It enables decoupling dependent components from the concrete
    MemoryService implementation and supports structural subtyping.
    """

    def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry.

        Args:
            entry: The MemoryEntry to store.
        """
        ...

    def retrieve_all(self) -> list[MemoryEntry]:
        """Retrieve all memory entries.

        Returns:
            List of all MemoryEntry objects.
        """
        ...

    def retrieve_by_id(self, entry_id: str) -> MemoryEntry | None:
        """Retrieve a single memory entry by its ID.

        Args:
            entry_id: The unique identifier of the entry.

        Returns:
            The MemoryEntry if found, None otherwise.
        """
        ...

    def retrieve_by_operation(self, operation: str) -> list[MemoryEntry]:
        """Retrieve all memory entries for a specific operation type.

        Args:
            operation: The operation name (e.g., "add", "divide").

        Returns:
            List of MemoryEntry objects matching the operation.
        """
        ...

    def retrieve_successes(self) -> list[MemoryEntry]:
        """Retrieve all successful memory entries.

        Returns:
            List of MemoryEntry objects where success=True.
        """
        ...

    def retrieve_failures(self) -> list[MemoryEntry]:
        """Retrieve all failed memory entries.

        Returns:
            List of MemoryEntry objects where success=False.
        """
        ...

    def clear(self) -> None:
        """Clear all memory entries."""
        ...

    def count(self) -> int:
        """Get total count of memory entries.

        Returns:
            Number of entries in memory storage.
        """
        ...

    def count_by_status(self) -> dict[str, int]:
        """Get count of entries grouped by status.

        Returns:
            Dictionary with keys "success" and "failure" mapping to counts.
        """
        ...

    def count_by_operation(self) -> dict[str, int]:
        """Get count of entries grouped by operation type.

        Returns:
            Dictionary mapping operation names to counts.
        """
        ...

    def retrieve_by_filter(
        self,
        operation: str | None = None,
        success: bool | None = None
    ) -> list[MemoryEntry]:
        """Retrieve memory entries with optional filtering.

        Args:
            operation: Filter by operation name. If None, no operation filter.
            success: Filter by status. True = successes only, False = failures only, None = all.

        Returns:
            List of MemoryEntry objects matching all non-None filters (AND semantics).
        """
        ...

    def get_operation_error_rates(self) -> dict[str, float]:
        """Calculate error rate (percentage) for each operation type.

        Returns:
            Dictionary mapping operation names to error rates (0-100).
        """
        ...

    def compute_statistics(self, filter_operation: str | None = None) -> MemoryStatistics:
        """Compute aggregated statistics from memory entries.

        Args:
            filter_operation: If provided, compute statistics only for this operation type.
                            If None, compute statistics for all entries.

        Returns:
            MemoryStatistics object with computed values.
        """
        ...
