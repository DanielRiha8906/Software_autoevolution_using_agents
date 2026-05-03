from typing import List, Optional, Callable
from datetime import datetime
import json
from pathlib import Path

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
        """Filter runs by duration range in seconds.

        Args:
            min_seconds: Minimum duration in seconds (inclusive), or None for no lower bound.
            max_seconds: Maximum duration in seconds (inclusive), or None for no upper bound.

        Returns:
            List of runs matching the duration criteria.
        """
        result = []
        for run in self._runs:
            if min_seconds is not None and run.duration_seconds < min_seconds:
                continue
            if max_seconds is not None and run.duration_seconds > max_seconds:
                continue
            result.append(run)
        return result

    def filter_by_created_before(self, timestamp: datetime) -> List[WorkflowRun]:
        """Filter runs created before a specific timestamp (UTC).

        Args:
            timestamp: Datetime in UTC to filter against.

        Returns:
            List of runs created before the given timestamp.
        """
        return [r for r in self._runs if r.created_at < timestamp]

    def filter_by_created_after(self, timestamp: datetime) -> List[WorkflowRun]:
        """Filter runs created after a specific timestamp (UTC).

        Args:
            timestamp: Datetime in UTC to filter against.

        Returns:
            List of runs created after the given timestamp.
        """
        return [r for r in self._runs if r.created_at > timestamp]

    def filter_by_updated_before(self, timestamp: datetime) -> List[WorkflowRun]:
        """Filter runs updated before a specific timestamp (UTC).

        Args:
            timestamp: Datetime in UTC to filter against.

        Returns:
            List of runs with updated_at before the given timestamp.
        """
        return [r for r in self._runs if r.updated_at and r.updated_at < timestamp]

    def filter_by_updated_after(self, timestamp: datetime) -> List[WorkflowRun]:
        """Filter runs updated after a specific timestamp (UTC).

        Args:
            timestamp: Datetime in UTC to filter against.

        Returns:
            List of runs with updated_at after the given timestamp.
        """
        return [r for r in self._runs if r.updated_at and r.updated_at > timestamp]

    def filter_with_attempts(self, attempt_service) -> List[WorkflowRun]:
        """Filter to runs that have at least one attempt.

        Args:
            attempt_service: The AttemptService instance to query attempts.

        Returns:
            List of runs that have at least one associated attempt.
        """
        # Support both string and integer run_ids from attempts
        attempt_run_ids = set()
        for a in attempt_service.list_attempts():
            attempt_run_ids.add(str(a.run_id))
            attempt_run_ids.add(int(a.run_id) if isinstance(a.run_id, str) and a.run_id.isdigit() else a.run_id)
        return [r for r in self._runs if r.id in attempt_run_ids or (r.id.isdigit() and int(r.id) in attempt_run_ids)]

    def filter_without_attempts(self, attempt_service) -> List[WorkflowRun]:
        """Filter to runs that have no attempts.

        Args:
            attempt_service: The AttemptService instance to query attempts.

        Returns:
            List of runs that have no associated attempts.
        """
        # Support both string and integer run_ids from attempts
        attempt_run_ids = set()
        for a in attempt_service.list_attempts():
            attempt_run_ids.add(str(a.run_id))
            attempt_run_ids.add(int(a.run_id) if isinstance(a.run_id, str) and a.run_id.isdigit() else a.run_id)
        return [r for r in self._runs if r.id not in attempt_run_ids and not (r.id.isdigit() and int(r.id) in attempt_run_ids)]

    def filter_runs(
        self,
        attempt_service=None,
        branch: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        conclusion: Optional[WorkflowConclusion] = None,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        created_before: Optional[datetime] = None,
        created_after: Optional[datetime] = None,
        updated_before: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        has_attempts: Optional[bool] = None,
    ) -> List[WorkflowRun]:
        """Apply multiple filters to workflow runs in a single query.

        All filters are combined with AND logic. If a filter parameter is None, it is ignored.

        Args:
            attempt_service: The AttemptService instance (required if has_attempts is used).
            branch: Filter by branch name (exact match).
            status: Filter by WorkflowStatus.
            conclusion: Filter by WorkflowConclusion.
            min_duration: Minimum duration in seconds (inclusive).
            max_duration: Maximum duration in seconds (inclusive).
            created_before: Filter runs created before this timestamp (UTC).
            created_after: Filter runs created after this timestamp (UTC).
            updated_before: Filter runs updated before this timestamp (UTC).
            updated_after: Filter runs updated after this timestamp (UTC).
            has_attempts: True for runs with attempts, False for runs without, None to ignore.

        Returns:
            List of runs matching all specified criteria.
        """
        result = list(self._runs)

        # Apply each filter in sequence
        if branch is not None:
            result = [r for r in result if r.branch == branch]

        if status is not None:
            result = [r for r in result if r.status == status]

        if conclusion is not None:
            result = [r for r in result if r.conclusion == conclusion]

        if min_duration is not None or max_duration is not None:
            result = [
                r
                for r in result
                if (min_duration is None or r.duration_seconds >= min_duration)
                and (max_duration is None or r.duration_seconds <= max_duration)
            ]

        if created_before is not None:
            result = [r for r in result if r.created_at < created_before]

        if created_after is not None:
            result = [r for r in result if r.created_at > created_after]

        if updated_before is not None:
            result = [r for r in result if r.updated_at and r.updated_at < updated_before]

        if updated_after is not None:
            result = [r for r in result if r.updated_at and r.updated_at > updated_after]

        if has_attempts is not None:
            if attempt_service is None:
                raise ValueError("attempt_service is required when filtering by has_attempts")
            # Support both string and integer run_ids from attempts
            attempt_run_ids = set()
            for a in attempt_service.list_attempts():
                attempt_run_ids.add(str(a.run_id))
                attempt_run_ids.add(int(a.run_id) if isinstance(a.run_id, str) and a.run_id.isdigit() else a.run_id)
            if has_attempts:
                result = [r for r in result if r.id in attempt_run_ids or (r.id.isdigit() and int(r.id) in attempt_run_ids)]
            else:
                result = [r for r in result if r.id not in attempt_run_ids and not (r.id.isdigit() and int(r.id) in attempt_run_ids)]

        return result

    def export_runs(self, filepath: str) -> int:
        """Export all workflow runs to a JSON file.

        Args:
            filepath: Path where the JSON file will be written.

        Returns:
            Number of runs exported.
        """
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = [run.to_dict() for run in self._runs]
        output_path.write_text(json.dumps(data, indent=2))
        return len(data)

    def import_runs(self, filepath: str, skip_duplicates: bool = False) -> tuple[int, List[str]]:
        """Import workflow runs from a JSON file.

        Args:
            filepath: Path to the JSON file to import from.
            skip_duplicates: If True, skip runs that already exist (by ID).
                           If False, raise ValueError on duplicate.

        Returns:
            Tuple of (number_imported, list_of_errors).
            Errors are strings describing validation or duplicate issues.
        """
        input_path = Path(filepath)
        if not input_path.exists():
            raise FileNotFoundError(f"Import file not found: {filepath}")

        try:
            raw_data = json.loads(input_path.read_text())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in import file: {e}")

        if not isinstance(raw_data, list):
            raise ValueError("Import file must contain a JSON array of runs")

        imported_count = 0
        errors = []

        for i, item in enumerate(raw_data):
            try:
                # Validate structure
                if not isinstance(item, dict):
                    errors.append(f"Item {i}: not a dictionary")
                    continue

                # Try to deserialize
                run = WorkflowRun.from_dict(item)

                # Check for duplicates
                if any(r.id == run.id for r in self._runs):
                    if skip_duplicates:
                        errors.append(f"Item {i}: run with id '{run.id}' already exists (skipped)")
                        continue
                    else:
                        raise ValueError(f"Run with id '{run.id}' already exists")

                self._runs.append(run)
                imported_count += 1
            except (KeyError, ValueError, TypeError) as e:
                errors.append(f"Item {i}: {str(e)}")

        if imported_count > 0:
            self._persist()

        return imported_count, errors
