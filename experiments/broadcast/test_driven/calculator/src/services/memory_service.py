"""Memory service - in-memory history management.

This module provides in-memory storage for memory entries, implementing
the MemoryManager protocol and decoupled from file I/O concerns.
"""

from typing import Optional

from ..models.memory_entry import MemoryEntry


class MemoryService:
    """In-memory storage service for MemoryEntry objects.

    Manages the lifecycle of memory entries without any file I/O or serialization.
    File I/O and serialization belong in a separate storage layer.

    This service implements the history/memory management component,
    keeping memory operations separate from persistence concerns.
    """

    def __init__(self) -> None:
        """Initialize with an empty list of entries."""
        self._entries: list[MemoryEntry] = []

    def store(self, entry: MemoryEntry) -> None:
        """Store a MemoryEntry in memory.

        Args:
            entry: The MemoryEntry to store.
        """
        self._entries.append(entry)

    def retrieve(self) -> list[MemoryEntry]:
        """Retrieve all stored MemoryEntry objects.

        Returns:
            A list of all stored MemoryEntry objects.
        """
        return self._entries

    def query(
        self, operation: Optional[str] = None, success: Optional[bool] = None
    ) -> list[MemoryEntry]:
        """Query stored entries by operation type and/or success state.

        Filters are applied with AND logic. If no filters are provided,
        returns all stored entries.

        Args:
            operation: Filter by operation type (e.g., "add", "multiply").
                       If None, operation filter is not applied.
            success: Filter by success state. If None, success filter is not applied.

        Returns:
            A list of MemoryEntry objects matching the filter criteria.
            Returns an empty list if no entries match.
        """
        results = self._entries

        if operation is not None:
            results = [e for e in results if e.operation == operation]

        if success is not None:
            results = [e for e in results if e.success == success]

        return results
