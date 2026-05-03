from typing import Dict

from ..models.workflow_statistics_report import WorkflowStatisticsReport
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_status import WorkflowStatus
from .workflow_run_service import WorkflowRunService


class WorkflowStatisticsService:
    """Service for computing workflow statistics."""

    def __init__(self, workflow_run_service: WorkflowRunService) -> None:
        """Initialize the statistics service.

        Args:
            workflow_run_service: Service to retrieve workflow runs.
        """
        self._workflow_run_service = workflow_run_service

    def compute(self) -> WorkflowStatisticsReport:
        """Compute workflow statistics from all runs.

        Returns:
            WorkflowStatisticsReport with aggregated statistics.
        """
        all_runs = self._workflow_run_service.list_runs()

        # Handle empty dataset
        if not all_runs:
            return WorkflowStatisticsReport(
                count_by_conclusion={},
                avg_duration_seconds=0.0,
                min_duration_seconds=0.0,
                max_duration_seconds=0.0,
                avg_attempts_per_run=0.0,
            )

        # Count by conclusion (only COMPLETED runs with non-null conclusion)
        count_by_conclusion: Dict[WorkflowConclusion, int] = {}
        for run in all_runs:
            if run.status == WorkflowStatus.COMPLETED and run.conclusion is not None:
                conclusion = run.conclusion
                count_by_conclusion[conclusion] = count_by_conclusion.get(conclusion, 0) + 1

        # Calculate duration statistics (all runs)
        durations = [r.duration_seconds for r in all_runs]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        min_duration = min(durations) if durations else 0.0
        max_duration = max(durations) if durations else 0.0

        # Calculate average attempts per run (all runs)
        attempt_service = self._workflow_run_service.attempt_service
        total_attempts = 0
        if attempt_service is not None:
            for run in all_runs:
                attempts = attempt_service.get_by_run_id(run.id)
                total_attempts += len(attempts)

        avg_attempts_per_run = total_attempts / len(all_runs) if all_runs else 0.0

        return WorkflowStatisticsReport(
            count_by_conclusion=count_by_conclusion,
            avg_duration_seconds=avg_duration,
            min_duration_seconds=min_duration,
            max_duration_seconds=max_duration,
            avg_attempts_per_run=avg_attempts_per_run,
        )
