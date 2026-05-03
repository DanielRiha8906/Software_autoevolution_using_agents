import uuid
from datetime import datetime, timezone
from typing import Optional

from ..models.workflow_run import WorkflowRun
from ..models.workflow_attempt import WorkflowRunAttempt
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from .workflow_run_service import WorkflowRunService
from .workflow_attempt_service import WorkflowAttemptService


class WorkflowRunTracker:
    """High-level facade that creates and tracks WorkflowRun instances."""

    def __init__(self, service: WorkflowRunService, attempt_service: Optional[WorkflowAttemptService] = None):
        self._service = service
        self._attempt_service = attempt_service

    def track(
        self,
        workflow_name: str,
        branch: str,
        status: WorkflowStatus,
        conclusion: Optional[WorkflowConclusion] = None,
        run_number: Optional[int] = None,
        commit_sha: Optional[str] = None,
        run_id: Optional[str] = None,
        duration_seconds: float = 0.0,
    ) -> WorkflowRun:
        run = WorkflowRun(
            id=run_id or str(uuid.uuid4()),
            workflow_name=workflow_name,
            branch=branch,
            status=status,
            conclusion=conclusion,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=run_number,
            commit_sha=commit_sha,
            duration_seconds=duration_seconds,
        )
        return self._service.add_workflow_run(run)

    def create_attempt(
        self,
        run_id: str,
        attempt_number: int,
        status: WorkflowStatus,
        conclusion: Optional[WorkflowConclusion] = None,
        completed_at: Optional[datetime] = None,
        duration_seconds: float = 0.0,
        logs_url: Optional[str] = None,
        attempt_id: Optional[str] = None,
    ) -> WorkflowRunAttempt:
        if self._attempt_service is None:
            raise RuntimeError("Attempt service not initialized.")
        attempt = WorkflowRunAttempt(
            id=attempt_id or str(uuid.uuid4()),
            run_id=run_id,
            attempt_number=attempt_number,
            status=status,
            conclusion=conclusion,
            started_at=datetime.now(timezone.utc),
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            logs_url=logs_url,
        )
        return self._attempt_service.add_attempt(attempt)
