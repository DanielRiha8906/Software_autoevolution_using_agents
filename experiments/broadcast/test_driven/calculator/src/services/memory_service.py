from ..models.memory_entry import MemoryEntry


class MemoryService:
    """In-memory storage service for MemoryEntry objects.

    Manages the lifecycle of memory entries without any file I/O or serialization.
    File I/O and serialization belong in a separate storage layer.
    """

    def __init__(self) -> None:
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
