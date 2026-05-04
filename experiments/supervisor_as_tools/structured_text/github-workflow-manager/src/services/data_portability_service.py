from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..adapters.protocols import FileHandler
from .workflow_run_service import WorkflowRunService
from .attempt_service import AttemptService


@dataclass
class PortabilityEnvelope:
    """Container for exported workflow data with metadata."""
    metadata: dict
    data: dict


@dataclass
class ExportResult:
    """Result of a data export operation."""
    output_path: str
    timestamp: str
    runs_count: int
    attempts_count: int


@dataclass
class ImportResult:
    """Result of a data import operation."""
    timestamp: str
    runs_imported: int
    runs_skipped: int
    runs_failed: int
    attempts_imported: int
    attempts_skipped: int
    attempts_failed: int
    errors: List[str] = field(default_factory=list)


class DataPortabilityService:
    """Service for exporting and importing workflow data."""

    def __init__(self, file_handler: Optional[FileHandler] = None) -> None:
        """Initialize DataPortabilityService.

        Args:
            file_handler: FileHandler instance for file I/O operations.
                If None, defaults to JsonFileAdapter.
        """
        if file_handler is None:
            from ..adapters.json_file_adapter import JsonFileAdapter
            file_handler = JsonFileAdapter()

        self.file_handler = file_handler

    def export_data(
        self,
        service: WorkflowRunService,
        attempt_service: AttemptService,
        output_path: str,
    ) -> ExportResult:
        """Export all runs and attempts to a JSON file.

        Args:
            service: WorkflowRunService instance.
            attempt_service: AttemptService instance.
            output_path: Path to write the export file.

        Returns:
            ExportResult with counts and output path.

        Raises:
            IOError: If file cannot be written.
        """
        # Collect data
        runs = service.list_runs()
        attempts = attempt_service.list_attempts()

        # Create timestamp in UTC ISO 8601 format
        timestamp = datetime.now(timezone.utc).isoformat()

        # Serialize data
        runs_data = [run.to_dict() for run in runs]
        attempts_data = [attempt.to_dict() for attempt in attempts]

        # Create envelope
        envelope = {
            "metadata": {
                "timestamp": timestamp,
                "schema_version": "1.0",
                "runs_count": len(runs_data),
                "attempts_count": len(attempts_data),
            },
            "data": {
                "runs": runs_data,
                "attempts": attempts_data,
            },
        }

        # Write to file using injected file handler
        output_file = self.file_handler.export_to_file(envelope, output_path)

        return ExportResult(
            output_path=output_file,
            timestamp=timestamp,
            runs_count=len(runs_data),
            attempts_count=len(attempts_data),
        )

    def import_data(
        self,
        service: WorkflowRunService,
        attempt_service: AttemptService,
        input_path: str,
        skip_duplicates: bool = True,
        skip_invalid: bool = True,
    ) -> ImportResult:
        """Import runs and attempts from a JSON file.

        Args:
            service: WorkflowRunService instance.
            attempt_service: AttemptService instance.
            input_path: Path to read the import file from.
            skip_duplicates: If True, skip duplicate entries instead of failing.
            skip_invalid: If True, skip invalid entries instead of failing.

        Returns:
            ImportResult with detailed counts and error list.

        Raises:
            IOError: If file cannot be read.
            ValueError: If schema validation fails (when skip_invalid=False).
        """
        # Load and parse JSON using injected file handler
        data = self.file_handler.import_from_file(input_path)

        # Validate schema
        if "metadata" not in data or "data" not in data:
            raise ValueError("Invalid export format: missing 'metadata' or 'data'")

        metadata = data.get("metadata", {})
        schema_version = metadata.get("schema_version")
        if schema_version != "1.0":
            raise ValueError(f"Unsupported schema version: {schema_version} (expected 1.0)")

        # Extract timestamp from metadata
        import_timestamp = metadata.get("timestamp", datetime.now(timezone.utc).isoformat())

        # Initialize counters and error list
        runs_imported = 0
        runs_skipped = 0
        runs_failed = 0
        attempts_imported = 0
        attempts_skipped = 0
        attempts_failed = 0
        errors: List[str] = []

        # Import runs
        runs_data = data.get("data", {}).get("runs", [])
        for idx, run_dict in enumerate(runs_data):
            try:
                run = WorkflowRun.from_dict(run_dict)
                try:
                    service.add_workflow_run(run)
                    runs_imported += 1
                except ValueError as e:
                    if skip_duplicates:
                        runs_skipped += 1
                    else:
                        runs_failed += 1
                        error_msg = f"Run {idx}: Duplicate entry - {e}"
                        errors.append(error_msg)
                        if not skip_invalid:
                            raise ValueError(error_msg)
            except (ValueError, KeyError) as e:
                if skip_invalid:
                    runs_failed += 1
                    error_msg = f"Run {idx}: Invalid data - {e}"
                    errors.append(error_msg)
                else:
                    raise ValueError(f"Run {idx}: Invalid data - {e}")

        # Import attempts
        attempts_data = data.get("data", {}).get("attempts", [])
        for idx, attempt_dict in enumerate(attempts_data):
            try:
                attempt = WorkflowRunAttempt.from_dict(attempt_dict)
                try:
                    # Use create_attempt to handle ID generation and duplicate checking
                    attempt_service.create_attempt(
                        run_id=attempt.run_id,
                        attempt_number=attempt.attempt_number,
                        status=attempt.status,
                        conclusion=attempt.conclusion,
                        created_at=attempt.created_at,
                        duration_seconds=attempt.duration_seconds,
                    )
                    attempts_imported += 1
                except ValueError as e:
                    if skip_duplicates:
                        attempts_skipped += 1
                    else:
                        attempts_failed += 1
                        error_msg = f"Attempt {idx}: Duplicate entry - {e}"
                        errors.append(error_msg)
                        if not skip_invalid:
                            raise ValueError(error_msg)
            except (ValueError, KeyError) as e:
                if skip_invalid:
                    attempts_failed += 1
                    error_msg = f"Attempt {idx}: Invalid data - {e}"
                    errors.append(error_msg)
                else:
                    raise ValueError(f"Attempt {idx}: Invalid data - {e}")

        return ImportResult(
            timestamp=import_timestamp,
            runs_imported=runs_imported,
            runs_skipped=runs_skipped,
            runs_failed=runs_failed,
            attempts_imported=attempts_imported,
            attempts_skipped=attempts_skipped,
            attempts_failed=attempts_failed,
            errors=errors,
        )
