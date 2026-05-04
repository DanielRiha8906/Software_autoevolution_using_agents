"""
Abstract protocols defining component interfaces.

This module provides type-safe contracts for service and storage components,
enabling loose coupling and facilitating testing through mockable interfaces.
"""

from typing import Generic, TypeVar, Protocol, List, Tuple

from ..models.operation import Operation
from ..models.calculation_result import CalculationResult
from ..models.memory_entry import MemoryEntry
from ..models.calculation_statistics import CalculationStatistics
from pathlib import Path


T = TypeVar("T")


class Storage(Protocol, Generic[T]):
    """
    Abstract protocol for persistent storage of objects.

    Defines a generic interface for append-only JSON persistence,
    supporting both CalculationResult and MemoryEntry types.
    """

    def save(self, entry: T) -> None:
        """
        Persist a single entry to storage (append-only).

        Args:
            entry: Object to persist.

        Raises:
            OSError: If file I/O fails.
        """
        ...

    def load_all(self) -> List[T]:
        """
        Load all stored entries from persistent storage.

        Returns:
            List of all entries in storage. Returns empty list if storage
            is empty or does not exist.
        """
        ...


class CalculationService(Protocol):
    """
    Abstract protocol for calculation orchestration.

    Defines the contract for performing calculations, managing timing,
    and persisting results. Implementations handle the full lifecycle
    of a single calculation attempt.
    """

    def perform(
        self, operation: Operation, a: float, b: float
    ) -> CalculationResult:
        """
        Execute a calculation and persist the result.

        Measures execution time, creates a CalculationResult, and
        saves it to persistent storage.

        Args:
            operation: The Operation enum value to perform.
            a: First operand (float).
            b: Second operand (float).

        Returns:
            CalculationResult with operation, operands, result, and timing.

        Raises:
            ValueError: If calculation fails (e.g., division by zero,
                       invalid input for domain-restricted operations).
        """
        ...

    def get_history(self) -> List[CalculationResult]:
        """
        Retrieve the complete calculation history.

        Returns:
            List of all CalculationResult entries in persistent storage.
            Returns empty list if no history exists.
        """
        ...


class MemoryService(Protocol):
    """
    Abstract protocol for memory (audit trail) management.

    Defines the contract for storing, querying, and analyzing calculation
    attempts. Unlike CalculationService (which only records successes),
    MemoryService captures both successful and failed attempts.
    """

    def store(self, entry: MemoryEntry) -> None:
        """
        Store a MemoryEntry representing a calculation attempt.

        Args:
            entry: MemoryEntry object to persist (may represent success or failure).
        """
        ...

    def retrieve_all(self) -> List[MemoryEntry]:
        """
        Retrieve all stored MemoryEntry objects.

        Returns:
            List of all entries in storage, in insertion order.
            Returns empty list if no entries exist.
        """
        ...

    def filter_by_operation(self, operation_name: str) -> List[MemoryEntry]:
        """
        Filter memory entries by operation name (case-insensitive).

        Args:
            operation_name: Name of the operation to filter by (e.g., "add", "sqrt").
                           Comparison is case-insensitive.

        Returns:
            List of matching entries in insertion order.
            Returns empty list if no matches found.
        """
        ...

    def filter_by_success(self, success: bool) -> List[MemoryEntry]:
        """
        Filter memory entries by success/failure status.

        Args:
            success: True to return only successful calculations,
                     False to return only failed calculations.

        Returns:
            List of matching entries in insertion order.
            Returns empty list if no matches found.
        """
        ...

    def filter_by_execution_time(
        self, min_ms: float = 0.0, max_ms: float = float("inf")
    ) -> List[MemoryEntry]:
        """
        Filter memory entries by execution time range (milliseconds).

        Args:
            min_ms: Minimum execution time (inclusive). Defaults to 0.0.
            max_ms: Maximum execution time (inclusive). Defaults to infinity.

        Returns:
            List of entries with execution_time_ms in [min_ms, max_ms],
            in insertion order. Returns empty list if no matches found.
        """
        ...

    def compute_statistics(self) -> CalculationStatistics:
        """
        Compute and return aggregated statistics over all MemoryEntry objects.

        Returns:
            CalculationStatistics with operation counts, error metrics,
            execution time metrics, and per-operation breakdowns.
        """
        ...

    def export_to_file(self, filepath: Path | str) -> int:
        """
        Export all memory entries to a JSON file.

        Args:
            filepath: Destination file path (parent directories auto-created).

        Returns:
            Count of entries exported.

        Raises:
            OSError: If file cannot be written.
        """
        ...

    def import_from_file(
        self, filepath: Path | str, skip_invalid: bool = False
    ) -> Tuple[int, List[dict]]:
        """
        Import memory entries from a JSON file and append to storage.

        Args:
            filepath: Source JSON file path (must be valid JSON array).
            skip_invalid: If True, skip malformed entries and continue.
                         If False, raise on first invalid entry.

        Returns:
            Tuple of (count_imported, list_of_skipped_entries).
            Each skipped entry is a dict with "data" and "error" keys.

        Raises:
            FileNotFoundError: If file does not exist.
            json.JSONDecodeError: If JSON is malformed and skip_invalid=False.
            ValueError: If JSON is not an array, or on first invalid entry.
        """
        ...


__all__ = [
    "Storage",
    "CalculationService",
    "MemoryService",
]
