from typing import List, Optional
from src.models.memory_entry import MemoryEntry


class MemoryService:
    """Service for managing MemoryEntry lifecycle."""

    def __init__(self) -> None:
        self._entries: List[MemoryEntry] = []

    def store(self, entry: MemoryEntry) -> None:
        """Store a MemoryEntry in memory."""
        self._entries.append(entry)

    def retrieve(self) -> List[MemoryEntry]:
        """Retrieve all stored MemoryEntry objects."""
        return self._entries

    def query(
        self,
        operation: Optional[str] = None,
        success: Optional[bool] = None,
    ) -> List[MemoryEntry]:
        """Query stored entries with optional filtering by operation type and/or success state.

        Args:
            operation: Filter by operation name (e.g., "add", "multiply"). If None, no operation filter.
            success: Filter by success state (True for successful, False for failed). If None, no success filter.

        Returns:
            List of MemoryEntry objects matching the filters. Returns empty list if no matches.
            If no filters provided, returns all entries.
        """
        results = []
        for entry in self._entries:
            # Check operation filter if provided
            if operation is not None and entry.operation != operation:
                continue
            # Check success filter if provided
            if success is not None and entry.success != success:
                continue
            # Entry matches all provided filters
            results.append(entry)
        return results
