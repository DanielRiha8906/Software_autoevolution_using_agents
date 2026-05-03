from dataclasses import dataclass
from typing import Dict


@dataclass
class WorkflowStatisticsReport:
    """Report containing aggregate statistics about workflow runs."""

    count_by_conclusion: Dict[str, int]
    avg_duration_seconds: float
    min_duration_seconds: float
    max_duration_seconds: float
    avg_attempts_per_run: float
