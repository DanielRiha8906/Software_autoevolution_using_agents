"""Base repository class defining the interface for all repositories."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar, Generic, List, Dict

from ..storage.json_storage import JsonStorage

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base class for all repositories.

    Defines common CRUD operations and persistence patterns.
    """

    def __init__(self, storage_path: Path) -> None:
        """Initialize repository with storage.

        Args:
            storage_path: Path to the JSON storage file
        """
        self._storage = JsonStorage(str(storage_path))
        self._items: Dict[str, T] = {}
        self._load()

    @abstractmethod
    def _deserialize(self, data: dict) -> T:
        """Deserialize a dict to a domain object.

        Args:
            data: Dictionary representation of the object

        Returns:
            Domain object instance
        """
        pass

    @abstractmethod
    def _serialize(self, item: T) -> dict:
        """Serialize a domain object to a dict.

        Args:
            item: Domain object instance

        Returns:
            Dictionary representation of the object
        """
        pass

    def _load(self) -> None:
        """Load all items from storage into memory."""
        raw = self._storage.load()
        self._items = {d["id"]: self._deserialize(d) for d in raw}

    def _persist(self) -> None:
        """Persist all items to storage."""
        self._storage.save([self._serialize(item) for item in self._items.values()])

    def get(self, item_id: str) -> T:
        """Retrieve an item by ID or unique prefix.

        Args:
            item_id: Full ID or unique prefix (first N characters)

        Returns:
            The domain object

        Raises:
            RepositoryError: If item not found or prefix is ambiguous
        """
        # Check for exact match first
        if item_id in self._items:
            return self._items[item_id]

        # Support short prefix lookup (e.g. first 8 chars)
        matches = [item for iid, item in self._items.items() if iid.startswith(item_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise self._item_not_found(f"Ambiguous prefix '{item_id}' matches {len(matches)} items")
        raise self._item_not_found(f"Item '{item_id}' not found")

    def list_all(self) -> List[T]:
        """List all items.

        Returns:
            List of all domain objects
        """
        return list(self._items.values())

    def delete(self, item_id: str) -> None:
        """Delete an item by ID or unique prefix.

        Args:
            item_id: Full ID or unique prefix

        Raises:
            RepositoryError: If item not found or prefix is ambiguous
        """
        item = self.get(item_id)  # Resolves prefix and validates existence
        del self._items[item.id]
        self._persist()

    @abstractmethod
    def _item_not_found(self, message: str) -> Exception:
        """Create an appropriate "not found" exception for this repository.

        Args:
            message: Error message

        Returns:
            Exception instance
        """
        pass
