from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..storage.workflow_json_storage import WorkflowJsonStorage

if TYPE_CHECKING:
    from .attempt_service import AttemptService


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

    def query(
        self,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        has_attempts: Optional[bool] = None,
        attempt_service: Optional["AttemptService"] = None,
    ) -> List[WorkflowRun]:
        """
        Filter workflow runs by duration, timestamp, and attempt presence.

        Args:
            min_duration: Minimum duration_seconds (inclusive). None = no minimum.
            max_duration: Maximum duration_seconds (inclusive). None = no maximum.
            created_after: Runs created strictly after this datetime (exclusive).
                           Expected to be timezone-aware.
            created_before: Runs created strictly before this datetime (exclusive).
                            Expected to be timezone-aware.
            has_attempts: If True, return runs with ≥1 attempts.
                          If False, return runs with 0 attempts.
                          If None, ignore attempt count.
            attempt_service: Required if has_attempts is not None.
                             Provides access to attempt data.

        Returns:
            List of WorkflowRun objects matching all specified filters.
            Returns empty list if no matches found.
            Filters are combined with AND logic (all must match).

        Raises:
            ValueError: If has_attempts is not None but attempt_service is None.
            ValueError: If created_after >= created_before (both provided).
            ValueError: If min_duration > max_duration (both provided).
            TypeError: If datetime arguments are not timezone-aware.
        """
        # Validation step 1: Check timezone awareness for datetime arguments
        if created_after is not None and created_after.tzinfo is None:
            raise TypeError("created_after must be timezone-aware")
        if created_before is not None and created_before.tzinfo is None:
            raise TypeError("created_before must be timezone-aware")

        # Validation step 2: Check date range validity
        if created_after is not None and created_before is not None:
            if created_after >= created_before:
                raise ValueError("created_after must be strictly before created_before")

        # Validation step 3: Check duration range validity
        if min_duration is not None and max_duration is not None:
            if min_duration > max_duration:
                raise ValueError("min_duration must not be greater than max_duration")

        # Validation step 4: Check attempt_service presence
        if has_attempts is not None and attempt_service is None:
            raise ValueError("attempt_service required when filtering by has_attempts")

        # Start with all runs
        results = list(self._runs)

        # Apply duration filter
        if min_duration is not None:
            results = [r for r in results if r.duration_seconds >= min_duration]
        if max_duration is not None:
            results = [r for r in results if r.duration_seconds <= max_duration]

        # Apply timestamp filter
        if created_after is not None:
            # Check that created_at is timezone-aware
            results = [
                r for r in results
                if r.created_at.tzinfo is not None and r.created_at > created_after
            ]
        if created_before is not None:
            # Check that created_at is timezone-aware
            results = [
                r for r in results
                if r.created_at.tzinfo is not None and r.created_at < created_before
            ]

        # Apply attempt presence filter
        if has_attempts is not None:
            filtered = []
            for run in results:
                try:
                    attempts = attempt_service.get_by_run_id(int(run.id))
                    run_has_attempts = len(attempts) >= 1
                    if run_has_attempts == has_attempts:
                        filtered.append(run)
                except (ValueError, TypeError):
                    # If run.id cannot convert to int, skip this run
                    pass
            results = filtered

        return results
