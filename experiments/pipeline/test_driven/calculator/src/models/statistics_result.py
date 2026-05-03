from dataclasses import dataclass


@dataclass
class StatisticsResult:
    """Dataclass holding aggregated statistics from MemoryEntry history.

    Fields capture operation counts, error metrics, and performance data
    computed from a collection of MemoryEntry objects.

    Attributes:
        count_per_operation: Dictionary mapping operation names (str) to the count
                            of entries for that operation (int).
        total_errors: Total count of entries where success=False.
        error_rate: Percentage of failed operations on 0-100 scale.
                   Calculated as (total_errors / total_entries) * 100.
        avg_execution_time_ms: Average execution time in milliseconds across all entries.
    """
    count_per_operation: dict[str, int]
    total_errors: int
    error_rate: float
    avg_execution_time_ms: float
