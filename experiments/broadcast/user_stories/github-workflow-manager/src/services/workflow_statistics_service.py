from typing import List, Dict

from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..models.workflow_run_statistics import WorkflowRunStatistics


class WorkflowStatisticsService:
    """Service for computing aggregated statistics over workflow runs and attempts.

    Computes statistics including success rates, durations, and retry behavior
    across stored workflow runs and attempts.
    """

    def compute_statistics(
        self,
        runs: List[WorkflowRun],
        attempts: List[WorkflowRunAttempt],
    ) -> WorkflowRunStatistics:
        """Compute statistics from workflow runs and attempts.

        Args:
            runs: List of WorkflowRun objects.
            attempts: List of WorkflowRunAttempt objects.

        Returns:
            A WorkflowRunStatistics object with computed statistics.
        """
        # Count by conclusion
        count_by_conclusion: Dict[str, int] = {}
        for run in runs:
            if run.conclusion:
                conclusion_val = run.conclusion.value
                count_by_conclusion[conclusion_val] = count_by_conclusion.get(conclusion_val, 0) + 1

        # Duration statistics
        durations = []
        for run in runs:
            if run.updated_at is not None:
                delta = run.updated_at - run.created_at
                duration_seconds = delta.total_seconds()
                durations.append(duration_seconds)

        average_duration_seconds = sum(durations) / len(durations) if durations else 0.0
        min_duration_seconds = min(durations) if durations else None
        max_duration_seconds = max(durations) if durations else None

        # Attempts per run
        attempts_count_per_run: Dict[int, int] = {}
        for attempt in attempts:
            run_id = attempt.run_id
            attempts_count_per_run[run_id] = attempts_count_per_run.get(run_id, 0) + 1

        # Calculate average attempts per run across all runs
        # Build set of run_ids that match the attempts (try both string and int conversion)
        total_attempts = 0
        for run in runs:
            # Try to find attempts for this run
            attempts_for_run = 0

            # First try using run_id directly if it's an int
            if isinstance(run.id, int):
                attempts_for_run = attempts_count_per_run.get(run.id, 0)
            else:
                # Try to convert run.id to int
                try:
                    run_id_as_int = int(run.id)
                    attempts_for_run = attempts_count_per_run.get(run_id_as_int, 0)
                except (ValueError, TypeError):
                    attempts_for_run = 0

            total_attempts += attempts_for_run

        average_attempts_per_run = (
            total_attempts / len(runs)
            if runs else 0.0
        )

        # Per-status breakdown (bonus)
        per_status_breakdown: Dict[str, float] = {}
        status_durations: Dict[str, List[float]] = {}

        for run in runs:
            if run.updated_at is not None:
                delta = run.updated_at - run.created_at
                duration_seconds = delta.total_seconds()
                status_val = run.status.value

                if status_val not in status_durations:
                    status_durations[status_val] = []
                status_durations[status_val].append(duration_seconds)

        for status, status_durs in status_durations.items():
            per_status_breakdown[status] = sum(status_durs) / len(status_durs)

        return WorkflowRunStatistics(
            count_by_conclusion=count_by_conclusion,
            average_duration_seconds=average_duration_seconds,
            min_duration_seconds=min_duration_seconds,
            max_duration_seconds=max_duration_seconds,
            average_attempts_per_run=average_attempts_per_run,
            per_status_breakdown=per_status_breakdown,
        )


__all__ = ["WorkflowStatisticsService"]
