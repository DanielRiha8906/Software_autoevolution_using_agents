from dataclasses import dataclass, field


@dataclass
class StatisticsReport:
    """Domain class representing calculation statistics."""

    total_operations: int = 0
    operation_count: dict[str, int] = field(default_factory=dict)
    total_errors: int = 0
    error_frequency: dict[str, int] = field(default_factory=dict)
    error_rate: float = 0.0
    average_execution_time_ms: float = 0.0
    min_execution_time_ms: float = float('inf')
    max_execution_time_ms: float = 0.0

    def __post_init__(self) -> None:
        """Initialize default values for min/max if not set."""
        if self.min_execution_time_ms == float('inf') and self.total_operations == 0:
            self.min_execution_time_ms = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'total_operations': self.total_operations,
            'operation_count': self.operation_count,
            'total_errors': self.total_errors,
            'error_frequency': self.error_frequency,
            'error_rate': self.error_rate,
            'average_execution_time_ms': self.average_execution_time_ms,
            'min_execution_time_ms': self.min_execution_time_ms if self.min_execution_time_ms != float('inf') else 0.0,
            'max_execution_time_ms': self.max_execution_time_ms,
        }
