from ..models.memory_entry import MemoryEntry
from ..storage.memory_entry_storage import MemoryEntryStorage


class MemoryService:
    """Manages the lifecycle of MemoryEntry objects (store and retrieve)."""

    def __init__(self, storage: MemoryEntryStorage) -> None:
        """Initialize MemoryService with a storage backend.

        Args:
            storage: The storage implementation to use for persisting MemoryEntry objects
        """
        self.storage = storage

    def store(self, entry: MemoryEntry) -> None:
        """Persist a MemoryEntry to storage.

        Args:
            entry: The MemoryEntry object to store
        """
        self.storage.save(entry)

    def get_all(self) -> list[MemoryEntry]:
        """Retrieve all stored MemoryEntry objects.

        Returns:
            A list of all MemoryEntry objects from storage
        """
        return self.storage.load_all()
