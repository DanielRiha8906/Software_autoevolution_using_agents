from dataclasses import dataclass
from typing import Dict

from .workflow_conclusion import WorkflowConclusion


@dataclass(frozen=True)
class WorkflowStatisticsReport:
    """A frozen dataclass containing workflow statistics."""
    count_by_conclusion: Dict[WorkflowConclusion, int]
    avg_duration_seconds: float
    min_duration_seconds: float
    max_duration_seconds: float
    avg_attempts_per_run: float
