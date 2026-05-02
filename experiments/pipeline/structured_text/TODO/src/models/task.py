from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
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
        due_date = None
        if data.get("due_date"):
            try:
                due_date = datetime.fromisoformat(data["due_date"])
            except ValueError:
                raise ValueError(f"Invalid due_date format: {data['due_date']}")
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=due_date,
        )

    def is_overdue(self) -> bool:
        """Check if task is overdue (due_date is in the past in CEST timezone)."""
        if self.due_date is None:
            return False
        cest = timezone(timedelta(hours=2))
        now = datetime.now(cest)
        return self.due_date < now

    def mark_in_progress(self) -> None:
        """
        Transition task status to IN_PROGRESS.

        Valid transition: PENDING → IN_PROGRESS
        Updates updated_at to current CEST time.

        Raises:
            ValueError: If current status is not PENDING
        """
        if self.status != TaskStatus.PENDING:
            raise ValueError(
                f"Cannot transition from {self.status.value} to {TaskStatus.IN_PROGRESS.value}"
            )
        self.status = TaskStatus.IN_PROGRESS
        cest = timezone(timedelta(hours=2))
        self.updated_at = datetime.now(cest)

    def mark_done(self) -> None:
        """
        Transition task status to DONE.

        Valid transition: IN_PROGRESS → DONE
        Updates updated_at to current CEST time.

        Raises:
            ValueError: If current status is not IN_PROGRESS
        """
        if self.status != TaskStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot transition from {self.status.value} to {TaskStatus.DONE.value}"
            )
        self.status = TaskStatus.DONE
        cest = timezone(timedelta(hours=2))
        self.updated_at = datetime.now(cest)

    def reopen(self) -> None:
        """
        Transition task status back to PENDING.

        Valid transition: DONE → PENDING
        Updates updated_at to current CEST time.

        Raises:
            ValueError: If current status is not DONE
        """
        if self.status != TaskStatus.DONE:
            raise ValueError(
                f"Cannot transition from {self.status.value} to {TaskStatus.PENDING.value}"
            )
        self.status = TaskStatus.PENDING
        cest = timezone(timedelta(hours=2))
        self.updated_at = datetime.now(cest)

    def is_completed(self) -> bool:
        """
        Check if task is completed.

        Returns:
            True if status is DONE, False otherwise
        """
        return self.status == TaskStatus.DONE
