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
            "due_date": self.due_date.isoformat() if self.due_date is not None else None,
        }

    def set_due_date(self, due_date: Optional[datetime]) -> None:
        """Set due date with validation. Raises ValueError if due_date is invalid."""
        if due_date is not None and not isinstance(due_date, datetime):
            raise ValueError("due_date must be a datetime object or None")
        self.due_date = due_date

    def mark_in_progress(self) -> None:
        """Transition task status to IN_PROGRESS and update updated_at to current CEST time."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(CEST)

    def mark_done(self) -> None:
        """Transition task status to DONE and update updated_at to current CEST time."""
        self.status = TaskStatus.DONE
        self.updated_at = datetime.now(CEST)

    def reopen(self) -> None:
        """Transition task status back to PENDING if currently DONE, else no-op. Updates updated_at to current CEST time."""
        if self.status == TaskStatus.DONE:
            self.status = TaskStatus.PENDING
            self.updated_at = datetime.now(CEST)

    def is_pending(self) -> bool:
        """Check if task is in PENDING status."""
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """Check if task is in IN_PROGRESS status."""
        return self.status == TaskStatus.IN_PROGRESS

    def is_completed(self) -> bool:
        """Check if task is in DONE status."""
        return self.status == TaskStatus.DONE

    def is_overdue(self) -> bool:
        """Check if task is overdue (due_date is in the past and status is not DONE)."""
        if self.due_date is None or self.is_completed():
            return False
        current_time = datetime.now(CEST)
        return self.due_date < current_time

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        due_date_str = data.get("due_date")
        due_date = None
        if due_date_str is not None:
            try:
                due_date = datetime.fromisoformat(due_date_str)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid due_date format: {e}")

        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=due_date,
        )
