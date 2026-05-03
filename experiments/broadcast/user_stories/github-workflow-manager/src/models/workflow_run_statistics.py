from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class WorkflowRunStatistics:
    """Aggregated statistics over workflow runs.

    This dataclass holds computed statistics including success rates,
    durations, and retry behavior across stored workflow runs.

    Attributes:
        count_by_conclusion: Dictionary mapping conclusion values to their counts.
        average_duration_seconds: Average duration across all runs with duration data.
        min_duration_seconds: Minimum duration across all runs, or None if no runs have duration.
        max_duration_seconds: Maximum duration across all runs, or None if no runs have duration.
        average_attempts_per_run: Average number of attempts per run across all runs.
        per_status_breakdown: Dictionary mapping run status to average duration for that status.
    """

    count_by_conclusion: Dict[str, int] = field(default_factory=dict)
    average_duration_seconds: float = 0.0
    min_duration_seconds: Optional[float] = None
    max_duration_seconds: Optional[float] = None
    average_attempts_per_run: float = 0.0
    per_status_breakdown: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize the statistics to a dictionary.

        Returns:
            A dictionary with all statistics fields.
        """
        return {
            "count_by_conclusion": self.count_by_conclusion,
            "average_duration_seconds": self.average_duration_seconds,
            "min_duration_seconds": self.min_duration_seconds,
            "max_duration_seconds": self.max_duration_seconds,
            "average_attempts_per_run": self.average_attempts_per_run,
            "per_status_breakdown": self.per_status_breakdown,
        }
