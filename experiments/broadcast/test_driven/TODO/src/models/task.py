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

    def __post_init__(self) -> None:
        """Validate due_date if provided."""
        if self.due_date is not None:
            if not isinstance(self.due_date, datetime):
                raise TypeError(f"due_date must be a datetime object, got {type(self.due_date)}")
            if self.due_date.tzinfo is None:
                raise ValueError("due_date must be timezone-aware")
            # Check if timezone is CEST (UTC+2)
            if self.due_date.tzinfo != CEST:
                raise ValueError(f"due_date must use CEST timezone (UTC+2), got {self.due_date.tzinfo}")

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
        due_date = None
        if "due_date" in data and data["due_date"] is not None:
            due_date = datetime.fromisoformat(data["due_date"])
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

    def mark_in_progress(self) -> None:
        """Transition Task to IN_PROGRESS status, update updated_at to current CEST time."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(CEST)

    def mark_done(self) -> None:
        """Transition Task to DONE status, update updated_at to current CEST time."""
        self.status = TaskStatus.DONE
        self.updated_at = datetime.now(CEST)

    def reopen(self) -> None:
        """Transition Task from DONE back to PENDING, update updated_at to current CEST time."""
        self.status = TaskStatus.PENDING
        self.updated_at = datetime.now(CEST)

    def is_completed(self) -> bool:
        """Return True if status is DONE, else False."""
        return self.status == TaskStatus.DONE

    def is_pending(self) -> bool:
        """Return True if status is PENDING, else False."""
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """Return True if status is IN_PROGRESS, else False."""
        return self.status == TaskStatus.IN_PROGRESS

    def is_overdue(self) -> bool:
        """Return True if due_date is in the past (compared to current CEST time), False otherwise or if due_date is None."""
        if self.due_date is None:
            return False
        return self.due_date < datetime.now(CEST)
