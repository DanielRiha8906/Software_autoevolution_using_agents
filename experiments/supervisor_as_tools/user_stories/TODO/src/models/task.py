from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .task_status import TaskStatus
from ..utils.datetime_utils import to_cest


@dataclass
class Task:
    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[datetime] = None

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
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
        )

    def mark_in_progress(self) -> None:
        """Transition task to IN_PROGRESS status and update timestamp to CEST."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = to_cest(datetime.now(timezone.utc))

    def mark_done(self) -> None:
        """Transition task to DONE status and update timestamp to CEST."""
        self.status = TaskStatus.DONE
        self.updated_at = to_cest(datetime.now(timezone.utc))

    def reopen(self) -> None:
        """Transition task back to PENDING status and update timestamp to CEST."""
        self.status = TaskStatus.PENDING
        self.updated_at = to_cest(datetime.now(timezone.utc))

    def is_completed(self) -> bool:
        """Return True if task status is DONE, False otherwise."""
        return self.status == TaskStatus.DONE

    def is_pending(self) -> bool:
        """Return True if task status is PENDING, False otherwise."""
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """Return True if task status is IN_PROGRESS, False otherwise."""
        return self.status == TaskStatus.IN_PROGRESS

    def is_overdue(self) -> bool:
        """Return True if due_date exists and is in the past (CEST), False otherwise."""
        if self.due_date is None:
            return False
        now_cest = to_cest(datetime.now(timezone.utc))
        return self.due_date < now_cest
