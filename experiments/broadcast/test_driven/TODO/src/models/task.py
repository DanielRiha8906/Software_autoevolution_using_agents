from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from .task_status import TaskStatus

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

    def __post_init__(self):
        if self.due_date is not None:
            if not isinstance(self.due_date, datetime):
                raise ValueError("due_date must be a datetime object")
            if self.due_date.tzinfo is None:
                raise ValueError("due_date must have timezone information (not naive)")
            if self.due_date.tzinfo != CEST:
                raise ValueError(f"due_date must be in CEST timezone, got {self.due_date.tzinfo}")

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
        )

    def mark_in_progress(self) -> None:
        """Transition task status to IN_PROGRESS and update updated_at to current CEST time."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(CEST)

    def mark_done(self) -> None:
        """Transition task status to DONE and update updated_at to current CEST time."""
        self.status = TaskStatus.DONE
        self.updated_at = datetime.now(CEST)

    def reopen(self) -> None:
        """Transition task status from DONE back to PENDING and update updated_at to current CEST time."""
        self.status = TaskStatus.PENDING
        self.updated_at = datetime.now(CEST)

    def is_completed(self) -> bool:
        """Return True if the task status is DONE."""
        return self.status == TaskStatus.DONE

    def is_overdue(self) -> bool:
        """Return True if due_date is set and in the past (using CEST for current time)."""
        if self.due_date is None:
            return False
        current_time = datetime.now(CEST)
        return self.due_date < current_time

    def is_pending(self) -> bool:
        """Return True if the task status is PENDING."""
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """Return True if the task status is IN_PROGRESS."""
        return self.status == TaskStatus.IN_PROGRESS
