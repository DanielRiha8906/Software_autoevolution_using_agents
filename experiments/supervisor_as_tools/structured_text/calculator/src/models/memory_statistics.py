from dataclasses import dataclass, field


@dataclass
class MemoryStatistics:
    """
    Aggregated statistics from calculator memory.

    Must fields:
    - operation_counts: Number of calculations per operation type
    - total_errors: Total number of failed calculations
    - error_rate: Percentage of failed calculations (0-100)
    - avg_execution_time_ms: Average execution time in milliseconds

    Should fields:
    - total_entries: Total number of calculations recorded

    Could fields:
    - min_execution_time_ms: Fastest execution time in milliseconds
    - max_execution_time_ms: Slowest execution time in milliseconds
    - operation_error_rates: Error rate percentage per operation type
    """

    operation_counts: dict[str, int]
    total_errors: int
    error_rate: float
    avg_execution_time_ms: float
    total_entries: int = 0
    min_execution_time_ms: float | None = None
    max_execution_time_ms: float | None = None
    operation_error_rates: dict[str, float] = field(default_factory=dict)
