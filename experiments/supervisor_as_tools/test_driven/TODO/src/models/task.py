from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from .task_status import TaskStatus

CEST = timezone(timedelta(hours=2))


def _validate_timezone_aware_datetime(dt: datetime) -> None:
    """Validate that a datetime is timezone-aware.

    Args:
        dt: The datetime to validate.

    Raises:
        ValueError: If the datetime is naive (has no timezone info).
    """
    if dt.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware")


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
        """Validate fields after initialization."""
        if self.due_date is not None:
            _validate_timezone_aware_datetime(self.due_date)

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
        due_date = None
        if due_date_str is not None:
            due_date = datetime.fromisoformat(due_date_str)
            _validate_timezone_aware_datetime(due_date)
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
        """Mark the task as in progress and update the timestamp to CEST.

        Sets the status to IN_PROGRESS and updates updated_at to the current
        time in CEST (UTC+2).
        """
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(CEST)

    def mark_done(self) -> None:
        """Mark the task as done and update the timestamp to CEST.

        Sets the status to DONE and updates updated_at to the current time in
        CEST (UTC+2).
        """
        self.status = TaskStatus.DONE
        self.updated_at = datetime.now(CEST)

    def reopen(self) -> None:
        """Reopen the task and update the timestamp to CEST.

        Sets the status to PENDING and updates updated_at to the current time
        in CEST (UTC+2).
        """
        self.status = TaskStatus.PENDING
        self.updated_at = datetime.now(CEST)

    def is_completed(self) -> bool:
        """Return True if the task status is DONE.

        Returns:
            True if status is DONE, False otherwise.
        """
        return self.status == TaskStatus.DONE

    def is_overdue(self) -> bool:
        """Return True if the task has a due date in the past.

        Uses the current time in CEST (UTC+2) to determine if the due date
        is in the past.

        Returns:
            True if due_date is set and is in the past, False otherwise.
        """
        if self.due_date is None:
            return False
        return datetime.now(CEST) > self.due_date

    def is_pending(self) -> bool:
        """Return True if the task status is PENDING.

        Returns:
            True if status is PENDING, False otherwise.
        """
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """Return True if the task status is IN_PROGRESS.

        Returns:
            True if status is IN_PROGRESS, False otherwise.
        """
        return self.status == TaskStatus.IN_PROGRESS
