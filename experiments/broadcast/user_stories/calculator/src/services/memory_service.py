from ..models.memory_entry import MemoryEntry


class MemoryService:
    """
    Manages the lifecycle of MemoryEntry objects.

    Provides operations for storing and retrieving calculation history entries
    without handling persistence details. Persistence is delegated to a separate
    storage layer.
    """

    def __init__(self) -> None:
        """Initialize the memory service with an empty in-memory store."""
        self._entries: list[MemoryEntry] = []

    def store(self, entry: MemoryEntry) -> None:
        """
        Store a MemoryEntry in the service.

        Args:
            entry: A MemoryEntry object representing a calculation attempt.
        """
        self._entries.append(entry)

    def retrieve(self) -> list[MemoryEntry]:
        """
        Retrieve all stored MemoryEntry objects.

        Returns:
            A list of all MemoryEntry objects stored in the service.
        """
        return list(self._entries)

    def clear(self) -> None:
        """Clear all stored entries from the service."""
        self._entries.clear()

    def count(self) -> int:
        """
        Get the number of stored entries.

        Returns:
            The total count of MemoryEntry objects in the service.
        """
        return len(self._entries)
