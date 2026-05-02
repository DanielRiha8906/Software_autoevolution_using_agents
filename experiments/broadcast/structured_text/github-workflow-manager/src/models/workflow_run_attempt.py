from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WorkflowRunAttempt:
    """Represents an attempt within a workflow run.

    Workflow runs can have multiple attempts (e.g., re-runs). Each attempt
    is tracked independently with its own status, conclusion, and timing.
    """

    id: int
    run_id: int
    attempt_number: int
    status: str
    conclusion: Optional[str]
    created_at: datetime
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to dictionary for storage/transmission.

        Returns:
            dict: Dictionary representation with ISO format timestamps.
        """
        return {
            "id": self.id,
            "run_id": self.run_id,
            "attempt_number": self.attempt_number,
            "status": self.status,
            "conclusion": self.conclusion,
            "created_at": self.created_at.isoformat(),
            "duration_seconds": self.duration_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRunAttempt":
        """Deserialize from dictionary.

        Args:
            data: Dictionary containing attempt data with ISO format timestamp.

        Returns:
            WorkflowRunAttempt: Reconstructed instance.

        Raises:
            ValueError: If duration_seconds is negative.
        """
        duration = data.get("duration_seconds", 0.0)
        if duration < 0:
            raise ValueError(f"duration_seconds must be non-negative, got {duration}")
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            attempt_number=data["attempt_number"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            created_at=datetime.fromisoformat(data["created_at"]),
            duration_seconds=duration,
        )
