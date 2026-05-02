from typing import List, Optional
from ..models.memory_entry import MemoryEntry
from ..storage.memory_storage import MemoryEntryStorage


class MemoryService:
    """
    Service for managing MemoryEntry objects.

    Handles storing and retrieving MemoryEntry objects in an in-memory collection
    with optional persistence to a storage backend.
    """

    def __init__(self, storage: Optional[MemoryEntryStorage] = None) -> None:
        """
        Initialize MemoryService.

        Args:
            storage: Optional storage backend for persisting MemoryEntry objects.
                    If None, entries are stored only in memory.
        """
        self._entries: List[MemoryEntry] = []
        self._storage: Optional[MemoryEntryStorage] = storage

    def store(self, entry: MemoryEntry) -> None:
        """
        Store a MemoryEntry in memory and optionally persist it.

        Args:
            entry: MemoryEntry object to store.

        Raises:
            TypeError: If entry is not a MemoryEntry instance.
        """
        if not isinstance(entry, MemoryEntry):
            raise TypeError(f"entry must be a MemoryEntry instance, got {type(entry).__name__}")
        self._entries.append(entry)
        if self._storage is not None:
            self._storage.save(entry)

    def retrieve(self) -> List[MemoryEntry]:
        """
        Retrieve all stored MemoryEntry objects.

        Returns:
            List of all MemoryEntry objects stored in this service.
            Returns empty list if no entries have been stored.
        """
        return self._entries
