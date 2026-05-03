from typing import List, Optional

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.statistics_report import StatisticsReport
from .workflow_run_attempt_service import WorkflowRunAttemptService


class StatisticsService:
    def calculate_statistics(
        self,
        runs: List[WorkflowRun],
        attempt_service: Optional[WorkflowRunAttemptService] = None,
    ) -> StatisticsReport:
        """
        Calculate aggregated statistics over a list of workflow runs.

        Args:
            runs: List of WorkflowRun objects to analyze
            attempt_service: Optional service for computing attempt counts

        Returns:
            StatisticsReport with computed metrics
        """
        # Initialize duration_by_status with all status values
        duration_by_status: dict[str, float] = {status.value: 0.0 for status in WorkflowStatus}

        if not runs:
            return StatisticsReport(
                count_by_conclusion={},
                average_duration_seconds=0.0,
                average_attempts_per_run=0.0,
                min_duration_seconds=None,
                max_duration_seconds=None,
                duration_by_status=duration_by_status,
            )

        # Calculate count by conclusion
        count_by_conclusion: dict[str, int] = {}
        for run in runs:
            if run.conclusion:
                conclusion_str = run.conclusion.value
                count_by_conclusion[conclusion_str] = count_by_conclusion.get(conclusion_str, 0) + 1

        # Calculate average duration
        total_duration = sum(run.duration_seconds for run in runs)
        average_duration_seconds = total_duration / len(runs) if runs else 0.0

        # Calculate average attempts per run
        average_attempts_per_run = 0.0
        if attempt_service is not None:
            total_attempts = len(attempt_service.list_attempts(sorted=False))
            average_attempts_per_run = total_attempts / len(runs) if runs else 0.0

        # Calculate min and max duration
        min_duration_seconds: Optional[float] = None
        max_duration_seconds: Optional[float] = None
        if runs:
            durations = [run.duration_seconds for run in runs]
            min_duration_seconds = min(durations)
            max_duration_seconds = max(durations)

        # Calculate duration by status (bonus)
        for status in WorkflowStatus:
            matching_runs = [r for r in runs if r.status == status]
            if matching_runs:
                avg_duration = sum(r.duration_seconds for r in matching_runs) / len(matching_runs)
                duration_by_status[status.value] = avg_duration

        return StatisticsReport(
            count_by_conclusion=count_by_conclusion,
            average_duration_seconds=average_duration_seconds,
            average_attempts_per_run=average_attempts_per_run,
            min_duration_seconds=min_duration_seconds,
            max_duration_seconds=max_duration_seconds,
            duration_by_status=duration_by_status,
        )
