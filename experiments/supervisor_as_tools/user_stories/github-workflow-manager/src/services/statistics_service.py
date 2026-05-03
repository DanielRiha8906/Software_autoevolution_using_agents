from typing import List

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.statistics_report import StatisticsReport


class StatisticsService:
    """Service for computing statistics from workflow runs."""

    def compute_statistics(self, runs: List[WorkflowRun]) -> StatisticsReport:
        """Compute statistics from a list of workflow runs.

        Args:
            runs: List of WorkflowRun objects to analyze

        Returns:
            StatisticsReport with aggregated metrics
        """
        if not runs:
            return StatisticsReport(
                total_runs=0,
                count_by_conclusion={},
                average_duration_seconds=0.0,
                min_duration_seconds=0.0,
                max_duration_seconds=0.0,
                average_attempts_per_run=0.0,
                per_status_avg_duration={},
            )

        # Count total runs
        total_runs = len(runs)

        # Count by conclusion (excluding None conclusions)
        count_by_conclusion: dict[WorkflowConclusion, int] = {}
        for run in runs:
            if run.conclusion is not None:
                count_by_conclusion[run.conclusion] = count_by_conclusion.get(run.conclusion, 0) + 1

        # Calculate duration statistics
        durations = [run.duration_seconds for run in runs]
        average_duration_seconds = sum(durations) / len(durations) if durations else 0.0
        min_duration_seconds = min(durations) if durations else 0.0
        max_duration_seconds = max(durations) if durations else 0.0

        # Calculate average attempts per run
        total_attempts = sum(len(run.attempts) for run in runs)
        average_attempts_per_run = total_attempts / total_runs if total_runs > 0 else 0.0

        # Calculate per-status average duration
        per_status_avg_duration: dict[WorkflowStatus, float] = {}
        status_groups: dict[WorkflowStatus, List[float]] = {}
        for run in runs:
            if run.status not in status_groups:
                status_groups[run.status] = []
            status_groups[run.status].append(run.duration_seconds)

        for status, durations_for_status in status_groups.items():
            per_status_avg_duration[status] = sum(durations_for_status) / len(durations_for_status)

        return StatisticsReport(
            total_runs=total_runs,
            count_by_conclusion=count_by_conclusion,
            average_duration_seconds=average_duration_seconds,
            min_duration_seconds=min_duration_seconds,
            max_duration_seconds=max_duration_seconds,
            average_attempts_per_run=average_attempts_per_run,
            per_status_avg_duration=per_status_avg_duration,
        )

    def format_statistics_for_terminal(self, report: StatisticsReport) -> str:
        """Format statistics report for terminal display.

        Args:
            report: StatisticsReport to format

        Returns:
            Multi-line formatted string for terminal output
        """
        lines = []
        lines.append("\n--- Workflow Statistics ---")
        lines.append(f"Total runs: {report.total_runs}")
        lines.append("")

        if report.count_by_conclusion:
            lines.append("Conclusion breakdown:")
            for conclusion, count in sorted(report.count_by_conclusion.items(), key=lambda x: x[0].value):
                lines.append(f"  {conclusion.value}: {count}")
            lines.append("")

        lines.append(f"Duration statistics (seconds):")
        lines.append(f"  Average: {report.average_duration_seconds:.2f}")
        lines.append(f"  Minimum: {report.min_duration_seconds:.2f}")
        lines.append(f"  Maximum: {report.max_duration_seconds:.2f}")
        lines.append("")

        lines.append(f"Average attempts per run: {report.average_attempts_per_run:.2f}")
        lines.append("")

        if report.per_status_avg_duration:
            lines.append("Average duration by status:")
            for status, avg_duration in sorted(report.per_status_avg_duration.items(), key=lambda x: x[0].value):
                lines.append(f"  {status.value}: {avg_duration:.2f}s")
            lines.append("")

        return "\n".join(lines)
