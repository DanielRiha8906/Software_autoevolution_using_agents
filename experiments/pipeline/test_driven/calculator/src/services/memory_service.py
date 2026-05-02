from ..models.memory_entry import MemoryEntry


class MemoryService:
    """Service for managing in-memory storage of MemoryEntry objects."""

    def __init__(self) -> None:
        """Initialize with empty in-memory list."""
        self.entries: list[MemoryEntry] = []

    def store(self, entry: MemoryEntry) -> None:
        """Store a MemoryEntry in memory.

        Args:
            entry: The MemoryEntry to store

        Returns:
            None
        """
        self.entries.append(entry)

    def retrieve(self) -> list[MemoryEntry]:
        """Retrieve all stored MemoryEntry objects.

        Returns:
            A new list containing all stored entries in insertion order.
            Returns an empty list if no entries have been stored.
        """
        return list(self.entries)
