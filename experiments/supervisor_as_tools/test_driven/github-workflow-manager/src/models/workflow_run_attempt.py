from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional


CEST = timezone(timedelta(hours=2))


@dataclass
class WorkflowRunAttempt:
    id: int
    run_id: int
    attempt_number: int
    status: str
    conclusion: str
    created_at: datetime
    duration_seconds: float = 0.0

    def __post_init__(self):
        if self.attempt_number < 1:
            raise ValueError("attempt_number must be >= 1")

        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware, not naive")

        if self.created_at.tzinfo != CEST:
            raise ValueError("created_at must be in CEST timezone (UTC+2)")

        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must be non-negative")

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
