from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WorkflowRunAttempt:
    """Model representing a single attempt of a workflow run.

    A workflow run can have multiple attempts. This model tracks attempt-specific
    information including the attempt number, status, and conclusion.

    Attributes:
        id: Unique identifier for this attempt.
        run_id: ID of the parent WorkflowRun.
        attempt_number: Sequential attempt number, starting from 1 (required to be positive).
        status: Current status of the attempt (e.g., "in_progress", "completed").
        conclusion: Optional conclusion of the attempt (e.g., "success", "failure").
        created_at: Timezone-aware datetime when the attempt was created (stored in UTC).
        duration_seconds: Optional execution time in seconds for this attempt (non-negative).

    Note:
        The (run_id, attempt_number) pair must be unique within a workflow run.
        Timezone handling: created_at should be timezone-aware UTC datetimes.
    """

    id: int
    run_id: int
    attempt_number: int
    status: str
    conclusion: Optional[str]
    created_at: datetime
    duration_seconds: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate attempt_number and duration_seconds.

        Raises:
            ValueError: If attempt_number is not positive (>= 1).
            ValueError: If duration_seconds is negative.
        """
        if self.attempt_number < 1:
            raise ValueError(
                f"attempt_number must be positive (>= 1), got {self.attempt_number}"
            )

        if self.duration_seconds is not None and self.duration_seconds < 0:
            raise ValueError(
                f"duration_seconds must be non-negative, got {self.duration_seconds}"
            )

    def to_dict(self) -> dict:
        """Serialize the WorkflowRunAttempt to a JSON-compatible dictionary.

        Returns:
            A dictionary with string keys and JSON-compatible values.
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
        """Deserialize a WorkflowRunAttempt from a dictionary.

        Args:
            data: A dictionary with the attempt data.

        Returns:
            A new WorkflowRunAttempt instance.

        Raises:
            ValueError: If validation fails during __post_init__.
        """
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            attempt_number=data["attempt_number"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            created_at=datetime.fromisoformat(data["created_at"]),
            duration_seconds=data.get("duration_seconds"),
        )
