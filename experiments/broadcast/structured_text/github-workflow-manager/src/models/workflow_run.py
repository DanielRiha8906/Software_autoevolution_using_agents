from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .workflow_status import WorkflowStatus
from .workflow_conclusion import WorkflowConclusion


@dataclass
class WorkflowRun:
    id: str
    workflow_name: str
    branch: str
    status: WorkflowStatus
    conclusion: Optional[WorkflowConclusion]
    created_at: datetime
    updated_at: Optional[datetime]
    run_number: Optional[int]
    commit_sha: Optional[str]
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflow_name": self.workflow_name,
            "branch": self.branch,
            "status": self.status.value,
            "conclusion": self.conclusion.value if self.conclusion else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "run_number": self.run_number,
            "commit_sha": self.commit_sha,
            "duration_seconds": self.duration_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRun":
        duration = data.get("duration_seconds", 0.0)
        if duration < 0:
            raise ValueError(f"duration_seconds must be non-negative, got {duration}")
        return cls(
            id=data["id"],
            workflow_name=data["workflow_name"],
            branch=data["branch"],
            status=WorkflowStatus(data["status"]),
            conclusion=WorkflowConclusion(data["conclusion"]) if data.get("conclusion") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            run_number=data.get("run_number"),
            commit_sha=data.get("commit_sha"),
            duration_seconds=duration,
        )

    def is_running(self) -> bool:
        """
        Check if the workflow run is currently running.

        A run is considered running if its status is one of:
        - in_progress
        - queued
        - waiting
        - requested
        - pending

        Returns:
            bool: True if the workflow is in a running state, False otherwise.
        """
        return self.status in (
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.QUEUED,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
        )

    def is_terminal(self) -> bool:
        """
        Check if the workflow run is in a terminal state.

        A run is considered terminal if its status is completed.
        This is mutually exclusive with is_running().

        Returns:
            bool: True if the workflow is in a terminal state, False otherwise.
        """
        return self.status == WorkflowStatus.COMPLETED

    def is_successful(self) -> bool:
        """
        Check if the workflow run completed successfully.

        A run is considered successful if:
        - Status is completed AND
        - Conclusion is success

        Returns:
            bool: True if the workflow completed successfully, False otherwise.
        """
        return (
            self.status == WorkflowStatus.COMPLETED
            and self.conclusion == WorkflowConclusion.SUCCESS
        )

    def is_failed(self) -> bool:
        """
        Check if the workflow run failed.

        A run is considered failed if:
        - Status is completed AND
        - Conclusion is either failure or timed_out

        Returns:
            bool: True if the workflow failed, False otherwise.
        """
        return (
            self.status == WorkflowStatus.COMPLETED
            and self.conclusion in (WorkflowConclusion.FAILURE, WorkflowConclusion.TIMED_OUT)
        )

    def is_cancelled(self) -> bool:
        """
        Check if the workflow run was cancelled.

        A run is considered cancelled if its conclusion is cancelled.

        Returns:
            bool: True if the workflow was cancelled, False otherwise.
        """
        return self.conclusion == WorkflowConclusion.CANCELLED
