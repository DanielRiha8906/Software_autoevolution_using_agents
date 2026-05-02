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

    def __post_init__(self) -> None:
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must be non-negative")

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
            duration_seconds=data.get("duration_seconds", 0.0),
        )

    def is_terminal(self) -> bool:
        """Check if the workflow run has reached a terminal state.

        A run is terminal when its status is COMPLETED, regardless of the conclusion.

        Returns:
            bool: True if status is COMPLETED, False otherwise.
        """
        return self.status == WorkflowStatus.COMPLETED

    def is_running(self) -> bool:
        """Check if the workflow run is currently executing or queued.

        A run is running when it is in one of the non-terminal states:
        REQUESTED, PENDING, QUEUED, WAITING, or IN_PROGRESS.

        Returns:
            bool: True if status is in the running states, False otherwise.
        """
        return self.status in (
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
            WorkflowStatus.QUEUED,
            WorkflowStatus.WAITING,
            WorkflowStatus.IN_PROGRESS,
        )

    def is_successful(self) -> bool:
        """Check if the workflow run completed successfully.

        A run is successful when it has reached a terminal state (COMPLETED)
        and the conclusion is SUCCESS.

        Returns:
            bool: True if status is COMPLETED and conclusion is SUCCESS, False otherwise.
        """
        return (
            self.status == WorkflowStatus.COMPLETED
            and self.conclusion == WorkflowConclusion.SUCCESS
        )

    def is_failed(self) -> bool:
        """Check if the workflow run failed.

        A run has failed when it has reached a terminal state (COMPLETED)
        and the conclusion is FAILURE or TIMED_OUT.

        Returns:
            bool: True if status is COMPLETED and conclusion is FAILURE or TIMED_OUT, False otherwise.
        """
        return (
            self.status == WorkflowStatus.COMPLETED
            and self.conclusion in (
                WorkflowConclusion.FAILURE,
                WorkflowConclusion.TIMED_OUT,
            )
        )

    def is_cancelled(self) -> bool:
        """Check if the workflow run was cancelled.

        A run is cancelled when its conclusion is CANCELLED, regardless of status.
        This check is independent of the workflow status.

        Returns:
            bool: True if conclusion is CANCELLED, False otherwise.
        """
        return self.conclusion == WorkflowConclusion.CANCELLED
