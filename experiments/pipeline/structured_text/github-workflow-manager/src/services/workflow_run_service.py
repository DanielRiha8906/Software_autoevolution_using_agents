from typing import List, Optional
from datetime import datetime

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..storage.workflow_json_storage import WorkflowJsonStorage


class WorkflowRunService:
    def __init__(self, storage: WorkflowJsonStorage):
        self._storage = storage
        self._runs: List[WorkflowRun] = storage.load()

    def _persist(self) -> None:
        self._storage.save(self._runs)

    def add_workflow_run(self, run: WorkflowRun) -> WorkflowRun:
        if any(r.id == run.id for r in self._runs):
            raise ValueError(f"Run with id '{run.id}' already exists.")
        self._runs.append(run)
        self._persist()
        return run

    def list_runs(self) -> List[WorkflowRun]:
        return list(self._runs)

    def get_run_detail(self, run_id: str) -> Optional[WorkflowRun]:
        return next((r for r in self._runs if r.id == run_id), None)

    def filter_by_branch(self, branch: str) -> List[WorkflowRun]:
        return [r for r in self._runs if r.branch == branch]

    def filter_by_status(self, status: WorkflowStatus) -> List[WorkflowRun]:
        return [r for r in self._runs if r.status == status]

    def filter_by_conclusion(self, conclusion: WorkflowConclusion) -> List[WorkflowRun]:
        return [r for r in self._runs if r.conclusion == conclusion]

    def filter_by_duration_range(
        self, min_seconds: Optional[float] = None, max_seconds: Optional[float] = None
    ) -> List[WorkflowRun]:
        """
        Filter runs by duration range (in seconds).

        Args:
            min_seconds: Minimum duration (inclusive). None means no lower bound.
            max_seconds: Maximum duration (inclusive). None means no upper bound.

        Returns:
            List of runs matching the duration criteria, sorted by duration ascending.

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

        filtered = self._runs
        if min_seconds is not None:
            filtered = [r for r in filtered if r.duration_seconds >= min_seconds]
        if max_seconds is not None:
            filtered = [r for r in filtered if r.duration_seconds <= max_seconds]

        return sorted(filtered, key=lambda r: r.duration_seconds)

    def filter_by_created_at(
        self, before: Optional[datetime] = None, after: Optional[datetime] = None
    ) -> List[WorkflowRun]:
        """
        Filter runs by creation timestamp.

        Args:
            before: Include runs created before this datetime (inclusive).
                    None means no upper bound.
            after: Include runs created after this datetime (inclusive).
                   None means no lower bound.

        Returns:
            List of runs matching the criteria, sorted by created_at ascending.

        Raises:
            ValueError: If before < after.
        """
        if before is not None and after is not None and after > before:
            raise ValueError(f"after ({after}) must be <= before ({before})")

        filtered = self._runs
        if after is not None:
            filtered = [r for r in filtered if r.created_at >= after]
        if before is not None:
            filtered = [r for r in filtered if r.created_at <= before]

        return sorted(filtered, key=lambda r: r.created_at)

    def filter_by_updated_at(
        self, before: Optional[datetime] = None, after: Optional[datetime] = None
    ) -> List[WorkflowRun]:
        """
        Filter runs by last update timestamp.

        Args:
            before: Include runs updated before this datetime (inclusive).
                    None means no upper bound.
            after: Include runs updated after this datetime (inclusive).
                   None means no lower bound. Runs with updated_at=None are excluded.

        Returns:
            List of runs matching the criteria, sorted by updated_at ascending
            (None values, if any, are excluded).

        Raises:
            ValueError: If before < after.
        """
        if before is not None and after is not None and after > before:
            raise ValueError(f"after ({after}) must be <= before ({before})")

        filtered = [r for r in self._runs if r.updated_at is not None]
        if after is not None:
            filtered = [r for r in filtered if r.updated_at >= after]
        if before is not None:
            filtered = [r for r in filtered if r.updated_at <= before]

        return sorted(filtered, key=lambda r: r.updated_at)

    def filter_by_has_attempts(
        self, has_attempts: bool, attempt_service: "WorkflowAttemptService"
    ) -> List[WorkflowRun]:
        """
        Filter runs by presence or absence of attempts.

        Args:
            has_attempts: If True, return runs with at least one attempt.
                          If False, return runs with no attempts.
            attempt_service: WorkflowAttemptService instance to query attempts.

        Returns:
            List of runs matching the criteria, in original order.

        Raises:
            ValueError: If attempt_service is None.
        """
        if attempt_service is None:
            raise ValueError("attempt_service cannot be None")

        all_attempts = attempt_service.list_attempts()
        run_ids_with_attempts = {a.run_id for a in all_attempts}

        if has_attempts:
            return [r for r in self._runs if r.id in run_ids_with_attempts]
        else:
            return [r for r in self._runs if r.id not in run_ids_with_attempts]

    def filter_runs(
        self,
        branch: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        conclusion: Optional[WorkflowConclusion] = None,
        duration_min_seconds: Optional[float] = None,
        duration_max_seconds: Optional[float] = None,
        created_before: Optional[datetime] = None,
        created_after: Optional[datetime] = None,
        updated_before: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        with_attempts: Optional[bool] = None,
        attempt_service: Optional["WorkflowAttemptService"] = None,
    ) -> List[WorkflowRun]:
        """
        Composite filter combining multiple filter criteria (AND logic).

        All provided filters are applied in sequence. Filters with None values
        are skipped.

        Args:
            branch: Exact match on branch name.
            status: Exact match on status.
            conclusion: Exact match on conclusion.
            duration_min_seconds: Minimum duration (inclusive).
            duration_max_seconds: Maximum duration (inclusive).
            created_before: Created before this datetime (inclusive).
            created_after: Created after this datetime (inclusive).
            updated_before: Updated before this datetime (inclusive).
            updated_after: Updated after this datetime (inclusive).
            with_attempts: If True, include only runs with attempts.
                           If False, include only runs without attempts.
                           If None, no filtering by attempts.
            attempt_service: Required if with_attempts is not None.

        Returns:
            List of runs matching all criteria (AND logic).

        Raises:
            ValueError: If filter parameters are invalid.
        """
        results = self.list_runs()

        if branch is not None:
            results = [r for r in results if r.branch == branch]

        if status is not None:
            results = [r for r in results if r.status == status]

        if conclusion is not None:
            results = [r for r in results if r.conclusion == conclusion]

        if duration_min_seconds is not None or duration_max_seconds is not None:
            # Apply range filter manually to preserve results
            filtered_by_duration = self.filter_by_duration_range(
                duration_min_seconds, duration_max_seconds
            )
            results = [r for r in results if r in filtered_by_duration]

        if created_before is not None or created_after is not None:
            filtered_by_created = self.filter_by_created_at(created_before, created_after)
            results = [r for r in results if r in filtered_by_created]

        if updated_before is not None or updated_after is not None:
            filtered_by_updated = self.filter_by_updated_at(updated_before, updated_after)
            results = [r for r in results if r in filtered_by_updated]

        if with_attempts is not None:
            filtered_by_attempts = self.filter_by_has_attempts(with_attempts, attempt_service)
            results = [r for r in results if r in filtered_by_attempts]

        return results
