from dataclasses import dataclass

from .memory_service import MemoryService


@dataclass
class StatisticsReport:
    """Report containing aggregated statistics from MemoryEntry history.

    Attributes:
        count_per_operation: Dict mapping operation names to their occurrence counts.
        total_errors: Number of failed entries (where success=False).
        error_rate: Percentage of failed entries (0-100).
        avg_execution_time_ms: Mean execution time across all entries.
    """
    count_per_operation: dict[str, int]
    total_errors: int
    error_rate: float
    avg_execution_time_ms: float


class StatisticsService:
    """Service to compute aggregated statistics from MemoryEntry history."""

    def __init__(self, memory_service: MemoryService) -> None:
        """Initialize StatisticsService with a MemoryService.

        Args:
            memory_service: The MemoryService containing entries to analyze.
        """
        self.memory_service = memory_service

    def compute(self) -> StatisticsReport:
        """Compute statistics from stored MemoryEntry objects.

        Returns:
            StatisticsReport containing aggregated metrics.
        """
        entries = self.memory_service.retrieve()

        if not entries:
            return StatisticsReport(
                count_per_operation={},
                total_errors=0,
                error_rate=0.0,
                avg_execution_time_ms=0.0
            )

        # Count operations by type
        count_per_operation: dict[str, int] = {}
        for entry in entries:
            count_per_operation[entry.operation] = count_per_operation.get(entry.operation, 0) + 1

        # Count errors
        total_errors = sum(1 for entry in entries if not entry.success)

        # Compute error rate as percentage
        error_rate = (total_errors / len(entries)) * 100 if entries else 0.0

        # Compute average execution time
        avg_execution_time_ms = (
            sum(entry.execution_time_ms for entry in entries) / len(entries)
            if entries
            else 0.0
        )

        return StatisticsReport(
            count_per_operation=count_per_operation,
            total_errors=total_errors,
            error_rate=error_rate,
            avg_execution_time_ms=avg_execution_time_ms
        )
