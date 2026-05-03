from dataclasses import dataclass
from typing import Optional


@dataclass
class WorkflowStatistics:
    """Statistics about workflow runs and attempts."""

    total_runs: int
    count_by_conclusion: dict[str, int]
    average_duration_seconds: float
    min_duration_seconds: Optional[float]
    max_duration_seconds: Optional[float]
    average_attempts_per_run: float

    def to_dict(self) -> dict:
        """Convert statistics to dictionary for JSON serialization."""
        return {
            "total_runs": self.total_runs,
            "count_by_conclusion": self.count_by_conclusion,
            "average_duration_seconds": self.average_duration_seconds,
            "min_duration_seconds": self.min_duration_seconds,
            "max_duration_seconds": self.max_duration_seconds,
            "average_attempts_per_run": self.average_attempts_per_run,
        }
