from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

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

    def mark_in_progress(self) -> None:
        """Transition status to IN_PROGRESS (no-op if already IN_PROGRESS or DONE)."""
        if self.status not in (TaskStatus.IN_PROGRESS, TaskStatus.DONE):
            self.status = TaskStatus.IN_PROGRESS
            self.updated_at = datetime.now(ZoneInfo("Europe/Paris")).astimezone(timezone.utc)

    def mark_done(self) -> None:
        """Transition status to DONE (no-op if already DONE)."""
        if self.status != TaskStatus.DONE:
            self.status = TaskStatus.DONE
            self.updated_at = datetime.now(ZoneInfo("Europe/Paris")).astimezone(timezone.utc)

    def reopen(self) -> None:
        """Transition status to PENDING (no-op if already PENDING)."""
        if self.status != TaskStatus.PENDING:
            self.status = TaskStatus.PENDING
            self.updated_at = datetime.now(ZoneInfo("Europe/Paris")).astimezone(timezone.utc)

    def is_completed(self) -> bool:
        """Return True if status is DONE."""
        return self.status == TaskStatus.DONE

    def is_overdue(self) -> bool:
        """Check if task is overdue (due_date is in the past in CEST timezone)."""
        if self.due_date is None:
            return False
        # Get current time in CEST
        cest = ZoneInfo("Europe/Paris")
        now_cest = datetime.now(cest)
        # Convert due_date to CEST for comparison
        due_date_cest = self.due_date.astimezone(cest) if self.due_date.tzinfo else self.due_date.replace(tzinfo=timezone.utc).astimezone(cest)
        return due_date_cest < now_cest
