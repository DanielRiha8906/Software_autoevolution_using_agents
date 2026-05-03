from ..models.memory_entry import MemoryEntry
from ..storage.memory_json_storage import MemoryJsonStorage


class MemoryService:
    """
    Manages the lifecycle of MemoryEntry objects.

    Coordinates storage and retrieval of calculation memory entries,
    delegating persistence to MemoryJsonStorage. Provides a clean
    separation between service logic and storage implementation.
    """

    def __init__(self, storage: MemoryJsonStorage) -> None:
        """
        Initialize the memory service with a storage backend.

        Args:
            storage: MemoryJsonStorage instance for persisting entries.
        """
        self.storage = storage

    def store(self, entry: MemoryEntry) -> None:
        """
        Store a MemoryEntry in persistent storage.

        Args:
            entry: MemoryEntry object to persist.
        """
        self.storage.save(entry)

    def retrieve_all(self) -> list[MemoryEntry]:
        """
        Retrieve all stored MemoryEntry objects.

        Returns:
            List of all MemoryEntry objects in storage. Returns empty
            list if no entries have been stored or storage is empty.
        """
        return self.storage.load_all()
