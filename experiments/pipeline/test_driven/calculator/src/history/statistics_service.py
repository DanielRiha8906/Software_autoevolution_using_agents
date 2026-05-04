from ..models.statistics_result import StatisticsResult
from .interfaces import MemoryBackend


class StatisticsService:
    """Service for computing aggregated metrics from MemoryEntry history.

    Takes a MemoryService instance and computes statistics by analyzing
    all stored entries. Computations are performed on-demand via compute().
    """

    def __init__(self, memory_service: MemoryBackend) -> None:
        """Initialize StatisticsService with a MemoryService instance.

        Args:
            memory_service: A MemoryService instance to compute statistics from.
        """
        self._memory_service = memory_service

    def compute(self) -> StatisticsResult:
        """Compute aggregated statistics from all stored MemoryEntry objects.

        Retrieves all entries from the MemoryService and computes:
        - count_per_operation: Dictionary mapping operation names to their counts
        - total_errors: Count of entries with success=False
        - error_rate: Percentage of failed operations (0-100 scale)
        - avg_execution_time_ms: Mean execution time across all entries

        Returns:
            StatisticsResult: Dataclass containing computed statistics.

        Behavior:
            - Empty MemoryService: Returns counts of 0, error_rate of 0.0, avg_time of 0.0
            - No errors: error_rate = 0.0
            - All errors: error_rate = 100.0
            - Does not modify MemoryService state
            - Does not perform file I/O
        """
        entries = self._memory_service.retrieve()

        # Handle empty MemoryService
        if not entries:
            return StatisticsResult(
                count_per_operation={},
                total_errors=0,
                error_rate=0.0,
                avg_execution_time_ms=0.0
            )

        # Count operations
        count_per_operation: dict[str, int] = {}
        for entry in entries:
            if entry.operation not in count_per_operation:
                count_per_operation[entry.operation] = 0
            count_per_operation[entry.operation] += 1

        # Count errors
        total_errors = sum(1 for entry in entries if not entry.success)

        # Calculate error rate
        error_rate = (total_errors / len(entries)) * 100

        # Calculate average execution time
        total_time = sum(entry.execution_time_ms for entry in entries)
        avg_execution_time_ms = total_time / len(entries)

        return StatisticsResult(
            count_per_operation=count_per_operation,
            total_errors=total_errors,
            error_rate=error_rate,
            avg_execution_time_ms=avg_execution_time_ms
        )
