from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from .task_status import TaskStatus

# CEST timezone (UTC+2)
CEST = timezone(timedelta(hours=2))


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
        """Validate that due_date is either None or a timezone-aware CEST datetime."""
        if self.due_date is not None:
            if self.due_date.tzinfo is None:
                raise ValueError("due_date must be timezone-aware (cannot be naive)")
            if self.due_date.tzinfo != CEST:
                raise ValueError(f"due_date must be in CEST timezone, got {self.due_date.tzinfo}")

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
        # Handle due_date with backward compatibility
        due_date_str = data.get("due_date")
        due_date = None
        if due_date_str is not None:
            due_date = datetime.fromisoformat(due_date_str)

        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=due_date,
        )
