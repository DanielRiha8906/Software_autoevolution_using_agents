from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from .task_status import TaskStatus

# CEST timezone (UTC+2, fixed, no DST)
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
        if self.due_date is not None:
            if not isinstance(self.due_date, datetime):
                raise ValueError("due_date must be a datetime instance or None")
            if self.due_date.tzinfo is None:
                raise ValueError("due_date must be timezone-aware")

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
        )

    def mark_in_progress(self) -> None:
        """Transition task from PENDING to IN_PROGRESS."""
        if self.status == TaskStatus.PENDING:
            self.status = TaskStatus.IN_PROGRESS
            self.updated_at = datetime.now(CEST)

    def mark_done(self) -> None:
        """Transition task from IN_PROGRESS to DONE."""
        if self.status == TaskStatus.IN_PROGRESS:
            self.status = TaskStatus.DONE
            self.updated_at = datetime.now(CEST)

    def reopen(self) -> None:
        """Transition task from DONE back to PENDING."""
        if self.status == TaskStatus.DONE:
            self.status = TaskStatus.PENDING
            self.updated_at = datetime.now(CEST)

    def is_completed(self) -> bool:
        """Check if task is in DONE status."""
        return self.status == TaskStatus.DONE

    def is_pending(self) -> bool:
        """Check if task is in PENDING status."""
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """Check if task is in IN_PROGRESS status."""
        return self.status == TaskStatus.IN_PROGRESS

    def is_overdue(self) -> bool:
        """Check if task is overdue (due_date is in the past)."""
        if self.due_date is None:
            return False
        return self.due_date < datetime.now(CEST)
