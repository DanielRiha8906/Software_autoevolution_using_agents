from typing import Protocol


class StoragePort(Protocol):
    """Protocol defining the storage interface that repositories depend on."""

    def load(self) -> list[dict]:
        """Load all task dictionaries from storage.

        Returns:
            List of task dictionaries
        """
        ...

    def save(self, tasks: list[dict]) -> None:
        """Save all task dictionaries to storage.

        Args:
            tasks: List of task dictionaries to persist
        """
        ...
