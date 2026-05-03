"""FilterService provides filtering capabilities for memory entries.

This service enables programmatic filtering of stored calculations by:
- Operation type (e.g., 'add', 'subtract', 'multiply', 'divide')
- Result state ('success' or 'error')
- Combining multiple filters in a single query
"""

from typing import Optional
from ..models.memory_entry import MemoryEntry, ResultEntry, ErrorEntry


class FilterService:
    """Service for filtering memory entries by operation and result state.

    Performs in-memory filtering on loaded memory entries without indexing.
    """

    def __init__(self) -> None:
        """Initialize the filter service."""
        pass

    def filter_entries(
        self,
        entries: list[MemoryEntry],
        operation: Optional[str] = None,
        state: Optional[str] = None,
    ) -> list[MemoryEntry]:
        """Filter memory entries by operation type and/or result state.

        Args:
            entries: List of MemoryEntry objects to filter
            operation: Operation type to filter by (e.g., 'add', 'subtract')
                      None means no operation filter
            state: Result state to filter by ('success' or 'error')
                  None means no state filter

        Returns:
            List of MemoryEntry objects matching all specified criteria

        Raises:
            ValueError: If state is not 'success', 'error', or None
        """
        if state is not None and state not in ("success", "error"):
            raise ValueError(f"Invalid state: '{state}'. Must be 'success' or 'error'.")

        result = entries

        # Filter by operation if specified
        if operation is not None:
            result = [e for e in result if e.operation == operation]

        # Filter by state if specified
        if state is not None:
            if state == "success":
                result = [e for e in result if isinstance(e, ResultEntry)]
            elif state == "error":
                result = [e for e in result if isinstance(e, ErrorEntry)]

        return result

    def get_valid_operations(self, entries: list[MemoryEntry]) -> list[str]:
        """Get all unique operation types present in entries.

        Args:
            entries: List of MemoryEntry objects

        Returns:
            Sorted list of unique operation names
        """
        operations = set(e.operation for e in entries if e.operation)
        return sorted(operations)
