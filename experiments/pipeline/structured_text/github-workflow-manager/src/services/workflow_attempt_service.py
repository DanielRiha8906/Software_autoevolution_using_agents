from typing import List, Optional
from datetime import datetime

from ..models.workflow_attempt import WorkflowRunAttempt
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..storage.workflow_attempt_json_storage import WorkflowAttemptJsonStorage


class WorkflowAttemptService:
    def __init__(self, storage: WorkflowAttemptJsonStorage):
        self._storage = storage
        self._attempts: List[WorkflowRunAttempt] = storage.load()

    def _persist(self) -> None:
        self._storage.save(self._attempts)

    def add_attempt(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        if any(a.id == attempt.id for a in self._attempts):
            raise ValueError(f"Attempt with id '{attempt.id}' already exists.")
        if any(a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number
               for a in self._attempts):
            raise ValueError(f"Attempt number {attempt.attempt_number} already exists for run '{attempt.run_id}'.")
        self._attempts.append(attempt)
        self._persist()
        return attempt

    def list_attempts(self) -> List[WorkflowRunAttempt]:
        return list(self._attempts)

    def get_attempt_detail(self, attempt_id: str) -> Optional[WorkflowRunAttempt]:
        return next((a for a in self._attempts if a.id == attempt_id), None)

    def filter_by_run_id(self, run_id: str) -> List[WorkflowRunAttempt]:
        return sorted(
            [a for a in self._attempts if a.run_id == run_id],
            key=lambda a: a.attempt_number
        )

    def filter_by_status(self, status: WorkflowStatus) -> List[WorkflowRunAttempt]:
        return [a for a in self._attempts if a.status == status]

    def filter_by_conclusion(self, conclusion: WorkflowConclusion) -> List[WorkflowRunAttempt]:
        return [a for a in self._attempts if a.conclusion == conclusion]

    def filter_by_duration_range(
        self, min_seconds: Optional[float] = None, max_seconds: Optional[float] = None
    ) -> List[WorkflowRunAttempt]:
        """
        Filter attempts by duration range (in seconds).

        Args:
            min_seconds: Minimum duration (inclusive). None means no lower bound.
            max_seconds: Maximum duration (inclusive). None means no upper bound.

        Returns:
            List of attempts matching the criteria, sorted by attempt_number ascending.

        Raises:
            ValueError: If min_seconds or max_seconds is negative, or min > max.
        """
        if min_seconds is not None and min_seconds < 0:
            raise ValueError(f"min_seconds must be non-negative, got {min_seconds}")
        if max_seconds is not None and max_seconds < 0:
            raise ValueError(f"max_seconds must be non-negative, got {max_seconds}")
        if min_seconds is not None and max_seconds is not None and min_seconds > max_seconds:
            raise ValueError(
                f"min_seconds ({min_seconds}) must be <= max_seconds ({max_seconds})"
            )

        filtered = self._attempts
        if min_seconds is not None:
            filtered = [a for a in filtered if a.duration_seconds >= min_seconds]
        if max_seconds is not None:
            filtered = [a for a in filtered if a.duration_seconds <= max_seconds]

        return sorted(filtered, key=lambda a: a.attempt_number)

    def filter_by_started_at(
        self, before: Optional[datetime] = None, after: Optional[datetime] = None
    ) -> List[WorkflowRunAttempt]:
        """
        Filter attempts by start timestamp.

        Args:
            before: Include attempts started before this datetime (inclusive).
                    None means no upper bound.
            after: Include attempts started after this datetime (inclusive).
                   None means no lower bound.

        Returns:
            List of attempts matching the criteria, sorted by attempt_number ascending.

        Raises:
            ValueError: If before < after.
        """
        if before is not None and after is not None and after > before:
            raise ValueError(f"after ({after}) must be <= before ({before})")

        filtered = self._attempts
        if after is not None:
            filtered = [a for a in filtered if a.started_at >= after]
        if before is not None:
            filtered = [a for a in filtered if a.started_at <= before]

        return sorted(filtered, key=lambda a: a.attempt_number)

    def filter_by_completed_at(
        self, before: Optional[datetime] = None, after: Optional[datetime] = None
    ) -> List[WorkflowRunAttempt]:
        """
        Filter attempts by completion timestamp.

        Args:
            before: Include attempts completed before this datetime (inclusive).
                    None means no upper bound.
            after: Include attempts completed after this datetime (inclusive).
                   None means no lower bound. Attempts with completed_at=None are excluded.

        Returns:
            List of attempts matching the criteria, sorted by attempt_number ascending
            (None values, if any, are excluded).

        Raises:
            ValueError: If before < after.
        """
        if before is not None and after is not None and after > before:
            raise ValueError(f"after ({after}) must be <= before ({before})")

        filtered = [a for a in self._attempts if a.completed_at is not None]
        if after is not None:
            filtered = [a for a in filtered if a.completed_at >= after]
        if before is not None:
            filtered = [a for a in filtered if a.completed_at <= before]

        return sorted(filtered, key=lambda a: a.attempt_number)

    def filter_attempts(
        self,
        run_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        conclusion: Optional[WorkflowConclusion] = None,
        duration_min_seconds: Optional[float] = None,
        duration_max_seconds: Optional[float] = None,
        started_before: Optional[datetime] = None,
        started_after: Optional[datetime] = None,
        completed_before: Optional[datetime] = None,
        completed_after: Optional[datetime] = None,
    ) -> List[WorkflowRunAttempt]:
        """
        Composite filter combining multiple filter criteria (AND logic).

        All provided filters are applied in sequence. Filters with None values
        are skipped.

        Args:
            run_id: Filter by run ID.
            status: Exact match on status.
            conclusion: Exact match on conclusion.
            duration_min_seconds: Minimum duration (inclusive).
            duration_max_seconds: Maximum duration (inclusive).
            started_before: Started before this datetime (inclusive).
            started_after: Started after this datetime (inclusive).
            completed_before: Completed before this datetime (inclusive).
            completed_after: Completed after this datetime (inclusive).

        Returns:
            List of attempts matching all criteria (AND logic), sorted by attempt_number.

        Raises:
            ValueError: If filter parameters are invalid.
        """
        results = self.list_attempts()

        if run_id is not None:
            results = [a for a in results if a.run_id == run_id]

        if status is not None:
            results = [a for a in results if a.status == status]

        if conclusion is not None:
            results = [a for a in results if a.conclusion == conclusion]

        if duration_min_seconds is not None or duration_max_seconds is not None:
            filtered_by_duration = self.filter_by_duration_range(
                duration_min_seconds, duration_max_seconds
            )
            results = [a for a in results if a in filtered_by_duration]

        if started_before is not None or started_after is not None:
            filtered_by_started = self.filter_by_started_at(started_before, started_after)
            results = [a for a in results if a in filtered_by_started]

        if completed_before is not None or completed_after is not None:
            filtered_by_completed = self.filter_by_completed_at(
                completed_before, completed_after
            )
            results = [a for a in results if a in filtered_by_completed]

        return sorted(results, key=lambda a: a.attempt_number)
