from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from .task_status import TaskStatus


# CEST: Central European Summer Time (UTC+2)
CEST = timezone(timedelta(hours=2))


def _validate_due_date_timezone(dt: datetime) -> None:
    """Validate that a datetime is timezone-aware and uses CEST."""
    if dt.tzinfo is None:
        raise ValueError("due_date must be timezone-aware (got naive datetime)")
    if dt.tzinfo != CEST:
        raise ValueError(f"due_date must use CEST (UTC+2); got {dt.tzinfo}")


@dataclass
class Task:
    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.due_date is not None:
            if not isinstance(self.due_date, datetime):
                raise TypeError(f"due_date must be a datetime object, got {type(self.due_date).__name__}")
            _validate_due_date_timezone(self.due_date)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        # Extract and validate due_date with backward compatibility
        due_date_str = data.get("due_date")
        due_date = None
        if due_date_str is not None:
            due_date = datetime.fromisoformat(due_date_str)
            _validate_due_date_timezone(due_date)

        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=due_date,
        )

    def mark_in_progress(self) -> None:
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(CEST)

    def mark_done(self) -> None:
        self.status = TaskStatus.DONE
        self.updated_at = datetime.now(CEST)

    def reopen(self) -> None:
        self.status = TaskStatus.PENDING
        self.updated_at = datetime.now(CEST)

    def is_completed(self) -> bool:
        return self.status == TaskStatus.DONE

    def is_pending(self) -> bool:
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        return self.status == TaskStatus.IN_PROGRESS

    def is_overdue(self) -> bool:
        if self.due_date is None:
            return False
        return self.due_date < datetime.now(CEST)
