from abc import ABC, abstractmethod

from ..models.memory_entry import MemoryEntry


class StorageBackend(ABC):
    """Abstract interface for storage backends.

    Defines the contract for persisting and retrieving MemoryEntry objects.
    Allows different storage implementations (JSON file, database, cloud, etc.)
    without changing dependent code.
    """

    @abstractmethod
    def save(self, entry: MemoryEntry) -> None:
        """Persist a single entry.

        Args:
            entry: MemoryEntry to save.
        """

    @abstractmethod
    def load_all(self) -> list[MemoryEntry]:
        """Load all entries.

        Returns:
            List of all stored MemoryEntry objects.
        """

    @abstractmethod
    def save_all(self, entries: list[MemoryEntry]) -> None:
        """Persist multiple entries (for bulk operations like clear/replace).

        Args:
            entries: List of MemoryEntry objects to save (overwrites existing).
        """
