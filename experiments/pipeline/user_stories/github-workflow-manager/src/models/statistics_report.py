from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class StatisticsReport:
    count_by_conclusion: dict[str, int]
    average_duration_seconds: float
    average_attempts_per_run: float
    min_duration_seconds: Optional[float]
    max_duration_seconds: Optional[float]
    duration_by_status: dict[str, float]
