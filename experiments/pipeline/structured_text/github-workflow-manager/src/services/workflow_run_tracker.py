import uuid
from datetime import datetime, timezone
from typing import Optional

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from .workflow_run_service import WorkflowRunService


class WorkflowRunTracker:
    """High-level facade that creates and tracks WorkflowRun instances."""

    def __init__(self, service: WorkflowRunService):
        self._service = service

    def track(
        self,
        workflow_name: str,
        branch: str,
        status: WorkflowStatus,
        conclusion: Optional[WorkflowConclusion] = None,
        run_number: Optional[int] = None,
        commit_sha: Optional[str] = None,
        run_id: Optional[str] = None,
        duration_seconds: Optional[float] = None,
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
            duration_seconds=duration_seconds or 0.0,
        )
        return self._service.add_workflow_run(run)
