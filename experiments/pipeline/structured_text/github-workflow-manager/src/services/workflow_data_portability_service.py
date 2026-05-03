"""
Data portability service for exporting and importing workflow runs and attempts.

Provides functionality to export workflow data to JSON files and import from files,
with support for deduplication and schema validation.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..models.workflow_run import WorkflowRun
from ..models.workflow_attempt import WorkflowRunAttempt
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_attempt_service import WorkflowAttemptService


class WorkflowDataPortabilityService:
    """Service for exporting and importing workflow runs and attempts."""

    def __init__(self, run_service: WorkflowRunService, attempt_service: WorkflowAttemptService):
        """
        Initialize the portability service.

        Args:
            run_service: WorkflowRunService instance for run operations
            attempt_service: WorkflowAttemptService instance for attempt operations
        """
        self._run_service = run_service
        self._attempt_service = attempt_service

    def export_runs(self, filepath: str, runs: Optional[List[WorkflowRun]] = None) -> int:
        """
        Export workflow runs to a JSON file.

        Args:
            filepath: Path to save the JSON file
            runs: List of runs to export. If None, exports all runs from service.

        Returns:
            Number of runs exported

        Raises:
            IOError: If file cannot be written
            ValueError: If filepath is invalid
        """
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            runs_to_export = runs if runs is not None else self._run_service.list_runs()

            data = [run.to_dict() for run in runs_to_export]

            with open(path, "w") as f:
                json.dump(data, f, indent=2)

            return len(runs_to_export)
        except Exception as e:
            raise IOError(f"Failed to export runs to {filepath}: {e}")

    def import_runs(
        self, filepath: str, skip_duplicates: bool = False
    ) -> Dict[str, Any]:
        """
        Import workflow runs from a JSON file.

        Args:
            filepath: Path to the JSON file
            skip_duplicates: If True, skip runs with IDs that already exist.
                           If False, raise error on duplicate IDs.

        Returns:
            Dictionary with keys:
                - 'imported': List of imported WorkflowRun objects
                - 'skipped': List of skipped run data (if skip_duplicates=True)
                - 'count': Total number of runs in file
                - 'successful': Number successfully imported
                - 'failed': Number that failed to import

        Raises:
            IOError: If file cannot be read
            ValueError: If file format is invalid or schema validation fails
        """
        try:
            path = Path(filepath)
            if not path.exists():
                raise IOError(f"File not found: {filepath}")

            with open(path, "r") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("Expected JSON file to contain an array of runs")

            imported = []
            skipped = []
            failed = 0

            for run_data in data:
                try:
                    # Validate schema
                    self._validate_run_schema(run_data)

                    # Create WorkflowRun object
                    run = WorkflowRun.from_dict(run_data)

                    # Check for duplicates
                    existing = self._run_service.get_run_detail(run.id)
                    if existing:
                        if skip_duplicates:
                            skipped.append(run_data)
                        else:
                            raise ValueError(f"Run with id '{run.id}' already exists")
                        continue

                    # Add to service
                    self._run_service.add_workflow_run(run)
                    imported.append(run)

                except (ValueError, KeyError, TypeError) as e:
                    failed += 1
                    # Continue processing other runs

            return {
                "imported": imported,
                "skipped": skipped,
                "count": len(data),
                "successful": len(imported),
                "failed": failed,
            }

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {filepath}: {e}")
        except Exception as e:
            raise IOError(f"Failed to import runs from {filepath}: {e}")

    def export_attempts(self, filepath: str, attempts: Optional[List[WorkflowRunAttempt]] = None) -> int:
        """
        Export workflow attempts to a JSON file.

        Args:
            filepath: Path to save the JSON file
            attempts: List of attempts to export. If None, exports all attempts from service.

        Returns:
            Number of attempts exported

        Raises:
            IOError: If file cannot be written
            ValueError: If filepath is invalid
        """
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            attempts_to_export = attempts if attempts is not None else self._attempt_service.list_attempts()

            data = [attempt.to_dict() for attempt in attempts_to_export]

            with open(path, "w") as f:
                json.dump(data, f, indent=2)

            return len(attempts_to_export)
        except Exception as e:
            raise IOError(f"Failed to export attempts to {filepath}: {e}")

    def import_attempts(
        self, filepath: str, skip_duplicates: bool = False
    ) -> Dict[str, Any]:
        """
        Import workflow attempts from a JSON file.

        Args:
            filepath: Path to the JSON file
            skip_duplicates: If True, skip attempts with IDs that already exist.
                           If False, raise error on duplicate IDs.

        Returns:
            Dictionary with keys:
                - 'imported': List of imported WorkflowRunAttempt objects
                - 'skipped': List of skipped attempt data (if skip_duplicates=True)
                - 'count': Total number of attempts in file
                - 'successful': Number successfully imported
                - 'failed': Number that failed to import

        Raises:
            IOError: If file cannot be read
            ValueError: If file format is invalid or schema validation fails
        """
        try:
            path = Path(filepath)
            if not path.exists():
                raise IOError(f"File not found: {filepath}")

            with open(path, "r") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("Expected JSON file to contain an array of attempts")

            imported = []
            skipped = []
            failed = 0

            for attempt_data in data:
                try:
                    # Validate schema
                    self._validate_attempt_schema(attempt_data)

                    # Create WorkflowRunAttempt object
                    attempt = WorkflowRunAttempt.from_dict(attempt_data)

                    # Check for duplicates
                    existing = self._attempt_service.get_attempt_detail(attempt.id)
                    if existing:
                        if skip_duplicates:
                            skipped.append(attempt_data)
                        else:
                            raise ValueError(f"Attempt with id '{attempt.id}' already exists")
                        continue

                    # Add to service
                    self._attempt_service.add_attempt(attempt)
                    imported.append(attempt)

                except (ValueError, KeyError, TypeError) as e:
                    failed += 1
                    # Continue processing other attempts

            return {
                "imported": imported,
                "skipped": skipped,
                "count": len(data),
                "successful": len(imported),
                "failed": failed,
            }

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {filepath}: {e}")
        except Exception as e:
            raise IOError(f"Failed to import attempts from {filepath}: {e}")

    def _validate_run_schema(self, run_data: Dict[str, Any]) -> None:
        """
        Validate that run_data has required fields for WorkflowRun.

        Args:
            run_data: Dictionary to validate

        Raises:
            ValueError: If required fields are missing or have invalid types
        """
        required_fields = {"id", "workflow_name", "branch", "status", "created_at"}
        missing = required_fields - set(run_data.keys())
        if missing:
            raise ValueError(f"Missing required fields for run: {missing}")

    def _validate_attempt_schema(self, attempt_data: Dict[str, Any]) -> None:
        """
        Validate that attempt_data has required fields for WorkflowRunAttempt.

        Args:
            attempt_data: Dictionary to validate

        Raises:
            ValueError: If required fields are missing or have invalid types
        """
        required_fields = {"id", "run_id", "attempt_number", "status", "started_at"}
        missing = required_fields - set(attempt_data.keys())
        if missing:
            raise ValueError(f"Missing required fields for attempt: {missing}")
