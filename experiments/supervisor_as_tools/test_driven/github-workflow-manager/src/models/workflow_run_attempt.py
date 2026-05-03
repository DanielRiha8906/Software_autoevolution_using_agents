from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional


# CEST timezone (UTC+2)
CEST = timezone(timedelta(hours=2))


@dataclass
class WorkflowRunAttempt:
    id: int
    run_id: int
    attempt_number: int
    status: str
    conclusion: str
    created_at: datetime
    duration_seconds: Optional[float] = None

    def __post_init__(self):
        # Validate attempt_number is positive
        if self.attempt_number < 1:
            raise Exception(f"attempt_number must be >= 1, got {self.attempt_number}")

        # Validate created_at has CEST timezone
        if self.created_at.tzinfo is None:
            raise Exception("created_at must be timezone-aware")
        if self.created_at.tzinfo != CEST:
            raise Exception(f"created_at must have CEST timezone (UTC+2), got {self.created_at.tzinfo}")

        # Set default for duration_seconds if None
        if self.duration_seconds is None:
            self.duration_seconds = 0.0

    def to_dict(self) -> dict:
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
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            attempt_number=data["attempt_number"],
            status=data["status"],
            conclusion=data["conclusion"],
            created_at=datetime.fromisoformat(data["created_at"]),
            duration_seconds=data.get("duration_seconds", 0.0),
        )
