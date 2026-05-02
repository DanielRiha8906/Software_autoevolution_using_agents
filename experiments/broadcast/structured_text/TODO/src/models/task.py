from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from .task_status import TaskStatus

# CEST is UTC+2
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
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str)
            except (ValueError, TypeError):
                # Invalid due_date format, skip it for backward compatibility
                due_date = None

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
        """Transition status to IN_PROGRESS and update updated_at to current CEST time."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(CEST)

    def mark_done(self) -> None:
        """Transition status to DONE and update updated_at to current CEST time."""
        self.status = TaskStatus.DONE
        self.updated_at = datetime.now(CEST)

    def reopen(self) -> None:
        """Transition status to PENDING and update updated_at to current CEST time."""
        self.status = TaskStatus.PENDING
        self.updated_at = datetime.now(CEST)

    def is_completed(self) -> bool:
        """Return True when status is DONE."""
        return self.status == TaskStatus.DONE

    def is_pending(self) -> bool:
        """Return True when status is PENDING."""
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """Return True when status is IN_PROGRESS."""
        return self.status == TaskStatus.IN_PROGRESS

    def is_overdue(self) -> bool:
        """Return True if due_date is set and earlier than current CEST time."""
        if self.due_date is None:
            return False
        now_cest = datetime.now(CEST)
        # Convert due_date to CEST for comparison if needed
        due_date_cest = self.due_date.astimezone(CEST) if self.due_date.tzinfo else self.due_date.replace(tzinfo=CEST)
        return due_date_cest < now_cest
