"""
Memory/History Store Layer - Data Persistence Interface

This module defines the structural interface for the memory store layer using
Python typing.Protocol, which handles all persistence, history, filtering, and
statistics operations. The memory store is responsible for managing the lifecycle
of calculation entries without concern for the calculation engine itself.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Protocol
from ..models.memory_entry import MemoryEntry

if TYPE_CHECKING:
    from .memory_service import MemoryService


class MemoryStore(Protocol):
    """Protocol for the memory/history store layer.

    The memory store is responsible for:
    - Saving and retrieving calculation entries (results and errors)
    - Filtering entries by operation type and state
    - Computing statistics over stored entries
    - Exporting and importing history to/from files
    - Maintaining entry IDs and timestamps

    It does NOT:
    - Perform any calculations
    - Define business logic for operations
    - Interact with the calculation engine

    Any implementation must provide all these methods.
    """

    def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry.

        Args:
            entry: MemoryEntry (ResultEntry or ErrorEntry) to store

        Raises:
            IOError: If the entry cannot be persisted
        """
        ...

    def retrieve(self) -> list[MemoryEntry]:
        """Retrieve all stored memory entries.

        Returns:
            List of MemoryEntry objects (ResultEntry or ErrorEntry)
        """
        ...

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
        ...

    def get_valid_operations(self) -> list[str]:
        """Get all unique operation types present in stored entries.

        Returns:
            Sorted list of unique operation names
        """
        ...

    def export_history(self, filepath: str | Path) -> None:
        """Export all memory entries to a JSON file.

        Args:
            filepath: Path to the output JSON file

        Raises:
            IOError: If the file cannot be written
        """
        ...

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
        ...

    def get_statistics(self) -> dict:
        """Compute and return statistics over stored entries.

        Returns:
            A dictionary containing:
            - operation_counts: dict of operation -> count
            - total_errors: int
            - error_rate_percentage: float
            - average_execution_time_ms: float
        """
        ...

    def get_memory_service(self) -> "MemoryService":
        """Return the underlying memory service for backward compatibility.

        Returns:
            The MemoryService instance
        """
        ...
