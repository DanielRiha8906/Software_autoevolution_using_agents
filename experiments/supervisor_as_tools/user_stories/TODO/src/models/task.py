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
    project_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "project_id": self.project_id,
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
            project_id=data.get("project_id"),
        )

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
        """
        Check if task is overdue (past due_date and not completed).
        Returns False if no due_date or if status is DONE.
        """
        if self.due_date is None or self.status == TaskStatus.DONE:
            return False
        return datetime.now(timezone.utc) > self.due_date

    def mark_in_progress(self) -> 'Task':
        """
        Transition task to IN_PROGRESS status.
        No-op if already IN_PROGRESS.
        Updates updated_at only if status changes.
        Returns self for chaining.
        """
        if self.status != TaskStatus.IN_PROGRESS:
            self.status = TaskStatus.IN_PROGRESS
            self.updated_at = datetime.now(timezone.utc)
        return self

    def mark_done(self) -> 'Task':
        """
        Transition task to DONE status.
        No-op if already DONE.
        Updates updated_at only if status changes.
        Returns self for chaining.
        """
        if self.status != TaskStatus.DONE:
            self.status = TaskStatus.DONE
            self.updated_at = datetime.now(timezone.utc)
        return self

    def reopen(self) -> 'Task':
        """
        Transition task back to PENDING status.
        No-op if already PENDING.
        Updates updated_at only if status changes.
        Returns self for chaining.
        """
        if self.status != TaskStatus.PENDING:
            self.status = TaskStatus.PENDING
            self.updated_at = datetime.now(timezone.utc)
        return self
