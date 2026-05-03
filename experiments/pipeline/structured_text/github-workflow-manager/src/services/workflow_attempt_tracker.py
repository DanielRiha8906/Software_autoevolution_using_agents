import uuid
from datetime import datetime, timezone
from typing import Optional

from ..models.workflow_attempt import WorkflowRunAttempt
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from .workflow_attempt_service import WorkflowAttemptService


class WorkflowAttemptTracker:
    """High-level facade that creates and tracks WorkflowRunAttempt instances."""

    def __init__(self, service: WorkflowAttemptService):
        self._service = service

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
        return self._service.add_attempt(attempt)
