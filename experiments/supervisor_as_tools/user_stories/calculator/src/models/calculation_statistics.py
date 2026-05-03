from dataclasses import dataclass


@dataclass(frozen=True)
class CalculationStatistics:
    operation_counts: dict[str, int]
    total_errors: int
    error_rate: float
    avg_execution_time_ms: float
