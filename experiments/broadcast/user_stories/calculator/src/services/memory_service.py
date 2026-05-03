"""MemoryService handles the lifecycle of memory entries.

This service provides a clean separation of concerns by:
- Handling store() and retrieve() operations for memory entries
- Delegating persistence to the storage layer (JsonStorage)
- Maintaining no business logic - only entry management
"""

from ..models.memory_entry import MemoryEntry
from ..storage.json_storage import JsonStorage


class MemoryService:
    """Service for managing calculator operation memory (history).

    Separates memory entry management from persistence details.
    All persistence is delegated to JsonStorage.
    """

    def __init__(self, storage: JsonStorage) -> None:
        """Initialize with a storage backend.

        Args:
            storage: JsonStorage instance handling persistence
        """
        self.storage = storage

    def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry via the storage layer.

        Args:
            entry: MemoryEntry (ResultEntry or ErrorEntry) to store
        """
        self.storage.save(entry)

    def retrieve(self) -> list[MemoryEntry]:
        """Retrieve all stored memory entries.

        Returns:
            List of MemoryEntry objects (ResultEntry or ErrorEntry)
        """
        return self.storage.load_memory_all()
