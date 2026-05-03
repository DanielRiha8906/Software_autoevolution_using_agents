from dataclasses import dataclass


@dataclass
class CalculationStatistics:
    """Statistics derived from stored MemoryEntry data."""

    total_calculations: int
    total_errors: int
    error_rate_percent: float
    operations_count: dict[str, int]
    average_execution_time_ms: float

    def __post_init__(self) -> None:
        """Validate error_rate_percent is within [0, 100]."""
        if not (0 <= self.error_rate_percent <= 100):
            raise ValueError(
                f"error_rate_percent must be between 0 and 100, got {self.error_rate_percent}"
            )
