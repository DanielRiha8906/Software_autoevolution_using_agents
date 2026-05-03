import json
from pathlib import Path
from src.services.workflow_run_service import WorkflowRunService
from src.models.workflow_run import WorkflowRun
from src.models.workflow_run_attempt import WorkflowRunAttempt


class WorkflowImportExportService:
    def __init__(self, workflow_run_service: WorkflowRunService):
        self._workflow_run_service = workflow_run_service

    def export(self, filepath: str) -> None:
        """Export all workflow runs and attempts to JSON file."""
        # Collect all runs
        runs = self._workflow_run_service.list_runs()

        # Collect all attempts
        all_attempts = []
        for run in runs:
            all_attempts.extend(self._workflow_run_service.attempt_service.get_by_run_id(run.id))

        # Serialize and write
        data = {
            "runs": [r.to_dict() for r in runs],
            "attempts": [a.to_dict() for a in all_attempts]
        }
        Path(filepath).write_text(json.dumps(data))

    def import_from(self, filepath: str) -> None:
        """Import workflow runs and attempts from JSON file."""
        # Read JSON from filepath
        data = json.loads(Path(filepath).read_text())

        # Validate top-level keys
        if "runs" not in data:
            raise Exception("Missing required key: 'runs'")
        if "attempts" not in data:
            raise Exception("Missing required key: 'attempts'")

        # Deserialize runs
        runs = [WorkflowRun.from_dict(r) for r in data["runs"]]

        # Deserialize attempts
        attempts = [WorkflowRunAttempt.from_dict(a) for a in data["attempts"]]

        # Deduplication for runs: skip if run already exists
        for run in runs:
            if self._workflow_run_service.get_run_detail(run.id) is None:
                self._workflow_run_service.add_workflow_run(run)

        # Deduplication for attempts: skip if attempt already exists
        for attempt in attempts:
            try:
                self._workflow_run_service.attempt_service.create(attempt)
            except Exception:
                # Attempt already exists, skip
                pass
