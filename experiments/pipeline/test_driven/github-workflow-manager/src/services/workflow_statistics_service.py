from typing import Optional, TYPE_CHECKING

from ..models.workflow_statistics_report import WorkflowStatisticsReport
from ..models.workflow_status import WorkflowStatus

if TYPE_CHECKING:
    from .workflow_run_service import WorkflowRunService
    from .attempt_service import AttemptService


class WorkflowStatisticsService:
    """Service for computing aggregate statistics about workflow runs."""

    def __init__(self, workflow_run_service: "WorkflowRunService") -> None:
        """
        Initialize the statistics service.

        Args:
            workflow_run_service: Service for accessing workflow runs.
        """
        self._workflow_run_service = workflow_run_service

    def compute(
        self, attempt_service: Optional["AttemptService"] = None
    ) -> WorkflowStatisticsReport:
        """
        Compute aggregate statistics for all workflow runs.

        Args:
            attempt_service: Optional service for accessing attempt counts.
                            If provided, avg_attempts_per_run will be computed.
                            If None, avg_attempts_per_run will be 0.0.

        Returns:
            WorkflowStatisticsReport containing:
            - count_by_conclusion: Dict mapping conclusion strings to counts
              (only for terminal runs with non-null conclusions)
            - avg_duration_seconds: Average duration across all runs (0.0 if no runs)
            - min_duration_seconds: Minimum duration across all runs (0.0 if no runs)
            - max_duration_seconds: Maximum duration across all runs (0.0 if no runs)
            - avg_attempts_per_run: Average attempts per run across all runs
              (includes runs with 0 attempts in denominator, 0.0 if no runs)
        """
        runs = self._workflow_run_service.list_runs()

        # Compute count_by_conclusion: only terminal runs with non-null conclusions
        count_by_conclusion = {}
        for run in runs:
            if run.status == WorkflowStatus.COMPLETED and run.conclusion is not None:
                conclusion_str = run.conclusion.value
                count_by_conclusion[conclusion_str] = count_by_conclusion.get(
                    conclusion_str, 0
                ) + 1

        # Compute duration statistics
        durations = [run.duration_seconds for run in runs]
        if durations:
            avg_duration_seconds = sum(durations) / len(durations)
            min_duration_seconds = min(durations)
            max_duration_seconds = max(durations)
        else:
            avg_duration_seconds = 0.0
            min_duration_seconds = 0.0
            max_duration_seconds = 0.0

        # Compute average attempts per run
        if attempt_service is None:
            avg_attempts_per_run = 0.0
        else:
            total_attempts = 0
            for run in runs:
                try:
                    run_id_int = int(run.id)
                    attempts = attempt_service.get_by_run_id(run_id_int)
                    total_attempts += len(attempts)
                except (ValueError, TypeError):
                    # Non-integer run IDs are treated as 0 attempts
                    pass

            if runs:
                avg_attempts_per_run = total_attempts / len(runs)
            else:
                avg_attempts_per_run = 0.0

        return WorkflowStatisticsReport(
            count_by_conclusion=count_by_conclusion,
            avg_duration_seconds=avg_duration_seconds,
            min_duration_seconds=min_duration_seconds,
            max_duration_seconds=max_duration_seconds,
            avg_attempts_per_run=avg_attempts_per_run,
        )
