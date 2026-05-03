from collections import Counter

from ..models.statistics import CalculationStatistics
from .memory_service import MemoryService


class StatisticsService:
    """Computes statistics from stored calculation history."""

    def __init__(self, memory_service: MemoryService) -> None:
        self.memory_service = memory_service

    def calculate_statistics(self) -> CalculationStatistics:
        """Calculate statistics from all stored calculation entries.

        Returns:
            CalculationStatistics dataclass with aggregated metrics.
        """
        entries = self.memory_service.retrieve()

        # Handle empty list case
        if not entries:
            return CalculationStatistics(
                total_calculations=0,
                total_errors=0,
                error_rate_percent=0.0,
                operations_count={},
                average_execution_time_ms=0.0,
            )

        # Count total calculations and errors
        total_calculations = len(entries)
        total_errors = sum(1 for entry in entries if entry.error is not None)

        # Calculate error rate as percentage, rounded to 2 decimals
        error_rate_percent = round((total_errors / total_calculations) * 100, 2)

        # Count operations using Counter
        operations_count = dict(Counter(entry.operation for entry in entries))

        # Calculate average execution time, rounded to 6 decimals
        total_execution_time = sum(entry.execution_time_ms for entry in entries)
        average_execution_time_ms = round(total_execution_time / total_calculations, 6)

        return CalculationStatistics(
            total_calculations=total_calculations,
            total_errors=total_errors,
            error_rate_percent=error_rate_percent,
            operations_count=operations_count,
            average_execution_time_ms=average_execution_time_ms,
        )
