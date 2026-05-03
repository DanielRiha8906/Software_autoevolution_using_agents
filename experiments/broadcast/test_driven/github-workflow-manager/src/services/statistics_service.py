from dataclasses import dataclass, field
from typing import Dict

from ..models.workflow_conclusion import WorkflowConclusion
from .workflow_run_service import WorkflowRunService


@dataclass
class WorkflowStatisticsReport:
    """Report containing aggregated statistics for workflow runs."""

    count_by_conclusion: Dict[WorkflowConclusion, int] = field(default_factory=dict)
    avg_duration_seconds: float = 0.0
    min_duration_seconds: float = 0.0
    max_duration_seconds: float = 0.0
    avg_attempts_per_run: float = 0.0


class WorkflowStatisticsService:
    """Service for computing statistics over workflow runs."""

    def __init__(self, run_service: WorkflowRunService) -> None:
        """Initialize the statistics service.

        Args:
            run_service: WorkflowRunService instance to query run data.
        """
        self._run_service = run_service

    def compute(self) -> WorkflowStatisticsReport:
        """Compute statistics for all workflow runs.

        Returns:
            A WorkflowStatisticsReport containing aggregated statistics.
            If no runs exist, all values are zero.
        """
        runs = self._run_service.list_runs()

        # Handle empty dataset
        if not runs:
            return WorkflowStatisticsReport()

        # Count by conclusion
        count_by_conclusion: Dict[WorkflowConclusion, int] = {}
        for run in runs:
            if run.conclusion is not None:
                count_by_conclusion[run.conclusion] = count_by_conclusion.get(run.conclusion, 0) + 1

        # Duration statistics
        durations = [run.duration_seconds for run in runs]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        min_duration = min(durations) if durations else 0.0
        max_duration = max(durations) if durations else 0.0

        # Average attempts per run
        # Count total attempts across all runs
        total_attempts = 0
        if self._run_service._attempt_service is not None:
            for run in runs:
                attempts = self._run_service._attempt_service.get_by_run_id(run.id)
                total_attempts += len(attempts)

        # avg_attempts_per_run counts all runs, including those with zero attempts
        avg_attempts = total_attempts / len(runs) if runs else 0.0

        return WorkflowStatisticsReport(
            count_by_conclusion=count_by_conclusion,
            avg_duration_seconds=avg_duration,
            min_duration_seconds=min_duration,
            max_duration_seconds=max_duration,
            avg_attempts_per_run=avg_attempts,
        )
