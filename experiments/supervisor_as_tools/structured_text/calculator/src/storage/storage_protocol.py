from typing import Protocol

from ..models.calculation_result import CalculationResult
from ..models.memory_entry import MemoryEntry


class StorageInterface(Protocol):
    """Protocol for storage backends of CalculationResult objects.

    This protocol defines the interface that any calculation result storage
    implementation must follow. It enables decoupling the CalculatorService
    from specific storage implementations (e.g., JSON, database, etc.).
    """

    def save(self, result: CalculationResult) -> None:
        """Save a calculation result to storage.

        Args:
            result: The CalculationResult to persist.
        """
        ...

    def load_all(self) -> list[CalculationResult]:
        """Load all stored calculation results.

        Returns:
            List of all CalculationResult objects in storage.
            Returns empty list if storage is empty or not initialized.
        """
        ...


class MemoryStorageInterface(Protocol):
    """Protocol for storage backends of MemoryEntry objects.

    This protocol defines the interface that any memory entry storage
    implementation must follow. It enables decoupling the MemoryService
    from specific storage implementations (e.g., JSON, database, etc.).
    """

    def save(self, entry: MemoryEntry) -> None:
        """Save a memory entry to storage.

        Args:
            entry: The MemoryEntry to persist.
        """
        ...

    def load_all(self) -> list[MemoryEntry]:
        """Load all stored memory entries.

        Returns:
            List of all MemoryEntry objects in storage.
            Returns empty list if storage is empty or not initialized.
        """
        ...
