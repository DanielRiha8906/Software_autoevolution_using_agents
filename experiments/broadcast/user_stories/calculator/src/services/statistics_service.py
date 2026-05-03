"""StatisticsService computes usage and error metrics from stored MemoryEntry data.

This service derives all statistics exclusively from MemoryEntry objects,
providing a structured Statistics dataclass output suitable for programmatic analysis.
"""

from ..models.statistics import Statistics
from ..models.memory_entry import MemoryEntry
from .memory_service import MemoryService


class StatisticsService:
    """Service for computing statistics from calculator operation memory.

    Computes operation counts, error metrics, and performance metrics
    from stored MemoryEntry objects (both ResultEntry and ErrorEntry).
    """

    def __init__(self, memory_service: MemoryService) -> None:
        """Initialize with a MemoryService instance.

        Args:
            memory_service: MemoryService providing access to stored entries
        """
        self.memory_service = memory_service

    def compute_statistics(self) -> Statistics:
        """Compute statistics from all stored memory entries.

        Returns:
            Statistics dataclass containing:
            - operation_counts: dict mapping operation names to count
            - total_errors: number of ErrorEntry instances
            - error_rate_percentage: (total_errors / total_entries) * 100
            - average_execution_time_ms: mean execution_time_ms across all entries

        If no entries exist, returns Statistics with zero values.
        """
        entries = self.memory_service.retrieve()

        if not entries:
            return Statistics()

        # Count operations and errors
        operation_counts: dict[str, int] = {}
        total_errors = 0
        total_execution_time_ms = 0.0

        for entry in entries:
            # Count by operation
            op = entry.operation
            operation_counts[op] = operation_counts.get(op, 0) + 1

            # Count errors
            if entry.is_error():
                total_errors += 1

            # Accumulate execution time
            total_execution_time_ms += entry.execution_time_ms

        # Compute averages
        total_entries = len(entries)
        error_rate_percentage = (total_errors / total_entries * 100.0) if total_entries > 0 else 0.0
        average_execution_time_ms = total_execution_time_ms / total_entries if total_entries > 0 else 0.0

        return Statistics(
            operation_counts=operation_counts,
            total_errors=total_errors,
            error_rate_percentage=error_rate_percentage,
            average_execution_time_ms=average_execution_time_ms,
        )
