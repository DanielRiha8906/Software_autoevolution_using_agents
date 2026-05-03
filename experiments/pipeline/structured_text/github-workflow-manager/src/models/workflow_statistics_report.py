from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class WorkflowStatisticsReport:
    """Structured report of workflow statistics computed from runs and attempts."""

    # Run counts
    total_runs: int
    conclusion_counts: Dict[Optional[str], int]

    # Duration statistics
    average_duration_seconds: float
    min_duration_seconds: Optional[float]
    max_duration_seconds: Optional[float]
    duration_by_conclusion: Dict[Optional[str], float]

    # Attempt statistics
    total_attempts: int
    average_attempts_per_run: float
    runs_with_no_attempts: int
    runs_with_attempts: int

    # Metadata
    generated_at: datetime

    def to_dict(self) -> dict:
        """Serialize report to dictionary for JSON output."""
        return {
            "total_runs": self.total_runs,
            "conclusion_counts": {
                str(k) if k is not None else "incomplete": v
                for k, v in self.conclusion_counts.items()
            },
            "average_duration_seconds": self.average_duration_seconds,
            "min_duration_seconds": self.min_duration_seconds,
            "max_duration_seconds": self.max_duration_seconds,
            "duration_by_conclusion": {
                str(k) if k is not None else "incomplete": v
                for k, v in self.duration_by_conclusion.items()
            },
            "total_attempts": self.total_attempts,
            "average_attempts_per_run": self.average_attempts_per_run,
            "runs_with_no_attempts": self.runs_with_no_attempts,
            "runs_with_attempts": self.runs_with_attempts,
            "generated_at": self.generated_at.isoformat(),
        }
