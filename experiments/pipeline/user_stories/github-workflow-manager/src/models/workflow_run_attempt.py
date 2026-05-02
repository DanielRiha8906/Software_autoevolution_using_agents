from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WorkflowRunAttempt:
    """Represents a single execution attempt within a workflow run.

    GitHub Actions allows a workflow run to be executed multiple times (retried).
    Each execution is tracked as a separate attempt, identified by its ordinal
    position within the run (1, 2, 3, ...).

    Attributes:
        id: Unique identifier for this attempt.
        run_id: Foreign key reference to the parent WorkflowRun.
        attempt_number: Ordinal position (1, 2, 3, ...) within the run.
            Must be >= 1. Enforced in __post_init__().
        status: Current execution status (e.g., "in_progress", "completed").
        conclusion: Final outcome if available (e.g., "success", "failure").
            Can be None if the attempt has not concluded.
        created_at: ISO 8601 datetime with timezone (UTC) when attempt started.
        duration_seconds: Execution time in seconds. Defaults to 0.0.
            Must be >= 0. Enforced in __post_init__().

    Constraint:
        The pair (run_id, attempt_number) must be unique across all attempts
        for a given run. This uniqueness must be enforced at the service/storage
        layer when persisting attempts.
    """

    id: int
    run_id: int
    attempt_number: int
    status: str
    conclusion: Optional[str]
    created_at: datetime
    duration_seconds: float = 0.0

    def __post_init__(self) -> None:
        """Validate attempt after initialization.

        Raises:
            ValueError: If attempt_number < 1 or duration_seconds < 0.
        """
        if self.attempt_number < 1:
            raise ValueError("attempt_number must be a positive integer (>= 1)")
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must be non-negative")

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary.

        Returns:
            dict: All fields serialized, with datetimes as ISO 8601 strings.
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
        """Deserialize from a dictionary.

        Args:
            data: Dictionary with fields matching the dataclass signature.
                Missing duration_seconds defaults to 0.0.

        Returns:
            WorkflowRunAttempt: Reconstructed instance.
        """
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            attempt_number=data["attempt_number"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            created_at=datetime.fromisoformat(data["created_at"]),
            duration_seconds=data.get("duration_seconds", 0.0),
        )
