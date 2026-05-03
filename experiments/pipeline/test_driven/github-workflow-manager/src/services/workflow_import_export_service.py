import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Optional, TYPE_CHECKING

from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt, CEST
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion

if TYPE_CHECKING:
    from .workflow_run_service import WorkflowRunService
    from .attempt_service import AttemptService


class SchemaValidationError(Exception):
    """Raised when import data fails validation against schema."""
    pass


class WorkflowImportExportService:
    """Service for importing and exporting workflow runs and attempts with validation."""

    def __init__(
        self,
        workflow_run_service: "WorkflowRunService",
        attempt_service: "AttemptService",
    ) -> None:
        """
        Initialize the service with references to storage services.

        Args:
            workflow_run_service: Service managing WorkflowRun instances.
            attempt_service: Service managing WorkflowRunAttempt instances.
        """
        self._workflow_run_service = workflow_run_service
        self._attempt_service = attempt_service

    def export(self) -> str:
        """
        Export all workflow runs and attempts as JSON string.

        Returns:
            JSON string with structure {"runs": [...], "attempts": [...]}
            Both runs and attempts are serialized to dicts using their to_dict() methods.
        """
        runs = self._workflow_run_service.list_runs()
        attempts = self._attempt_service.get_all_attempts()

        runs_dicts = [run.to_dict() for run in runs]
        attempts_dicts = [attempt.to_dict() for attempt in attempts]

        data = {
            "runs": runs_dicts,
            "attempts": attempts_dicts,
        }

        return json.dumps(data)

    def import_from(self, filepath: str) -> None:
        """
        Import workflow runs and attempts from a JSON file.

        Performs comprehensive validation including:
        - Top-level keys ("runs", "attempts") existence and type
        - Required fields per model
        - Enum value validity
        - Timestamp format (ISO 8601, timezone-aware)
        - CEST timezone for attempts
        - Deduplication (skip existing by id or run_id+attempt_number)

        Args:
            filepath: Path to JSON file to import.

        Raises:
            SchemaValidationError: If validation fails at any step.
            FileNotFoundError: If filepath does not exist.
        """
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            raw_data = json.loads(file_path.read_text())
        except json.JSONDecodeError as e:
            raise SchemaValidationError(f"Invalid JSON format: {e}")

        # Validate top-level structure
        if not isinstance(raw_data, dict):
            raise SchemaValidationError("Root must be a JSON object")

        if "runs" not in raw_data:
            raise SchemaValidationError("Missing required key 'runs'")
        if "attempts" not in raw_data:
            raise SchemaValidationError("Missing required key 'attempts'")

        if not isinstance(raw_data["runs"], list):
            raise SchemaValidationError("'runs' must be a list")
        if not isinstance(raw_data["attempts"], list):
            raise SchemaValidationError("'attempts' must be a list")

        # Validate and import runs
        existing_run_ids = {run.id for run in self._workflow_run_service.list_runs()}
        for run_data in raw_data["runs"]:
            self._validate_and_import_run(run_data, existing_run_ids)

        # Validate and import attempts
        existing_attempts = {
            (a.run_id, a.attempt_number)
            for a in self._attempt_service.get_all_attempts()
        }
        for attempt_data in raw_data["attempts"]:
            self._validate_and_import_attempt(attempt_data, existing_attempts)

    def _validate_and_import_run(self, run_data: dict, existing_ids: set) -> None:
        """
        Validate a run dict and import it if valid and not duplicate.

        Args:
            run_data: Dictionary representation of a workflow run.
            existing_ids: Set of run IDs already in the service.

        Raises:
            SchemaValidationError: If validation fails.
        """
        if not isinstance(run_data, dict):
            raise SchemaValidationError("Each run must be a JSON object")

        # Check required fields
        required_fields = {
            "id",
            "workflow_name",
            "branch",
            "status",
            "conclusion",
            "created_at",
            "updated_at",
            "run_number",
            "commit_sha",
            "duration_seconds",
        }
        missing = required_fields - set(run_data.keys())
        if missing:
            raise SchemaValidationError(
                f"Run missing required fields: {', '.join(sorted(missing))}"
            )

        # Validate enum values
        try:
            WorkflowStatus(run_data["status"])
        except ValueError:
            raise SchemaValidationError(f"Invalid status: {run_data['status']}")

        if run_data["conclusion"] is not None:
            try:
                WorkflowConclusion(run_data["conclusion"])
            except ValueError:
                raise SchemaValidationError(f"Invalid conclusion: {run_data['conclusion']}")

        # Validate timestamps are ISO 8601 format and timezone-aware
        try:
            created_at = datetime.fromisoformat(run_data["created_at"])
            if created_at.tzinfo is None:
                raise SchemaValidationError(
                    f"created_at must be timezone-aware (got naive datetime)"
                )
        except (ValueError, TypeError) as e:
            raise SchemaValidationError(f"Invalid created_at format: {run_data['created_at']}")

        if run_data["updated_at"] is not None:
            try:
                updated_at = datetime.fromisoformat(run_data["updated_at"])
                if updated_at.tzinfo is None:
                    raise SchemaValidationError(
                        f"updated_at must be timezone-aware (got naive datetime)"
                    )
            except (ValueError, TypeError):
                raise SchemaValidationError(
                    f"Invalid updated_at format: {run_data['updated_at']}"
                )

        # Check for duplicates
        if run_data["id"] in existing_ids:
            return  # Skip duplicate

        # If all validation passed, create and store the run
        try:
            run = WorkflowRun.from_dict(run_data)
            self._workflow_run_service.add_workflow_run(run)
            existing_ids.add(run_data["id"])
        except (ValueError, KeyError) as e:
            raise SchemaValidationError(f"Failed to create run: {e}")

    def _validate_and_import_attempt(
        self,
        attempt_data: dict,
        existing_attempts: set,
    ) -> None:
        """
        Validate an attempt dict and import it if valid and not duplicate.

        Args:
            attempt_data: Dictionary representation of a workflow attempt.
            existing_attempts: Set of (run_id, attempt_number) tuples already in the service.

        Raises:
            SchemaValidationError: If validation fails.
        """
        if not isinstance(attempt_data, dict):
            raise SchemaValidationError("Each attempt must be a JSON object")

        # Check required fields
        required_fields = {
            "id",
            "run_id",
            "attempt_number",
            "status",
            "conclusion",
            "created_at",
            "duration_seconds",
        }
        missing = required_fields - set(attempt_data.keys())
        if missing:
            raise SchemaValidationError(
                f"Attempt missing required fields: {', '.join(sorted(missing))}"
            )

        # Validate created_at is ISO 8601 format and has CEST timezone
        try:
            created_at = datetime.fromisoformat(attempt_data["created_at"])
            if created_at.tzinfo != CEST:
                raise SchemaValidationError(
                    f"created_at must use CEST timezone (got {created_at.tzinfo})"
                )
        except (ValueError, TypeError) as e:
            raise SchemaValidationError(
                f"Invalid created_at format or timezone: {attempt_data['created_at']}"
            )

        # Check for duplicates by (run_id, attempt_number)
        key = (attempt_data["run_id"], attempt_data["attempt_number"])
        if key in existing_attempts:
            return  # Skip duplicate

        # If all validation passed, create and store the attempt
        try:
            attempt = WorkflowRunAttempt.from_dict(attempt_data)
            self._attempt_service.create(attempt)
            existing_attempts.add(key)
        except (ValueError, KeyError) as e:
            raise SchemaValidationError(f"Failed to create attempt: {e}")
