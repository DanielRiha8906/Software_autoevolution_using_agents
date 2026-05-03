from typing import List, Optional
from datetime import datetime

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..storage.workflow_json_storage import WorkflowJsonStorage


class WorkflowRunService:
    def __init__(self, storage: WorkflowJsonStorage, attempt_service=None):
        self._storage = storage
        self._runs: List[WorkflowRun] = storage.load()
        self._attempt_service = attempt_service

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
        created_before: Optional[datetime] = None,
        created_after: Optional[datetime] = None,
        has_attempts: Optional[bool] = None
    ) -> List[WorkflowRun]:
        """Query workflow runs with multiple optional filters (AND logic).

        Args:
            min_duration: Include runs with duration_seconds >= this value.
            max_duration: Include runs with duration_seconds <= this value.
            created_before: Include runs with created_at < this datetime (must be timezone-aware).
            created_after: Include runs with created_at > this datetime (must be timezone-aware).
            has_attempts: Include runs where attempt_service.get_by_run_id() returns non-empty (True)
                         or empty (False). Requires attempt_service to be set.

        Returns:
            List of WorkflowRun objects matching all filters. Empty list if no matches.

        Raises:
            ValueError: If created_before or created_after are naive (missing tzinfo),
                       or if has_attempts is used without attempt_service.
        """
        result = list(self._runs)

        # Filter by min_duration
        if min_duration is not None:
            result = [r for r in result if r.duration_seconds >= min_duration]

        # Filter by max_duration
        if max_duration is not None:
            result = [r for r in result if r.duration_seconds <= max_duration]

        # Filter by created_before
        if created_before is not None:
            if created_before.tzinfo is None:
                raise ValueError("created_before must be timezone-aware")
            result = [r for r in result if r.created_at < created_before]

        # Filter by created_after
        if created_after is not None:
            if created_after.tzinfo is None:
                raise ValueError("created_after must be timezone-aware")
            result = [r for r in result if r.created_at > created_after]

        # Filter by has_attempts
        if has_attempts is not None:
            if self._attempt_service is None:
                raise ValueError("attempt_service must be set to filter by has_attempts")
            result = [
                r for r in result
                if bool(self._attempt_service.get_by_run_id(r.id)) == has_attempts
            ]

        return result
