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
    project_id: Optional[str] = None

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if self.due_date is not None:
            result["due_date"] = self.due_date.isoformat()
        if self.project_id is not None:
            result["project_id"] = self.project_id
        return result

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        due_date_str = data.get("due_date")
        due_date = datetime.fromisoformat(due_date_str) if due_date_str else None

        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=due_date,
            project_id=data.get("project_id"),
        )

    def is_overdue(self) -> bool:
        """Return True if due_date is set and is earlier than the current CEST time."""
        if self.due_date is None:
            return False
        # Get current time in CEST
        now_cest = datetime.now(CEST)
        # Convert due_date to CEST for fair comparison
        due_date_cest = self.due_date.astimezone(CEST) if self.due_date.tzinfo else self.due_date.replace(tzinfo=CEST)
        return due_date_cest < now_cest
