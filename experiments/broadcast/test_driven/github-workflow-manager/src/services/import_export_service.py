import json
from typing import List, Dict, Any

from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from .workflow_run_service import WorkflowRunService


class WorkflowImportExportService:
    """Service for importing and exporting workflow runs and attempts to/from JSON files."""

    def __init__(self, run_svc: WorkflowRunService) -> None:
        """Initialize the service with a WorkflowRunService.

        Args:
            run_svc: The WorkflowRunService instance to use for operations.
        """
        self._run_svc = run_svc

    def export(self, file_path: str) -> None:
        """Export all workflow runs and attempts to a JSON file.

        Args:
            file_path: Path where the JSON file should be written.
        """
        runs = self._run_svc.list_runs()
        attempt_svc = self._run_svc.attempt_service

        # Serialize runs
        runs_data = [run.to_dict() for run in runs]

        # Serialize attempts
        attempts_data: List[Dict[str, Any]] = []
        if attempt_svc is not None:
            for run in runs:
                attempts = attempt_svc.get_by_run_id(run.id)
                for attempt in attempts:
                    attempts_data.append(attempt.to_dict())

        # Write to file
        data = {
            "runs": runs_data,
            "attempts": attempts_data,
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def import_from(self, file_path: str) -> None:
        """Import workflow runs and attempts from a JSON file.

        Args:
            file_path: Path to the JSON file to import from.

        Raises:
            Exception: If the JSON structure is invalid (missing "runs" or "attempts" keys).
        """
        with open(file_path, "r") as f:
            data = json.load(f)

        # Validate structure
        if "runs" not in data or "attempts" not in data:
            raise Exception("Invalid JSON structure: must contain 'runs' and 'attempts' keys")

        # Import runs
        for run_data in data.get("runs", []):
            run = WorkflowRun.from_dict(run_data)
            # Skip if run already exists
            if self._run_svc.get_run_detail(run.id) is None:
                self._run_svc.add_workflow_run(run)

        # Import attempts
        attempt_svc = self._run_svc.attempt_service
        if attempt_svc is not None:
            for attempt_data in data.get("attempts", []):
                attempt = WorkflowRunAttempt.from_dict(attempt_data)
                # Skip if attempt already exists
                existing_attempts = attempt_svc.get_by_run_id(attempt.run_id)
                if not any(
                    a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number
                    for a in existing_attempts
                ):
                    attempt_svc.create(attempt)
