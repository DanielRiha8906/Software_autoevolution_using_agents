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
            raise ValueError(f"duration_seconds cannot be negative, got {self.duration_seconds}")

    def is_terminal(self) -> bool:
        """Returns True if the run has terminated and will not change further.

        A run is terminal when its status is COMPLETED.

        Returns:
            bool: True if status is COMPLETED, False otherwise.
        """
        return self.status == WorkflowStatus.COMPLETED

    def is_successful(self) -> bool:
        """Returns True if the run succeeded.

        A run is successful when status is COMPLETED and conclusion is SUCCESS.

        Returns:
            bool: True if status is COMPLETED and conclusion is SUCCESS, False otherwise.
        """
        return self.status == WorkflowStatus.COMPLETED and self.conclusion == WorkflowConclusion.SUCCESS

    def is_failed(self) -> bool:
        """Returns True if the run failed.

        A run is failed when status is COMPLETED and conclusion is FAILURE.

        Returns:
            bool: True if status is COMPLETED and conclusion is FAILURE, False otherwise.
        """
        return self.status == WorkflowStatus.COMPLETED and self.conclusion == WorkflowConclusion.FAILURE

    def is_running(self) -> bool:
        """Returns True if the run is still executing.

        A run is running when status is IN_PROGRESS or REQUESTED.

        Returns:
            bool: True if status is IN_PROGRESS or REQUESTED, False otherwise.
        """
        return self.status in (WorkflowStatus.IN_PROGRESS, WorkflowStatus.REQUESTED)

    def is_cancelled(self) -> bool:
        """Returns True if the run was cancelled.

        A run is cancelled when its conclusion is CANCELLED.

        Returns:
            bool: True if conclusion is CANCELLED, False otherwise.
        """
        return self.conclusion == WorkflowConclusion.CANCELLED

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
