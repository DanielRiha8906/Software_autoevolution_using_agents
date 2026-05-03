from typing import List, Optional
from datetime import datetime, timezone

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

    @staticmethod
    def _normalize_datetime(dt: datetime) -> datetime:
        """Normalize datetime to UTC-aware for consistent comparison.

        If dt is naive, assumes UTC and returns with UTC tzinfo.
        If dt is TZ-aware, returns as-is.
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def filter_by_duration_range(
        self,
        min_duration_seconds: Optional[float] = None,
        max_duration_seconds: Optional[float] = None,
    ) -> List[WorkflowRun]:
        """Filter runs by duration range.

        Args:
            min_duration_seconds: Minimum duration (inclusive). If None, defaults to 0.
            max_duration_seconds: Maximum duration (inclusive). If None, no upper limit.

        Returns:
            List of runs where duration is within [min, max].

        Raises:
            ValueError: If min < 0, max < 0, or min > max.
        """
        min_duration = min_duration_seconds if min_duration_seconds is not None else 0.0
        max_duration = max_duration_seconds if max_duration_seconds is not None else float('inf')

        if min_duration < 0:
            raise ValueError(f"min_duration_seconds must be non-negative, got {min_duration_seconds}")
        if max_duration < 0:
            raise ValueError(f"max_duration_seconds must be non-negative, got {max_duration_seconds}")
        if min_duration > max_duration:
            raise ValueError(
                f"min_duration_seconds ({min_duration_seconds}) must be <= "
                f"max_duration_seconds ({max_duration_seconds})"
            )

        return [
            r for r in self._runs
            if min_duration <= r.duration_seconds <= max_duration
        ]

    def filter_by_created_after(self, cutoff_datetime: datetime) -> List[WorkflowRun]:
        """Filter runs created after cutoff_datetime.

        Args:
            cutoff_datetime: Datetime cutoff (naive assumed UTC).

        Returns:
            List of runs where created_at > cutoff_datetime.
        """
        normalized_cutoff = self._normalize_datetime(cutoff_datetime)
        return [
            r for r in self._runs
            if self._normalize_datetime(r.created_at) > normalized_cutoff
        ]

    def filter_by_created_before(self, cutoff_datetime: datetime) -> List[WorkflowRun]:
        """Filter runs created before cutoff_datetime.

        Args:
            cutoff_datetime: Datetime cutoff (naive assumed UTC).

        Returns:
            List of runs where created_at < cutoff_datetime.
        """
        normalized_cutoff = self._normalize_datetime(cutoff_datetime)
        return [
            r for r in self._runs
            if self._normalize_datetime(r.created_at) < normalized_cutoff
        ]

    def filter_by_updated_after(self, cutoff_datetime: datetime) -> List[WorkflowRun]:
        """Filter runs updated after cutoff_datetime.

        Args:
            cutoff_datetime: Datetime cutoff (naive assumed UTC).

        Returns:
            List of runs where updated_at is not None AND updated_at > cutoff_datetime.
        """
        normalized_cutoff = self._normalize_datetime(cutoff_datetime)
        return [
            r for r in self._runs
            if r.updated_at is not None and self._normalize_datetime(r.updated_at) > normalized_cutoff
        ]

    def filter_by_updated_before(self, cutoff_datetime: datetime) -> List[WorkflowRun]:
        """Filter runs updated before cutoff_datetime.

        Args:
            cutoff_datetime: Datetime cutoff (naive assumed UTC).

        Returns:
            List of runs where updated_at is not None AND updated_at < cutoff_datetime.
        """
        normalized_cutoff = self._normalize_datetime(cutoff_datetime)
        return [
            r for r in self._runs
            if r.updated_at is not None and self._normalize_datetime(r.updated_at) < normalized_cutoff
        ]

    def filter_by_has_attempts(
        self,
        attempt_service: 'AttemptService',
        has_attempts: bool = True,
    ) -> List[WorkflowRun]:
        """Filter runs by whether they have attempts.

        Args:
            attempt_service: AttemptService instance to look up attempts.
            has_attempts: If True, return runs with at least one attempt.
                         If False, return runs with zero attempts.

        Returns:
            Filtered list of runs based on attempt presence.
        """
        result = []
        for run in self._runs:
            # Handle both string and int run_id by converting to int for lookup
            try:
                run_id_int = int(run.id) if isinstance(run.id, str) else run.id
            except (ValueError, TypeError):
                # If run.id cannot be converted to int, skip it
                continue

            attempts = attempt_service.get_attempts_by_run_id(run_id_int)
            has_any_attempts = len(attempts) > 0

            if has_attempts and has_any_attempts:
                result.append(run)
            elif not has_attempts and not has_any_attempts:
                result.append(run)

        return result

    def filter_runs(
        self,
        attempt_service: Optional['AttemptService'] = None,
        branch: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        conclusion: Optional[WorkflowConclusion] = None,
        min_duration_seconds: Optional[float] = None,
        max_duration_seconds: Optional[float] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        updated_before: Optional[datetime] = None,
        has_attempts: Optional[bool] = None,
    ) -> List[WorkflowRun]:
        """Compound filter accepting all criteria.

        Applies all provided filters in sequence (AND logic).

        Args:
            attempt_service: Required if has_attempts is not None.
            branch: Filter by branch name.
            status: Filter by WorkflowStatus.
            conclusion: Filter by WorkflowConclusion.
            min_duration_seconds: Minimum duration.
            max_duration_seconds: Maximum duration.
            created_after: Runs created after this datetime.
            created_before: Runs created before this datetime.
            updated_after: Runs updated after this datetime.
            updated_before: Runs updated before this datetime.
            has_attempts: Filter by attempt presence.

        Returns:
            List of runs matching all provided criteria.

        Raises:
            ValueError: If attempt_service is None and has_attempts is not None.
            ValueError: If duration range validation fails.
        """
        if has_attempts is not None and attempt_service is None:
            raise ValueError(
                "attempt_service must be provided if has_attempts filter is used"
            )

        # Validate duration range early
        if min_duration_seconds is not None or max_duration_seconds is not None:
            min_duration = min_duration_seconds if min_duration_seconds is not None else 0.0
            max_duration = max_duration_seconds if max_duration_seconds is not None else float('inf')

            if min_duration < 0:
                raise ValueError(f"min_duration_seconds must be non-negative, got {min_duration_seconds}")
            if max_duration < 0:
                raise ValueError(f"max_duration_seconds must be non-negative, got {max_duration_seconds}")
            if min_duration > max_duration:
                raise ValueError(
                    f"min_duration_seconds ({min_duration_seconds}) must be <= "
                    f"max_duration_seconds ({max_duration_seconds})"
                )

        # Start with all runs
        results = self.list_runs()

        # Apply each filter in sequence
        if branch is not None:
            results = [r for r in results if r.branch == branch]

        if status is not None:
            results = [r for r in results if r.status == status]

        if conclusion is not None:
            results = [r for r in results if r.conclusion == conclusion]

        if min_duration_seconds is not None or max_duration_seconds is not None:
            filtered = self.filter_by_duration_range(min_duration_seconds, max_duration_seconds)
            results = [r for r in results if r in filtered]

        if created_after is not None:
            filtered = self.filter_by_created_after(created_after)
            results = [r for r in results if r in filtered]

        if created_before is not None:
            filtered = self.filter_by_created_before(created_before)
            results = [r for r in results if r in filtered]

        if updated_after is not None:
            filtered = self.filter_by_updated_after(updated_after)
            results = [r for r in results if r in filtered]

        if updated_before is not None:
            filtered = self.filter_by_updated_before(updated_before)
            results = [r for r in results if r in filtered]

        if has_attempts is not None:
            filtered = self.filter_by_has_attempts(attempt_service, has_attempts)
            results = [r for r in results if r in filtered]

        return results
