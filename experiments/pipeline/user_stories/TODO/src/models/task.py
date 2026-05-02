from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .task_status import TaskStatus


def _get_utc_now() -> datetime:
    """Get current time in UTC."""
    return datetime.now(timezone.utc)


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
        """Transition task to IN_PROGRESS status.

        Valid from PENDING or DONE status.
        Invalid from IN_PROGRESS (no-op).
        """
        if self.status != TaskStatus.IN_PROGRESS:
            self.status = TaskStatus.IN_PROGRESS
            self.updated_at = _get_utc_now()

    def mark_done(self) -> None:
        """Transition task to DONE status.

        Valid from IN_PROGRESS status only.
        Invalid from PENDING or DONE (no-op).
        """
        if self.status == TaskStatus.IN_PROGRESS:
            self.status = TaskStatus.DONE
            self.updated_at = _get_utc_now()

    def reopen(self) -> None:
        """Transition task from DONE back to IN_PROGRESS.

        Valid from DONE status only.
        Invalid from PENDING or IN_PROGRESS (no-op).
        """
        if self.status == TaskStatus.DONE:
            self.status = TaskStatus.IN_PROGRESS
            self.updated_at = _get_utc_now()

    def is_completed(self) -> bool:
        """Return True if task status is DONE."""
        return self.status == TaskStatus.DONE

    def is_overdue(self) -> bool:
        """Return True if due_date is set and past, and task is not completed."""
        if self.due_date is None or self.is_completed():
            return False
        return _get_utc_now() > self.due_date

    def is_pending(self) -> bool:
        """Return True if task status is PENDING."""
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """Return True if task status is IN_PROGRESS."""
        return self.status == TaskStatus.IN_PROGRESS
