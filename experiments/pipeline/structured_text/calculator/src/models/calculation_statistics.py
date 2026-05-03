from dataclasses import dataclass


@dataclass
class CalculationStatistics:
    """
    Aggregated statistics computed from stored MemoryEntry objects.

    Provides a comprehensive view of calculation usage patterns and performance
    metrics, including operation frequency, error rates, and execution times.
    """
    operation_counts: dict[str, int]
    total_calculations: int
    error_count: int
    error_percentage: float
    average_execution_time_ms: float
    min_execution_time_ms: float
    max_execution_time_ms: float
    per_operation_stats: dict[str, dict]

    def to_dict(self) -> dict:
        """Convert to JSON-compatible dictionary."""
        return {
            "operation_counts": self.operation_counts,
            "total_calculations": self.total_calculations,
            "error_count": self.error_count,
            "error_percentage": self.error_percentage,
            "average_execution_time_ms": self.average_execution_time_ms,
            "min_execution_time_ms": self.min_execution_time_ms,
            "max_execution_time_ms": self.max_execution_time_ms,
            "per_operation_stats": self.per_operation_stats,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CalculationStatistics":
        """Create CalculationStatistics from dict."""
        return cls(**data)
