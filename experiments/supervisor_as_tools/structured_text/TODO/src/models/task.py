from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .task_status import TaskStatus


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
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=datetime.fromisoformat(due_date_str) if due_date_str is not None else None,
        )

    def is_overdue(self) -> bool:
        if self.due_date is None:
            return False
        now_utc = datetime.now(timezone.utc)
        due_date_utc = self.due_date if self.due_date.tzinfo else self.due_date.replace(tzinfo=timezone.utc)
        return due_date_utc < now_utc

    def mark_in_progress(self) -> None:
        """Transition status to IN_PROGRESS.

        Raises ValueError if task is already IN_PROGRESS or DONE.
        Updates updated_at to current UTC time.
        """
        if self.status == TaskStatus.IN_PROGRESS:
            raise ValueError("Cannot mark a task that is already in progress as in progress")
        if self.status == TaskStatus.DONE:
            raise ValueError("Cannot mark a completed task as in progress")
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(timezone.utc)

    def mark_done(self) -> None:
        """Transition status to DONE.

        Raises ValueError if task is already DONE.
        Updates updated_at to current UTC time.
        """
        if self.status == TaskStatus.DONE:
            raise ValueError("Cannot mark a task that is already done as done")
        self.status = TaskStatus.DONE
        self.updated_at = datetime.now(timezone.utc)

    def reopen(self) -> None:
        """Transition status to PENDING.

        Raises ValueError if task is not DONE (i.e., if it's PENDING or IN_PROGRESS).
        Updates updated_at to current UTC time.
        """
        if self.status != TaskStatus.DONE:
            raise ValueError("Only completed tasks can be reopened")
        self.status = TaskStatus.PENDING
        self.updated_at = datetime.now(timezone.utc)

    def is_completed(self) -> bool:
        """Return True if status is DONE, False otherwise."""
        return self.status == TaskStatus.DONE

    def is_pending(self) -> bool:
        """Return True if status is PENDING, False otherwise."""
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """Return True if status is IN_PROGRESS, False otherwise."""
        return self.status == TaskStatus.IN_PROGRESS
