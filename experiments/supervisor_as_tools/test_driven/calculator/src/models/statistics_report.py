from dataclasses import dataclass


@dataclass
class StatisticsReport:
    count_per_operation: dict[str, int]
    total_errors: int
    error_rate: float
    avg_execution_time_ms: float
