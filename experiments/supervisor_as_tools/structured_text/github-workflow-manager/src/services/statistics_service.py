from typing import Optional

from ..models.workflow_statistics import WorkflowStatistics
from .workflow_run_service import WorkflowRunService
from .attempt_service import AttemptService


class StatisticsService:
    """Service to compute statistics about workflow runs and attempts."""

    def __init__(self, workflow_run_service: WorkflowRunService, attempt_service: AttemptService):
        """Initialize StatisticsService with dependencies.

        Args:
            workflow_run_service: WorkflowRunService instance.
            attempt_service: AttemptService instance.
        """
        self._workflow_run_service = workflow_run_service
        self._attempt_service = attempt_service

    def compute_statistics(self) -> WorkflowStatistics:
        """Compute statistics about all workflow runs and attempts.

        Returns:
            WorkflowStatistics object with computed metrics.
        """
        runs = self._workflow_run_service.list_runs()
        total_runs = len(runs)

        # Count by conclusion
        count_by_conclusion: dict[str, int] = {}
        durations_with_values = []

        for run in runs:
            # Count by conclusion
            if run.conclusion is None:
                key = "none"
            else:
                key = run.conclusion.value

            count_by_conclusion[key] = count_by_conclusion.get(key, 0) + 1

            # Collect non-zero durations for min/max/avg
            if run.duration_seconds > 0.0:
                durations_with_values.append(run.duration_seconds)

        # Compute duration statistics
        if durations_with_values:
            average_duration_seconds = sum(durations_with_values) / len(durations_with_values)
            min_duration_seconds = min(durations_with_values)
            max_duration_seconds = max(durations_with_values)
        else:
            average_duration_seconds = 0.0
            min_duration_seconds = None
            max_duration_seconds = None

        # Compute average attempts per run
        all_attempts = self._attempt_service.list_attempts()
        total_attempts = len(all_attempts)
        average_attempts_per_run = (
            total_attempts / total_runs if total_runs > 0 else 0.0
        )

        return WorkflowStatistics(
            total_runs=total_runs,
            count_by_conclusion=count_by_conclusion,
            average_duration_seconds=average_duration_seconds,
            min_duration_seconds=min_duration_seconds,
            max_duration_seconds=max_duration_seconds,
            average_attempts_per_run=average_attempts_per_run,
        )
