from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .task_status import TaskStatus


def _validate_timezone_aware_datetime(dt: datetime) -> None:
    """Validate that a datetime is timezone-aware.

    Args:
        dt: The datetime to validate.

    Raises:
        ValueError: If the datetime is naive (has no timezone info).
    """
    if dt.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware")


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
        """Validate fields after initialization."""
        if self.due_date is not None:
            _validate_timezone_aware_datetime(self.due_date)

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
        due_date_str = data.get("due_date")
        due_date = None
        if due_date_str is not None:
            due_date = datetime.fromisoformat(due_date_str)
            _validate_timezone_aware_datetime(due_date)
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=due_date,
        )
