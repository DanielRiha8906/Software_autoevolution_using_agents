from typing import TYPE_CHECKING

from ..models.calculation_statistics import CalculationStatistics

if TYPE_CHECKING:
    from .memory_service import MemoryService


class StatisticsService:
    def __init__(self, memory_service: "MemoryService") -> None:
        self.memory_service = memory_service

    def generate(self) -> CalculationStatistics:
        """Generate statistics from all recorded calculations.

        Returns:
            CalculationStatistics with operation counts, error rate, and execution time metrics.
        """
        entries = self.memory_service.get_all_entries()

        # Initialize operation counts for all 14 operations
        operation_counts: dict[str, int] = {
            "add": 0,
            "subtract": 0,
            "multiply": 0,
            "divide": 0,
            "square": 0,
            "sqrt": 0,
            "power": 0,
            "modulo": 0,
            "sin": 0,
            "cos": 0,
            "tan": 0,
            "log": 0,
            "ln": 0,
            "exp": 0,
        }

        total_errors = 0
        total_execution_time = 0.0

        for entry in entries:
            # Count operations
            operation_counts[entry.operation_name] += 1

            # Count errors
            if not entry.success:
                total_errors += 1

            # Accumulate execution time
            total_execution_time += entry.execution_time_ms

        # Calculate error rate
        total_operations = len(entries)
        error_rate = (total_errors / total_operations * 100) if total_operations > 0 else 0.0

        # Calculate average execution time
        avg_execution_time = (total_execution_time / total_operations) if total_operations > 0 else 0.0

        return CalculationStatistics(
            operation_counts=operation_counts,
            total_errors=total_errors,
            error_rate=error_rate,
            avg_execution_time_ms=avg_execution_time,
        )
