from src.models.statistics_report import StatisticsReport
from src.services.memory_service import MemoryService


class StatisticsService:
    """Service for computing statistics on memory entries."""

    def __init__(self, memory: MemoryService) -> None:
        self.memory = memory

    def compute(self) -> StatisticsReport:
        """Compute statistics from all memory entries.

        Returns:
            StatisticsReport with aggregated metrics. Returns all zeros if no entries.
        """
        entries = self.memory.retrieve()

        if not entries:
            return StatisticsReport(
                count_per_operation={},
                total_errors=0,
                error_rate=0.0,
                avg_execution_time_ms=0.0,
            )

        # Build count_per_operation
        count_per_operation: dict[str, int] = {}
        for entry in entries:
            count_per_operation[entry.operation] = count_per_operation.get(entry.operation, 0) + 1

        # Count errors and execution times
        total_errors = sum(1 for entry in entries if not entry.success)
        total_execution_time = sum(entry.execution_time_ms for entry in entries)
        total_entries = len(entries)

        # Calculate error_rate and avg_execution_time_ms
        error_rate = (total_errors / total_entries) * 100 if total_entries > 0 else 0.0
        avg_execution_time_ms = (total_execution_time / total_entries) if total_entries > 0 else 0.0

        return StatisticsReport(
            count_per_operation=count_per_operation,
            total_errors=total_errors,
            error_rate=error_rate,
            avg_execution_time_ms=avg_execution_time_ms,
        )
