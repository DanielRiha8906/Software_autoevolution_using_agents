"""Memory management and history tracking abstraction.

This module provides a protocol-based interface for managing calculation
history and memory entries, decoupled from storage implementation details.
"""

from typing import Protocol, Optional

from ..models.memory_entry import MemoryEntry


class MemoryManager(Protocol):
    """Protocol for memory management operations.

    Any implementation must support storing entries, retrieving them,
    and querying by operation type and success state.
    """

    def store(self, entry: MemoryEntry) -> None:
        """Store a MemoryEntry in memory."""
        ...

    def retrieve(self) -> list[MemoryEntry]:
        """Retrieve all stored MemoryEntry objects."""
        ...

    def query(
        self, operation: Optional[str] = None, success: Optional[bool] = None
    ) -> list[MemoryEntry]:
        """Query stored entries by operation type and/or success state."""
        ...
