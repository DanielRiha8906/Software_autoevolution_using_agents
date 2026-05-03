from typing import List, Optional
from datetime import datetime

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..storage.workflow_json_storage import WorkflowJsonStorage
from .attempt_service import AttemptService


class WorkflowRunService:
    def __init__(self, storage: WorkflowJsonStorage, attempt_service: Optional[AttemptService] = None):
        self._storage = storage
        self._runs: List[WorkflowRun] = storage.load()
        self._attempt_service = attempt_service

    @property
    def attempt_service(self) -> Optional[AttemptService]:
        """Get the attempt service instance."""
        return self._attempt_service

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
        has_attempts: Optional[bool] = None,
    ) -> List[WorkflowRun]:
        """Query workflow runs with multiple filters using AND logic.

        Args:
            min_duration: Minimum duration in seconds (inclusive).
            max_duration: Maximum duration in seconds (inclusive).
            created_before: Filter runs created before this datetime (inclusive).
            created_after: Filter runs created after this datetime (inclusive).
            has_attempts: If True, only include runs with ≥1 attempt. If False, only include runs with 0 attempts.

        Returns:
            A list of WorkflowRun objects matching all provided filters.

        Raises:
            ValueError: If created_before or created_after are naive datetimes.
        """
        if created_before is not None and created_before.tzinfo is None:
            raise ValueError("created_before must be timezone-aware")
        if created_after is not None and created_after.tzinfo is None:
            raise ValueError("created_after must be timezone-aware")

        result = []

        for run in self._runs:
            if min_duration is not None and run.duration_seconds < min_duration:
                continue
            if max_duration is not None and run.duration_seconds > max_duration:
                continue

            if created_before is not None and run.created_at > created_before:
                continue

            if created_after is not None and run.created_at < created_after:
                continue

            if has_attempts is not None and self._attempt_service is not None:
                attempts = self._attempt_service.get_by_run_id(run.id)
                has_any_attempts = len(attempts) > 0

                if has_attempts and not has_any_attempts:
                    continue
                if not has_attempts and has_any_attempts:
                    continue

            result.append(run)

        return result
