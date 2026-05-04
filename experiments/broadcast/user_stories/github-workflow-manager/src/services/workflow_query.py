from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ..models.workflow_run import WorkflowRun


@dataclass
class DurationRange:
    """Filter for workflow run duration."""
    min_seconds: Optional[float] = None
    max_seconds: Optional[float] = None


@dataclass
class TimestampRange:
    """Filter for workflow run timestamps."""
    before: Optional[datetime] = None
    after: Optional[datetime] = None


class WorkflowQuery:
    """Programmatic query interface for filtering workflow runs.

    Allows filtering by duration, timestamp, and attempt presence with
    support for combining multiple filters in a single query.
    """

    def __init__(self, runs: List[WorkflowRun], attempt_service: Optional["AttemptService"] = None):
        """Initialize the query with a list of workflow runs.

        Args:
            runs: List of WorkflowRun objects to query.
            attempt_service: Optional AttemptService for attempt presence filtering.
        """
        self._runs = runs
        self._attempt_service = attempt_service

    def _calculate_duration_seconds(self, run: WorkflowRun) -> Optional[float]:
        """Calculate duration in seconds for a run.

        Duration is calculated as the difference between updated_at and created_at.
        If updated_at is None, returns None.

        Args:
            run: The WorkflowRun to calculate duration for.

        Returns:
            Duration in seconds, or None if updated_at is not available.
        """
        if run.updated_at is None:
            return None
        delta = run.updated_at - run.created_at
        return delta.total_seconds()

    def filter_by_duration(self, min_seconds: Optional[float] = None,
                          max_seconds: Optional[float] = None) -> List[WorkflowRun]:
        """Filter runs by duration range.

        Args:
            min_seconds: Minimum duration in seconds (inclusive), or None for no minimum.
            max_seconds: Maximum duration in seconds (inclusive), or None for no maximum.

        Returns:
            List of runs matching the duration criteria.

        Raises:
            ValueError: If min_seconds > max_seconds, or if either is negative.
        """
        if min_seconds is not None and min_seconds < 0:
            raise ValueError(f"min_seconds must be non-negative, got {min_seconds}")
        if max_seconds is not None and max_seconds < 0:
            raise ValueError(f"max_seconds must be non-negative, got {max_seconds}")
        if min_seconds is not None and max_seconds is not None and min_seconds > max_seconds:
            raise ValueError(f"min_seconds ({min_seconds}) cannot be greater than max_seconds ({max_seconds})")

        results = []
        for run in self._runs:
            duration = self._calculate_duration_seconds(run)
            if duration is None:
                continue

            if min_seconds is not None and duration < min_seconds:
                continue
            if max_seconds is not None and duration > max_seconds:
                continue

            results.append(run)

        return results

    def filter_by_timestamp(self, before: Optional[datetime] = None,
                           after: Optional[datetime] = None) -> List[WorkflowRun]:
        """Filter runs by creation timestamp.

        Args:
            before: Only include runs created before this datetime (exclusive).
            after: Only include runs created after this datetime (exclusive).

        Returns:
            List of runs matching the timestamp criteria.

        Raises:
            ValueError: If before <= after.
        """
        if before is not None and after is not None and before <= after:
            raise ValueError(f"before ({before}) must be greater than after ({after})")

        results = []
        for run in self._runs:
            if before is not None and run.created_at >= before:
                continue
            if after is not None and run.created_at <= after:
                continue
            results.append(run)

        return results

    def filter_by_attempt_presence(self, has_attempts: bool = True) -> List[WorkflowRun]:
        """Filter runs by whether they have attempts.

        Args:
            has_attempts: If True, only include runs that have attempts.
                         If False, only include runs that have no attempts.

        Returns:
            List of runs matching the attempt criteria.

        Raises:
            ValueError: If attempt_service is not available.
        """
        if self._attempt_service is None:
            raise ValueError("attempt_service is required for attempt presence filtering")

        results = []
        for run in self._runs:
            try:
                run_id = int(run.id)
            except (ValueError, TypeError):
                run_id = run.id
            attempts = self._attempt_service.get_attempts_for_run(run_id)
            has_any = len(attempts) > 0

            if has_attempts and has_any:
                results.append(run)
            elif not has_attempts and not has_any:
                results.append(run)

        return results

    def query(self,
              duration_range: Optional[DurationRange] = None,
              timestamp_range: Optional[TimestampRange] = None,
              has_attempts: Optional[bool] = None) -> List[WorkflowRun]:
        """Execute a combined query with multiple filters.

        All specified filters are applied in sequence (AND logic).

        Args:
            duration_range: Optional DurationRange to filter by duration.
            timestamp_range: Optional TimestampRange to filter by timestamp.
            has_attempts: Optional boolean to filter by attempt presence.
                         True = has attempts, False = no attempts.

        Returns:
            List of runs matching all specified criteria.
        """
        results = list(self._runs)

        if duration_range is not None:
            results = self._filter_results_by_duration(
                results,
                duration_range.min_seconds,
                duration_range.max_seconds
            )

        if timestamp_range is not None:
            results = self._filter_results_by_timestamp(
                results,
                timestamp_range.before,
                timestamp_range.after
            )

        if has_attempts is not None:
            results = self._filter_results_by_attempt_presence(results, has_attempts)

        return results

    def _filter_results_by_duration(self, runs: List[WorkflowRun],
                                   min_seconds: Optional[float],
                                   max_seconds: Optional[float]) -> List[WorkflowRun]:
        """Helper to filter an existing result set by duration."""
        results = []
        for run in runs:
            duration = self._calculate_duration_seconds(run)
            if duration is None:
                continue

            if min_seconds is not None and duration < min_seconds:
                continue
            if max_seconds is not None and duration > max_seconds:
                continue

            results.append(run)

        return results

    def _filter_results_by_timestamp(self, runs: List[WorkflowRun],
                                    before: Optional[datetime],
                                    after: Optional[datetime]) -> List[WorkflowRun]:
        """Helper to filter an existing result set by timestamp."""
        results = []
        for run in runs:
            if before is not None and run.created_at >= before:
                continue
            if after is not None and run.created_at <= after:
                continue
            results.append(run)

        return results

    def _filter_results_by_attempt_presence(self, runs: List[WorkflowRun],
                                           has_attempts: bool) -> List[WorkflowRun]:
        """Helper to filter an existing result set by attempt presence."""
        if self._attempt_service is None:
            raise ValueError("attempt_service is required for attempt presence filtering")

        results = []
        for run in runs:
            try:
                run_id = int(run.id)
            except (ValueError, TypeError):
                run_id = run.id
            attempts = self._attempt_service.get_attempts_for_run(run_id)
            has_any = len(attempts) > 0

            if has_attempts and has_any:
                results.append(run)
            elif not has_attempts and not has_any:
                results.append(run)

        return results


__all__ = ["WorkflowQuery", "DurationRange", "TimestampRange"]
