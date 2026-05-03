from typing import List, Optional
from datetime import datetime

from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
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

    def validate_attempt_uniqueness(self, attempts: List[WorkflowRunAttempt]) -> bool:
        """Validate that all attempt numbers in the list are unique.

        Args:
            attempts: List of WorkflowRunAttempt objects to validate

        Returns:
            True if all attempt numbers are unique

        Raises:
            ValueError: If duplicate attempt numbers are found
        """
        attempt_numbers = [attempt.attempt_number for attempt in attempts]
        if len(attempt_numbers) != len(set(attempt_numbers)):
            raise ValueError("Attempt numbers must be unique within a workflow run")
        return True

    def filter_runs(
        self,
        branch: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        conclusion: Optional[WorkflowConclusion] = None,
        duration_min: Optional[float] = None,
        duration_max: Optional[float] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        updated_before: Optional[datetime] = None,
        has_attempts: Optional[bool] = None,
    ) -> List[WorkflowRun]:
        """Filter runs by multiple criteria.

        Args:
            branch: Filter by branch name
            status: Filter by workflow status
            conclusion: Filter by workflow conclusion
            duration_min: Minimum duration in seconds (inclusive)
            duration_max: Maximum duration in seconds (inclusive)
            created_after: Filter runs created after this datetime (exclusive)
            created_before: Filter runs created before this datetime (exclusive)
            updated_after: Filter runs updated after this datetime (exclusive), only applies if updated_at is not None
            updated_before: Filter runs updated before this datetime (exclusive), only applies if updated_at is not None
            has_attempts: If True, filter by runs with attempts (len > 0); if False, filter by runs without attempts (len == 0)

        Returns:
            List of filtered WorkflowRun objects
        """
        result = list(self._runs)

        if branch is not None:
            result = [r for r in result if r.branch == branch]

        if status is not None:
            result = [r for r in result if r.status == status]

        if conclusion is not None:
            result = [r for r in result if r.conclusion == conclusion]

        if duration_min is not None:
            result = [r for r in result if r.duration_seconds >= duration_min]

        if duration_max is not None:
            result = [r for r in result if r.duration_seconds <= duration_max]

        if created_after is not None:
            result = [r for r in result if r.created_at > created_after]

        if created_before is not None:
            result = [r for r in result if r.created_at < created_before]

        if updated_after is not None:
            result = [r for r in result if r.updated_at is not None and r.updated_at > updated_after]

        if updated_before is not None:
            result = [r for r in result if r.updated_at is not None and r.updated_at < updated_before]

        if has_attempts is not None:
            if has_attempts:
                result = [r for r in result if len(r.attempts) > 0]
            else:
                result = [r for r in result if len(r.attempts) == 0]

        return result

    def add_workflow_run_attempt(self, run_id: str, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        """Add a workflow run attempt to a specific run.

        Args:
            run_id: The ID of the workflow run
            attempt: The WorkflowRunAttempt to add

        Returns:
            The added WorkflowRunAttempt

        Raises:
            ValueError: If run not found or attempt number already exists in the run
        """
        run = self.get_run_detail(run_id)
        if run is None:
            raise ValueError(f"Run with id '{run_id}' not found.")
        if any(a.attempt_number == attempt.attempt_number for a in run.attempts):
            raise ValueError(
                f"Attempt number {attempt.attempt_number} already exists in run '{run_id}'."
            )
        run.attempts.append(attempt)
        self._persist()
        return attempt
