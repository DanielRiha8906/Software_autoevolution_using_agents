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
    due_date: Optional[datetime] = None
    project_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

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
            due_date=due_date,
            project_id=data.get("project_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    def is_overdue(self) -> bool:
        """Check if task is overdue.

        Returns True if due_date is set, task is not DONE, and current UTC time is past due_date.
        """
        if self.due_date is None or self.status == TaskStatus.DONE:
            return False
        return datetime.now(timezone.utc) > self.due_date

    def mark_in_progress(self) -> Task:
        """Mark task as in-progress and update the updated_at timestamp.

        Returns self for method chaining.
        """
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(timezone.utc)
        return self

    def mark_done(self) -> Task:
        """Mark task as done and update the updated_at timestamp.

        Returns self for method chaining.
        """
        self.status = TaskStatus.DONE
        self.updated_at = datetime.now(timezone.utc)
        return self

    def reopen(self) -> Task:
        """Reopen task (set status to pending) and update the updated_at timestamp.

        Returns self for method chaining.
        """
        self.status = TaskStatus.PENDING
        self.updated_at = datetime.now(timezone.utc)
        return self

    def is_completed(self) -> bool:
        """Check if task is completed.

        Returns True if status is DONE, False otherwise.
        """
        return self.status == TaskStatus.DONE
