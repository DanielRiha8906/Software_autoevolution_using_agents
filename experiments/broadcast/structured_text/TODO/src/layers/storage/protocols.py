"""Storage protocol definitions for interface-first design."""

from typing import Protocol, Union


class StorageProtocol(Protocol):
    """Protocol defining the storage interface.

    Any storage implementation must conform to this protocol to be used
    with the domain layer services.
    """

    def load(self) -> Union[list[dict], dict]:
        """Load data from storage.

        Returns:
            If the file contains a list of dicts (legacy tasks format),
            returns the list. If it contains a dict with 'tasks' key,
            returns the entire dict. If file doesn't exist, returns empty list.
        """
        ...

    def save(self, data: Union[list[dict], dict]) -> None:
        """Save data to storage.

        Args:
            data: Either a list of task dicts (legacy format) or
                  a dict with 'tasks' and/or 'comments' keys.
        """
        ...
