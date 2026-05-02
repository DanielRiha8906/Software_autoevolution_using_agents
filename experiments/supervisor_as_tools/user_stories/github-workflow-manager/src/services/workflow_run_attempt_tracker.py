from datetime import datetime, timezone
from typing import Optional

from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..models.attempt_run_status import RunAttemptStatus
from ..models.attempt_run_conclusion import RunAttemptConclusion
from .workflow_run_attempt_service import WorkflowRunAttemptService


class WorkflowRunAttemptTracker:
    """High-level facade for creating and tracking WorkflowRunAttempt instances."""

    def __init__(self, service: WorkflowRunAttemptService):
        self._service = service

    def track(
        self,
        id: int,
        run_id: int,
        attempt_number: int,
        status: RunAttemptStatus,
        conclusion: Optional[RunAttemptConclusion] = None,
        duration_seconds: Optional[float] = None,
        created_at: Optional[datetime] = None,
    ) -> WorkflowRunAttempt:
        """
        Create and add a new WorkflowRunAttempt.

        Parameters:
            id: Unique identifier for the attempt
            run_id: ID of the parent WorkflowRun
            attempt_number: Sequential attempt number (must be >= 1)
            status: Current status
            conclusion: Terminal status reason (optional)
            duration_seconds: Execution time in seconds (optional)
            created_at: Timestamp (defaults to now UTC if None)

        Returns: The created and persisted WorkflowRunAttempt
        """
        attempt = WorkflowRunAttempt(
            id=id,
            run_id=run_id,
            attempt_number=attempt_number,
            status=status,
            conclusion=conclusion,
            created_at=created_at or datetime.now(timezone.utc),
            duration_seconds=duration_seconds,
        )
        return self._service.add_workflow_run_attempt(attempt)
