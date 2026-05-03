import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.import_result import ImportResult
from .workflow_run_service import WorkflowRunService
from .workflow_run_attempt_service import WorkflowRunAttemptService


class WorkflowRunExportImportService:
    """Service for exporting and importing workflow runs and attempts to/from JSON files."""

    def __init__(self) -> None:
        pass

    def export_to_file(
        self,
        filepath: str,
        service: WorkflowRunService,
        attempt_service: Optional[WorkflowRunAttemptService] = None,
        include_attempts: bool = False
    ) -> None:
        """
        Export workflow runs (and optionally attempts) to a JSON file.

        Args:
            filepath: Output file path
            service: WorkflowRunService instance
            attempt_service: WorkflowRunAttemptService instance (required if include_attempts=True)
            include_attempts: If True, also export attempts to <filepath>_attempts.json

        Raises:
            IOError: If unable to write to file
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        runs = service.list_runs()
        data = [run.to_dict() for run in runs]

        try:
            Path(filepath).write_text(json.dumps(data, indent=2))
        except IOError as e:
            raise IOError(f"Failed to write runs to {filepath}: {e}")

        if include_attempts and attempt_service is not None:
            attempts = attempt_service.list_attempts(sorted=False)
            attempts_data = [attempt.to_dict() for attempt in attempts]
            attempts_filepath = f"{filepath[:-5]}_attempts.json" if filepath.endswith(".json") else f"{filepath}_attempts.json"
            try:
                Path(attempts_filepath).write_text(json.dumps(attempts_data, indent=2))
            except IOError as e:
                raise IOError(f"Failed to write attempts to {attempts_filepath}: {e}")

    def import_from_file(
        self,
        filepath: str,
        service: WorkflowRunService,
        attempt_service: Optional[WorkflowRunAttemptService] = None,
        overwrite: bool = False,
        dry_run: bool = False
    ) -> ImportResult:
        """
        Import workflow runs (and optionally attempts) from a JSON file.

        Args:
            filepath: Input file path
            service: WorkflowRunService instance
            attempt_service: WorkflowRunAttemptService instance
            overwrite: If True, replace existing runs with same id
            dry_run: If True, validate without persisting

        Returns:
            ImportResult with metadata about the import

        Raises:
            FileNotFoundError: If input file does not exist
            ValueError: If JSON is malformed
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            data = json.loads(Path(filepath).read_text())
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed JSON in {filepath}: {e}")

        if not isinstance(data, list):
            raise ValueError(f"JSON in {filepath} must be a list of runs")

        imported_runs = 0
        skipped_runs = 0
        errors: List[str] = []

        for i, run_data in enumerate(data):
            try:
                run = self._validate_and_build_run(run_data, i)
            except ValueError as e:
                skipped_runs += 1
                errors.append(str(e))
                continue

            existing = service.get_run_detail(run.id)
            if existing is not None:
                if not overwrite:
                    skipped_runs += 1
                    errors.append(f"Record {i}: Run with id '{run.id}' already exists (use --overwrite to replace)")
                    continue
                else:
                    if not dry_run:
                        service._runs = [r for r in service._runs if r.id != run.id]
                        service._runs.append(run)
                        service._persist()
                    imported_runs += 1
            else:
                if not dry_run:
                    service._runs.append(run)
                    service._persist()
                imported_runs += 1

        imported_attempts = 0
        skipped_attempts = 0

        attempts_filepath = f"{filepath[:-5]}_attempts.json" if filepath.endswith(".json") else f"{filepath}_attempts.json"
        if Path(attempts_filepath).exists() and attempt_service is not None:
            try:
                attempts_data = json.loads(Path(attempts_filepath).read_text())
            except json.JSONDecodeError as e:
                raise ValueError(f"Malformed JSON in {attempts_filepath}: {e}")

            if not isinstance(attempts_data, list):
                raise ValueError(f"JSON in {attempts_filepath} must be a list of attempts")

            for i, attempt_data in enumerate(attempts_data):
                try:
                    attempt = self._validate_and_build_attempt(attempt_data, i)
                except ValueError as e:
                    skipped_attempts += 1
                    errors.append(str(e))
                    continue

                existing_attempt = attempt_service.get_attempt(attempt.id)
                if existing_attempt is not None:
                    if not overwrite:
                        skipped_attempts += 1
                        errors.append(f"Record {i}: Attempt with id {attempt.id} already exists (use --overwrite to replace)")
                        continue
                    else:
                        if not dry_run:
                            attempt_service._attempts = [a for a in attempt_service._attempts if a.id != attempt.id]
                            attempt_service._attempts.append(attempt)
                            attempt_service._persist()
                        imported_attempts += 1
                else:
                    if not dry_run:
                        attempt_service._attempts.append(attempt)
                        attempt_service._persist()
                    imported_attempts += 1

        return ImportResult(
            filepath=filepath,
            total_records=len(data),
            imported_runs=imported_runs,
            skipped_runs=skipped_runs,
            imported_attempts=imported_attempts,
            skipped_attempts=skipped_attempts,
            errors=errors,
            had_overwrite=overwrite,
        )

    def _validate_and_build_run(self, data: dict, record_index: int) -> WorkflowRun:
        """
        Validate a run dictionary and build a WorkflowRun instance.

        Args:
            data: Dictionary containing run data
            record_index: Index of record in file (for error messages)

        Returns:
            WorkflowRun instance

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValueError(f"Record {record_index}: Run data must be a dictionary")

        required_fields = ["id", "workflow_name", "branch", "status", "created_at"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Record {record_index}: Missing required field '{field}'")

        run_id = data.get("id")
        if not isinstance(run_id, str) or not run_id:
            raise ValueError(f"Record {record_index}: 'id' must be a non-empty string")

        workflow_name = data.get("workflow_name")
        if not isinstance(workflow_name, str) or not workflow_name:
            raise ValueError(f"Record {record_index}: 'workflow_name' must be a non-empty string")

        branch = data.get("branch")
        if not isinstance(branch, str) or not branch:
            raise ValueError(f"Record {record_index}: 'branch' must be a non-empty string")

        status_val = data.get("status")
        if not isinstance(status_val, str):
            raise ValueError(f"Record {record_index}: 'status' must be a string")
        try:
            status = WorkflowStatus(status_val)
        except ValueError:
            raise ValueError(f"Record {record_index}: Invalid status '{status_val}'. Must be one of: {', '.join([s.value for s in WorkflowStatus])}")

        conclusion_val = data.get("conclusion")
        if conclusion_val is not None:
            if not isinstance(conclusion_val, str):
                raise ValueError(f"Record {record_index}: 'conclusion' must be a string or null")
            try:
                conclusion = WorkflowConclusion(conclusion_val)
            except ValueError:
                raise ValueError(f"Record {record_index}: Invalid conclusion '{conclusion_val}'. Must be one of: {', '.join([c.value for c in WorkflowConclusion])}")
        else:
            conclusion = None

        created_at_str = data.get("created_at")
        if not isinstance(created_at_str, str):
            raise ValueError(f"Record {record_index}: 'created_at' must be an ISO format datetime string")
        try:
            created_at = datetime.fromisoformat(created_at_str)
        except ValueError:
            raise ValueError(f"Record {record_index}: 'created_at' is not a valid ISO format datetime: '{created_at_str}'")

        updated_at_str = data.get("updated_at")
        if updated_at_str is not None:
            if not isinstance(updated_at_str, str):
                raise ValueError(f"Record {record_index}: 'updated_at' must be an ISO format datetime string or null")
            try:
                updated_at = datetime.fromisoformat(updated_at_str)
            except ValueError:
                raise ValueError(f"Record {record_index}: 'updated_at' is not a valid ISO format datetime: '{updated_at_str}'")
        else:
            updated_at = None

        run_number = data.get("run_number")
        if run_number is not None and not isinstance(run_number, int):
            raise ValueError(f"Record {record_index}: 'run_number' must be an integer or null")

        commit_sha = data.get("commit_sha")
        if commit_sha is not None and not isinstance(commit_sha, str):
            raise ValueError(f"Record {record_index}: 'commit_sha' must be a string or null")

        duration_seconds = data.get("duration_seconds", 0.0)
        if not isinstance(duration_seconds, (int, float)):
            raise ValueError(f"Record {record_index}: 'duration_seconds' must be a number")
        if duration_seconds < 0:
            raise ValueError(f"Record {record_index}: 'duration_seconds' must be non-negative")

        return WorkflowRun(
            id=run_id,
            workflow_name=workflow_name,
            branch=branch,
            status=status,
            conclusion=conclusion,
            created_at=created_at,
            updated_at=updated_at,
            run_number=run_number,
            commit_sha=commit_sha,
            duration_seconds=float(duration_seconds),
        )

    def _validate_and_build_attempt(self, data: dict, record_index: int) -> WorkflowRunAttempt:
        """
        Validate an attempt dictionary and build a WorkflowRunAttempt instance.

        Args:
            data: Dictionary containing attempt data
            record_index: Index of record in file (for error messages)

        Returns:
            WorkflowRunAttempt instance

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValueError(f"Record {record_index}: Attempt data must be a dictionary")

        required_fields = ["id", "run_id", "attempt_number", "status", "created_at"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Record {record_index}: Missing required field '{field}'")

        attempt_id = data.get("id")
        if not isinstance(attempt_id, int):
            raise ValueError(f"Record {record_index}: 'id' must be an integer")

        run_id = data.get("run_id")
        if not isinstance(run_id, int):
            raise ValueError(f"Record {record_index}: 'run_id' must be an integer")

        attempt_number = data.get("attempt_number")
        if not isinstance(attempt_number, int) or attempt_number < 1:
            raise ValueError(f"Record {record_index}: 'attempt_number' must be a positive integer (>= 1)")

        status = data.get("status")
        if not isinstance(status, str) or not status:
            raise ValueError(f"Record {record_index}: 'status' must be a non-empty string")

        conclusion = data.get("conclusion")
        if conclusion is not None and not isinstance(conclusion, str):
            raise ValueError(f"Record {record_index}: 'conclusion' must be a string or null")

        created_at_str = data.get("created_at")
        if not isinstance(created_at_str, str):
            raise ValueError(f"Record {record_index}: 'created_at' must be an ISO format datetime string")
        try:
            created_at = datetime.fromisoformat(created_at_str)
        except ValueError:
            raise ValueError(f"Record {record_index}: 'created_at' is not a valid ISO format datetime: '{created_at_str}'")

        duration_seconds = data.get("duration_seconds", 0.0)
        if not isinstance(duration_seconds, (int, float)):
            raise ValueError(f"Record {record_index}: 'duration_seconds' must be a number")
        if duration_seconds < 0:
            raise ValueError(f"Record {record_index}: 'duration_seconds' must be non-negative")

        return WorkflowRunAttempt(
            id=attempt_id,
            run_id=run_id,
            attempt_number=attempt_number,
            status=status,
            conclusion=conclusion,
            created_at=created_at,
            duration_seconds=float(duration_seconds),
        )
