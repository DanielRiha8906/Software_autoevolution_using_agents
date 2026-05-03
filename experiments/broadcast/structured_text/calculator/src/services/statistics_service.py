"""Service for computing statistics on calculated operations."""

from collections import defaultdict
from ..models.memory_entry import MemoryEntry
from ..models.statistics_report import StatisticsReport
from .memory_service import MemoryService


class StatisticsService:
    """Service for computing operation statistics from MemoryEntry records.

    Computes:
    - Total operation count and per-operation counts
    - Error frequency and overall error rate
    - Average, min, and max execution times
    """

    def __init__(self, memory_service: MemoryService) -> None:
        """Initialize StatisticsService with a MemoryService backend.

        Args:
            memory_service: MemoryService instance containing MemoryEntry objects.
        """
        self.memory_service = memory_service

    def compute_statistics(self) -> StatisticsReport:
        """Compute statistics from all stored MemoryEntry objects.

        Returns:
            StatisticsReport containing operation counts, error rates, and timing stats.
        """
        entries = self.memory_service.retrieve()

        if not entries:
            return StatisticsReport()

        report = StatisticsReport()
        report.total_operations = len(entries)

        operation_count: dict[str, int] = defaultdict(int)
        error_count_by_op: dict[str, int] = defaultdict(int)
        total_execution_time = 0.0
        min_time = float('inf')
        max_time = 0.0

        for entry in entries:
            # Count operations
            operation_count[entry.operation_name] += 1

            # Count errors
            if not entry.success:
                report.total_errors += 1
                error_count_by_op[entry.operation_name] += 1

            # Track execution times
            total_execution_time += entry.execution_time_ms
            min_time = min(min_time, entry.execution_time_ms)
            max_time = max(max_time, entry.execution_time_ms)

        # Set operation counts
        report.operation_count = dict(operation_count)

        # Set error frequency (per-operation error counts)
        report.error_frequency = dict(error_count_by_op)

        # Compute error rate
        if report.total_operations > 0:
            report.error_rate = report.total_errors / report.total_operations
        else:
            report.error_rate = 0.0

        # Compute average execution time
        if report.total_operations > 0:
            report.average_execution_time_ms = total_execution_time / report.total_operations
        else:
            report.average_execution_time_ms = 0.0

        # Set min/max execution times
        report.min_execution_time_ms = min_time if min_time != float('inf') else 0.0
        report.max_execution_time_ms = max_time

        return report
