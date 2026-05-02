from ..models.memory_entry import MemoryEntry


class MemoryService:
    """Service for managing in-memory storage of MemoryEntry objects."""

    def __init__(self) -> None:
        """Initialize the MemoryService with an empty in-memory store."""
        self._entries: list[MemoryEntry] = []

    def store(self, entry: MemoryEntry) -> None:
        """
        Store a MemoryEntry in memory.

        Args:
            entry: The MemoryEntry to store.
        """
        self._entries.append(entry)

    def retrieve(self) -> list[MemoryEntry]:
        """
        Retrieve all stored MemoryEntry objects.

        Returns:
            A list of all MemoryEntry objects currently in memory.
        """
        return self._entries
