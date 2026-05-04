from abc import ABC, abstractmethod


class StorageInterface(ABC):
    """Abstract base class defining the contract for storage implementations."""

    @abstractmethod
    def load(self) -> list[dict]:
        """Load data from storage.

        Returns:
            A list of dictionaries representing persisted data.
        """
        pass

    @abstractmethod
    def save(self, data: list[dict]) -> None:
        """Save data to storage.

        Args:
            data: A list of dictionaries to persist.
        """
        pass
