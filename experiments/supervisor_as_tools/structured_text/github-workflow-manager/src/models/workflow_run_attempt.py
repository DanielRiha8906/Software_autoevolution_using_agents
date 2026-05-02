from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WorkflowRunAttempt:
    """
    Represents a single attempt of a workflow run.

    A WorkflowRun can have multiple attempts. This class models each individual
    attempt with its own status, conclusion, and timing information.

    Attributes:
        id: Unique identifier for this attempt.
        run_id: The workflow run ID that this attempt belongs to.
        attempt_number: Sequential number of this attempt within the run.
        status: Current status of this attempt (e.g., "in_progress", "completed").
        conclusion: Final conclusion if the attempt completed (e.g., "success", "failure").
        created_at: When this attempt was created.
    """

    id: int
    run_id: str
    attempt_number: int
    status: str
    conclusion: Optional[str]
    created_at: datetime

    def to_dict(self) -> dict:
        """
        Serialize the WorkflowRunAttempt to a dictionary.

        Converts the datetime to ISO format string for serialization.

        Returns:
            Dictionary representation of this attempt.
        """
        return {
            "id": self.id,
            "run_id": self.run_id,
            "attempt_number": self.attempt_number,
            "status": self.status,
            "conclusion": self.conclusion,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRunAttempt":
        """
        Deserialize a WorkflowRunAttempt from a dictionary.

        Converts the ISO format datetime string back to a datetime object.

        Args:
            data: Dictionary with attempt data.

        Returns:
            WorkflowRunAttempt instance.
        """
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            attempt_number=data["attempt_number"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            created_at=datetime.fromisoformat(data["created_at"]),
        )
