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

    def is_pending(self) -> bool:
        """Return True if task status is PENDING."""
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """Return True if task status is IN_PROGRESS."""
        return self.status == TaskStatus.IN_PROGRESS

    def is_done(self) -> bool:
        """Return True if task status is DONE."""
        return self.status == TaskStatus.DONE

    def _transition_to(self, new_status: TaskStatus) -> None:
        """Internal helper to transition to a new status and update timestamp."""
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

    def mark_in_progress(self) -> None:
        """Transition task from PENDING to IN_PROGRESS. Updates updated_at. Raises ValueError if not PENDING."""
        if self.status != TaskStatus.PENDING:
            raise ValueError(
                f"Cannot mark {self.status.value} task as in progress. Task must be pending."
            )
        self._transition_to(TaskStatus.IN_PROGRESS)

    def mark_done(self) -> None:
        """Transition task from IN_PROGRESS to DONE. Updates updated_at. Raises ValueError if not IN_PROGRESS."""
        if self.status != TaskStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot mark {self.status.value} task as done. Task must be in progress."
            )
        self._transition_to(TaskStatus.DONE)

    def reopen(self) -> None:
        """Transition task from DONE/IN_PROGRESS back to PENDING. Updates updated_at. Raises ValueError if PENDING."""
        if self.status == TaskStatus.PENDING:
            raise ValueError(
                "Cannot reopen a pending task. Task must be in progress or done."
            )
        self._transition_to(TaskStatus.PENDING)
