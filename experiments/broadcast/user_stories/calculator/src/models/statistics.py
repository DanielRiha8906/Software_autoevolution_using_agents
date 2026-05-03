from dataclasses import dataclass, field


@dataclass
class Statistics:
    """Structured statistics derived from stored memory entries.

    Provides a consistent output format for calculator usage and error metrics.
    All statistics are computed from MemoryEntry objects in the storage.
    """

    operation_counts: dict[str, int] = field(default_factory=dict)
    """Count of calculations per operation type (e.g., {'add': 5, 'divide': 2})."""

    total_errors: int = 0
    """Total number of failed operations (ErrorEntry instances)."""

    error_rate_percentage: float = 0.0
    """Percentage of total operations that resulted in errors (0.0 to 100.0)."""

    average_execution_time_ms: float = 0.0
    """Mean execution time in milliseconds across all operations."""
