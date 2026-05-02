from abc import ABC, abstractmethod
from typing import List
from ..models.memory_entry import MemoryEntry


class MemoryEntryStorage(ABC):
    """
    Abstract base class for MemoryEntry persistence.

    Defines the interface for storing and loading MemoryEntry objects
    from persistent storage (file, database, etc.).
    """

    @abstractmethod
    def save(self, entry: MemoryEntry) -> None:
        """
        Persist a single MemoryEntry to storage.

        Args:
            entry: MemoryEntry object to persist.
        """

    @abstractmethod
    def load_all(self) -> List[MemoryEntry]:
        """
        Load all MemoryEntry objects from persistent storage.

        Returns:
            List of MemoryEntry objects loaded from storage.
            Returns empty list if no entries exist in storage.
        """
