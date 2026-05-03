from dataclasses import dataclass, field
from typing import Dict, Optional

from ..models.workflow_conclusion import WorkflowConclusion
from .workflow_run_service import WorkflowRunService
from .attempt_service import AttemptService


@dataclass
class WorkflowStatisticsReport:
    """Structured report of workflow statistics."""
    total_runs: int
    conclusions_count: Dict[str, int] = field(default_factory=dict)
    avg_duration_seconds: float = 0.0
    min_duration_seconds: Optional[float] = None
    max_duration_seconds: Optional[float] = None
    avg_attempts_per_run: float = 0.0

    def to_dict(self) -> dict:
        """Convert report to dictionary representation."""
        return {
            "total_runs": self.total_runs,
            "conclusions_count": self.conclusions_count,
            "avg_duration_seconds": self.avg_duration_seconds,
            "min_duration_seconds": self.min_duration_seconds,
            "max_duration_seconds": self.max_duration_seconds,
            "avg_attempts_per_run": self.avg_attempts_per_run,
        }


class StatisticsService:
    """Service for computing workflow statistics."""

    def __init__(self, workflow_run_service: WorkflowRunService, attempt_service: AttemptService):
        self._workflow_run_service = workflow_run_service
        self._attempt_service = attempt_service

    def compute_statistics(self) -> WorkflowStatisticsReport:
        """Compute statistics for all workflow runs.

        Returns:
            WorkflowStatisticsReport with computed statistics.
        """
        runs = self._workflow_run_service.list_runs()
        attempts = self._attempt_service.list_attempts()

        # Total runs
        total_runs = len(runs)

        # Count by conclusion
        conclusions_count: Dict[str, int] = {}
        for conclusion in WorkflowConclusion:
            count = sum(1 for r in runs if r.conclusion == conclusion)
            if count > 0:
                conclusions_count[conclusion.value] = count

        # Average duration
        avg_duration_seconds = 0.0
        min_duration_seconds: Optional[float] = None
        max_duration_seconds: Optional[float] = None

        if runs:
            durations = [r.duration_seconds for r in runs]
            avg_duration_seconds = sum(durations) / len(durations)
            min_duration_seconds = min(durations)
            max_duration_seconds = max(durations)

        # Average attempts per run
        avg_attempts_per_run = 0.0
        if runs:
            # Count attempts per run
            attempts_by_run: Dict[int, int] = {}
            for attempt in attempts:
                run_id = attempt.run_id
                attempts_by_run[run_id] = attempts_by_run.get(run_id, 0) + 1

            # Calculate average
            total_attempts = sum(attempts_by_run.values())
            avg_attempts_per_run = total_attempts / len(runs)

        return WorkflowStatisticsReport(
            total_runs=total_runs,
            conclusions_count=conclusions_count,
            avg_duration_seconds=avg_duration_seconds,
            min_duration_seconds=min_duration_seconds,
            max_duration_seconds=max_duration_seconds,
            avg_attempts_per_run=avg_attempts_per_run,
        )
