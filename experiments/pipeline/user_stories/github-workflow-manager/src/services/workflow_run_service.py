from typing import List, Optional
from datetime import datetime

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..storage.base import WorkflowRunStorage
from .workflow_run_attempt_service import WorkflowRunAttemptService


class WorkflowRunService:
    def __init__(self, storage: WorkflowRunStorage):
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

    def replace_run(self, run: WorkflowRun) -> None:
        """Replace existing run or add if not exists. For import operations."""
        self._runs = [r for r in self._runs if r.id != run.id]
        self._runs.append(run)
        self._persist()

    def delete_run(self, run_id: str) -> bool:
        """Delete run by id. Returns True if deleted, False if not found."""
        original_count = len(self._runs)
        self._runs = [r for r in self._runs if r.id != run_id]
        if len(self._runs) < original_count:
            self._persist()
            return True
        return False

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

    def filter_by_created_after(self, threshold_date: datetime) -> List[WorkflowRun]:
        """Filter runs created on or after the given date."""
        return [r for r in self._runs if r.created_at >= threshold_date]

    def filter_by_created_before(self, threshold_date: datetime) -> List[WorkflowRun]:
        """Filter runs created on or before the given date."""
        return [r for r in self._runs if r.created_at <= threshold_date]

    def filter_by_duration_min(self, min_seconds: float) -> List[WorkflowRun]:
        """Filter runs with duration greater than or equal to the minimum."""
        return [r for r in self._runs if r.duration_seconds >= min_seconds]

    def filter_by_duration_max(self, max_seconds: float) -> List[WorkflowRun]:
        """Filter runs with duration less than or equal to the maximum."""
        return [r for r in self._runs if r.duration_seconds <= max_seconds]

    def filter_by_attempt_presence(self, attempt_service: WorkflowRunAttemptService, has_attempts: bool) -> List[WorkflowRun]:
        """
        Filter runs based on whether they have attempts.

        Args:
            attempt_service: The service managing workflow run attempts
            has_attempts: If True, return runs with at least one attempt; if False, return runs with no attempts

        Returns:
            List of WorkflowRun objects matching the attempt presence criterion

        Note:
            Handles type mismatch between WorkflowRun.id (str) and WorkflowRunAttempt.run_id (int).
            Only runs with numeric IDs can match attempts; UUID string IDs will be treated as having no attempts.
        """
        run_ids_with_attempts = {a.run_id for a in attempt_service.list_attempts(sorted=False)}

        result = []
        for r in self._runs:
            # Try to convert run.id to int; if it fails, treat as no attempts
            try:
                run_id_int = int(r.id)
                has_attempt = run_id_int in run_ids_with_attempts
            except (ValueError, TypeError):
                # Cannot convert to int (e.g., UUID string), so treat as no attempts
                has_attempt = False

            if has_attempts and has_attempt:
                result.append(r)
            elif not has_attempts and not has_attempt:
                result.append(r)

        return result

    def query(
        self,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        duration_min: Optional[float] = None,
        duration_max: Optional[float] = None,
        attempt_service: Optional[WorkflowRunAttemptService] = None,
        has_attempts: Optional[bool] = None,
        branch: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        conclusion: Optional[WorkflowConclusion] = None,
    ) -> List[WorkflowRun]:
        """
        Composite query method that applies all provided filters.
        All filters are AND-ed together.

        Args:
            created_after: Filter runs created on or after this date
            created_before: Filter runs created on or before this date
            duration_min: Filter runs with duration >= this value in seconds
            duration_max: Filter runs with duration <= this value in seconds
            attempt_service: Service for checking attempt presence (required if has_attempts is not None)
            has_attempts: If True, include only runs with attempts; if False, only runs without
            branch: Filter by branch name
            status: Filter by WorkflowStatus
            conclusion: Filter by WorkflowConclusion

        Returns:
            List of WorkflowRun objects matching all specified criteria
        """
        results = list(self._runs)

        if created_after:
            results = [r for r in results if r.created_at >= created_after]

        if created_before:
            results = [r for r in results if r.created_at <= created_before]

        if duration_min is not None:
            results = [r for r in results if r.duration_seconds >= duration_min]

        if duration_max is not None:
            results = [r for r in results if r.duration_seconds <= duration_max]

        if branch:
            results = [r for r in results if r.branch == branch]

        if status:
            results = [r for r in results if r.status == status]

        if conclusion:
            results = [r for r in results if r.conclusion == conclusion]

        if has_attempts is not None:
            if attempt_service is None:
                raise ValueError("attempt_service must be provided when has_attempts filter is used")
            run_ids_with_attempts = {a.run_id for a in attempt_service.list_attempts(sorted=False)}

            filtered_results = []
            for r in results:
                # Try to convert run.id to int; if it fails, treat as no attempts
                try:
                    run_id_int = int(r.id)
                    has_attempt = run_id_int in run_ids_with_attempts
                except (ValueError, TypeError):
                    # Cannot convert to int (e.g., UUID string), so treat as no attempts
                    has_attempt = False

                if has_attempts and has_attempt:
                    filtered_results.append(r)
                elif not has_attempts and not has_attempt:
                    filtered_results.append(r)

            results = filtered_results

        return results
