from dataclasses import dataclass, field

from .workflow_status import WorkflowStatus
from .workflow_conclusion import WorkflowConclusion


@dataclass(frozen=True)
class StatisticsReport:
    """Statistics aggregation report for workflow runs."""
    total_runs: int
    count_by_conclusion: dict[WorkflowConclusion, int] = field(default_factory=dict)
    average_duration_seconds: float = 0.0
    min_duration_seconds: float = 0.0
    max_duration_seconds: float = 0.0
    average_attempts_per_run: float = 0.0
    per_status_avg_duration: dict[WorkflowStatus, float] = field(default_factory=dict)
