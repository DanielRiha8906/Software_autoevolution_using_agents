from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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

    def __post_init__(self) -> None:
        """Validate timezone awareness of datetime fields."""
        if self.due_date is not None:
            if self.due_date.tzinfo is None:
                raise ValueError("due_date must be timezone-aware")

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

    def mark_in_progress(self) -> Task:
        """Transition task to IN_PROGRESS status.

        Valid from PENDING or IN_PROGRESS (idempotent).
        Raises ValueError if called from DONE status.
        Updates updated_at to current CEST time.

        Returns:
            self for method chaining

        Raises:
            ValueError: if task is already DONE
        """
        if self.status == TaskStatus.DONE:
            raise ValueError("Cannot mark a DONE task as IN_PROGRESS")
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(CEST)
        return self

    def mark_done(self) -> Task:
        """Transition task to DONE status.

        Valid only from IN_PROGRESS status.
        Raises ValueError if called from PENDING or DONE status.
        Updates updated_at to current CEST time.

        Returns:
            self for method chaining

        Raises:
            ValueError: if task is not IN_PROGRESS
        """
        if self.status != TaskStatus.IN_PROGRESS:
            raise ValueError("Can only mark IN_PROGRESS tasks as DONE")
        self.status = TaskStatus.DONE
        self.updated_at = datetime.now(CEST)
        return self

    def reopen(self) -> Task:
        """Transition task back to IN_PROGRESS status.

        Valid only from DONE status.
        Raises ValueError if called from PENDING or IN_PROGRESS status.
        Updates updated_at to current CEST time.

        Returns:
            self for method chaining

        Raises:
            ValueError: if task is not DONE
        """
        if self.status != TaskStatus.DONE:
            raise ValueError("Can only reopen DONE tasks")
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(CEST)
        return self

    def is_completed(self) -> bool:
        """Check if task is in DONE status.

        Returns:
            True if status is DONE, False otherwise
        """
        return self.status == TaskStatus.DONE

    def is_pending(self) -> bool:
        """Check if task is in PENDING status.

        Returns:
            True if status is PENDING, False otherwise
        """
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """Check if task is in IN_PROGRESS status.

        Returns:
            True if status is IN_PROGRESS, False otherwise
        """
        return self.status == TaskStatus.IN_PROGRESS

    def is_overdue(self) -> bool:
        """Check if task is overdue based on due_date.

        Compares due_date (converted to CEST) against current CEST time.
        Returns False if due_date is not set.

        Returns:
            True if due_date is set and is in the past (relative to CEST now),
            False otherwise
        """
        if self.due_date is None:
            return False
        now_cest = datetime.now(CEST)
        due_date_cest = self.due_date.astimezone(CEST)
        return due_date_cest < now_cest
