from ..models.memory_entry import MemoryEntry
from ..storage.json_storage import JsonStorage


class MemoryService:
    """Service for managing MemoryEntry objects.

    Responsibilities:
    - Store MemoryEntry objects via the storage backend
    - Retrieve stored MemoryEntry objects

    Storage (file I/O, persistence) is delegated to JsonStorage.
    """

    def __init__(self, storage: JsonStorage) -> None:
        """Initialize MemoryService with a storage backend.

        Args:
            storage: JsonStorage instance for persisting MemoryEntry objects.
        """
        self.storage = storage

    def store(self, entry: MemoryEntry) -> None:
        """Store a MemoryEntry.

        Args:
            entry: MemoryEntry object to store.
        """
        self.storage.save(entry)

    def retrieve(self) -> list[MemoryEntry]:
        """Retrieve all stored MemoryEntry objects.

        Returns:
            List of MemoryEntry objects, ordered by storage.
        """
        return self.storage.load_all()
