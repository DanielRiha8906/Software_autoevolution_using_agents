from datetime import datetime
from typing import Dict, List, Optional

from ..models.workflow_run import WorkflowRun
from ..models.workflow_statistics_report import WorkflowStatisticsReport
from .workflow_attempt_service import WorkflowAttemptService
from .workflow_run_service import WorkflowRunService


class WorkflowStatisticsService:
    """Service for computing statistics about workflow runs and attempts."""

    def __init__(
        self,
        workflow_run_service: WorkflowRunService,
        workflow_attempt_service: WorkflowAttemptService,
    ):
        """
        Initialize statistics service with dependencies.

        Args:
            workflow_run_service: Service for accessing workflow runs
            workflow_attempt_service: Service for accessing workflow attempts
        """
        self._run_service = workflow_run_service
        self._attempt_service = workflow_attempt_service

    def compute_report(self) -> WorkflowStatisticsReport:
        """
        Compute full statistics report from all runs and attempts.

        Returns:
            WorkflowStatisticsReport with all computed statistics
        """
        runs = self._run_service.list_runs()
        return self.compute_report_for_runs(runs)

    def compute_report_for_runs(self, runs: List[WorkflowRun]) -> WorkflowStatisticsReport:
        """
        Compute statistics for a filtered subset of runs.

        Args:
            runs: List of WorkflowRun objects to compute statistics for

        Returns:
            WorkflowStatisticsReport with computed statistics
        """
        total_runs = len(runs)
        conclusion_counts = self._compute_conclusion_counts(runs)
        average_duration = self._compute_average_duration(runs)
        min_duration, max_duration = self._compute_min_max_duration(runs)
        duration_by_conclusion = self._compute_duration_by_conclusion(runs)
        total_attempts, runs_with_attempts, runs_with_no_attempts = (
            self._compute_attempt_statistics(runs)
        )
        average_attempts = (
            total_attempts / total_runs if total_runs > 0 else 0.0
        )

        return WorkflowStatisticsReport(
            total_runs=total_runs,
            conclusion_counts=conclusion_counts,
            average_duration_seconds=average_duration,
            min_duration_seconds=min_duration,
            max_duration_seconds=max_duration,
            duration_by_conclusion=duration_by_conclusion,
            total_attempts=total_attempts,
            average_attempts_per_run=average_attempts,
            runs_with_no_attempts=runs_with_no_attempts,
            runs_with_attempts=runs_with_attempts,
            generated_at=datetime.now(),
        )

    def _compute_conclusion_counts(self, runs: List[WorkflowRun]) -> Dict[Optional[str], int]:
        """
        Group runs by conclusion and count occurrences.

        Args:
            runs: List of workflow runs

        Returns:
            Dictionary mapping conclusion (or None) to count
        """
        counts: Dict[Optional[str], int] = {}
        for run in runs:
            conclusion_key = run.conclusion.value if run.conclusion else None
            counts[conclusion_key] = counts.get(conclusion_key, 0) + 1
        return counts

    def _compute_average_duration(self, runs: List[WorkflowRun]) -> float:
        """
        Compute average duration across all runs.

        Args:
            runs: List of workflow runs

        Returns:
            Average duration in seconds, or 0.0 if no runs
        """
        if not runs:
            return 0.0
        total_duration = sum(r.duration_seconds for r in runs)
        return total_duration / len(runs)

    def _compute_min_max_duration(
        self, runs: List[WorkflowRun]
    ) -> tuple[Optional[float], Optional[float]]:
        """
        Compute minimum and maximum duration across all runs.

        Args:
            runs: List of workflow runs

        Returns:
            Tuple of (min_duration, max_duration), or (None, None) if no runs
        """
        if not runs:
            return None, None
        durations = [r.duration_seconds for r in runs]
        return min(durations), max(durations)

    def _compute_duration_by_conclusion(
        self, runs: List[WorkflowRun]
    ) -> Dict[Optional[str], float]:
        """
        Compute average duration grouped by conclusion.

        Args:
            runs: List of workflow runs

        Returns:
            Dictionary mapping conclusion (or None) to average duration
        """
        by_conclusion: Dict[Optional[str], List[float]] = {}
        for run in runs:
            conclusion_key = run.conclusion.value if run.conclusion else None
            if conclusion_key not in by_conclusion:
                by_conclusion[conclusion_key] = []
            by_conclusion[conclusion_key].append(run.duration_seconds)

        averages: Dict[Optional[str], float] = {}
        for conclusion_key, durations in by_conclusion.items():
            if durations:
                averages[conclusion_key] = sum(durations) / len(durations)
            else:
                averages[conclusion_key] = 0.0
        return averages

    def _compute_attempt_statistics(
        self, runs: List[WorkflowRun]
    ) -> tuple[int, int, int]:
        """
        Compute attempt statistics for runs.

        Args:
            runs: List of workflow runs

        Returns:
            Tuple of (total_attempts, runs_with_attempts, runs_with_no_attempts)
        """
        total_attempts = 0
        runs_with_attempts = 0
        runs_with_no_attempts = 0

        for run in runs:
            attempts = self._attempt_service.filter_by_run_id(run.id)
            attempt_count = len(attempts)
            total_attempts += attempt_count

            if attempt_count > 0:
                runs_with_attempts += 1
            else:
                runs_with_no_attempts += 1

        return total_attempts, runs_with_attempts, runs_with_no_attempts
