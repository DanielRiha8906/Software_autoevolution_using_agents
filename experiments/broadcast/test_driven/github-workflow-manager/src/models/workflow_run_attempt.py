from dataclasses import dataclass, field
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
    duration_seconds: Optional[float] = None

    def __post_init__(self) -> None:
        if self.attempt_number < 1:
            raise ValueError("attempt_number must be >= 1")

        # Validate that created_at is in CEST timezone
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")

        # Check if it's CEST (UTC+2) by comparing offsets
        expected_offset = timedelta(hours=2)
        if self.created_at.tzinfo.utcoffset(self.created_at) != expected_offset:
            raise ValueError("created_at must use CEST timezone (UTC+2)")

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
            duration_seconds=data.get("duration_seconds"),
        )
