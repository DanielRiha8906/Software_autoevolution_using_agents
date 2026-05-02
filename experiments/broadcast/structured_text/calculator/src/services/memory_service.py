from ..models.memory_entry import MemoryEntry
from ..storage.memory_entry_storage import MemoryEntryStorage


class MemoryService:
    """Service for managing MemoryEntry lifecycle and retrieval."""

    def __init__(self, storage: MemoryEntryStorage) -> None:
        """Initialize with a MemoryEntry storage dependency."""
        self.storage = storage

    def store(self, entry: MemoryEntry) -> None:
        """Store a single MemoryEntry."""
        self.storage.save(entry)

    def get_all(self) -> list[MemoryEntry]:
        """Retrieve all stored MemoryEntry objects."""
        return self.storage.load_all()

    def retrieve_all(self) -> list[MemoryEntry]:
        """Alias for get_all() for API flexibility."""
        return self.get_all()
