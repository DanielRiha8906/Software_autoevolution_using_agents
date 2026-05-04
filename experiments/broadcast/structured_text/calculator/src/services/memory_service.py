from typing import TYPE_CHECKING

from ..models.memory_entry import MemoryEntry
from ..storage.json_storage import JsonStorage

if TYPE_CHECKING:
    from ..protocols import HistoryStorage


class MemoryService:
    """Concrete implementation of the HistoryStorage protocol.

    Manages calculation history and memory entries with no knowledge of UI or calculation logic.
    """
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
