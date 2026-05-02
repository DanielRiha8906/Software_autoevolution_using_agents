from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from .task_status import TaskStatus

CEST = ZoneInfo("Europe/Paris")


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
        """Validate due_date after initialization."""
        if self.due_date is not None:
            if not isinstance(self.due_date, datetime):
                raise ValueError(f"due_date must be a datetime object, got {type(self.due_date)}")
            if self.due_date.tzinfo is None:
                raise ValueError("due_date must be timezone-aware")

    def mark_in_progress(self) -> None:
        """Mark task as in progress.

        Updates status to IN_PROGRESS and sets updated_at to current CEST time.
        Valid transitions: PENDING -> IN_PROGRESS. No-op if already IN_PROGRESS.
        Invalid transitions (e.g., DONE -> IN_PROGRESS) are ignored.
        """
        if self.status == TaskStatus.PENDING or self.status == TaskStatus.IN_PROGRESS:
            if self.status != TaskStatus.IN_PROGRESS:
                self.status = TaskStatus.IN_PROGRESS
                self.updated_at = datetime.now(CEST)

    def mark_done(self) -> None:
        """Mark task as done.

        Updates status to DONE and sets updated_at to current CEST time.
        Valid from: PENDING or IN_PROGRESS states. No-op if already DONE.
        """
        if self.status != TaskStatus.DONE:
            self.status = TaskStatus.DONE
            self.updated_at = datetime.now(CEST)

    def reopen(self) -> None:
        """Reopen a completed task.

        Updates status back to PENDING and sets updated_at to current CEST time.
        Valid from: DONE state. No-op if not DONE.
        """
        if self.status == TaskStatus.DONE:
            self.status = TaskStatus.PENDING
            self.updated_at = datetime.now(CEST)

    def is_pending(self) -> bool:
        """Check if task is in PENDING state.

        Returns:
            True if status is PENDING, False otherwise.
        """
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """Check if task is in IN_PROGRESS state.

        Returns:
            True if status is IN_PROGRESS, False otherwise.
        """
        return self.status == TaskStatus.IN_PROGRESS

    def is_completed(self) -> bool:
        """Check if task is completed (in DONE state).

        Returns:
            True if status is DONE, False otherwise.
        """
        return self.status == TaskStatus.DONE

    def is_overdue(self) -> bool:
        """Check if task is overdue.

        A task is overdue if it has a due_date in the past and is not completed.
        Returns:
            True if due_date exists, is in the past, and task is not DONE.
            False if task is completed or has no due_date or due_date is in the future.
        """
        if self.due_date is None or self.is_completed():
            return False
        return datetime.now(CEST) > self.due_date

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
            # Store the timezone key if it's a ZoneInfo for proper deserialization
            if isinstance(self.due_date.tzinfo, ZoneInfo):
                result["due_date_tz"] = self.due_date.tzinfo.key
        return result

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        due_date = None
        if "due_date" in data and data["due_date"] is not None:
            dt = datetime.fromisoformat(data["due_date"])
            # If we have the timezone key stored, use it to reconstruct the ZoneInfo
            if "due_date_tz" in data and data["due_date_tz"] is not None:
                tz = ZoneInfo(data["due_date_tz"])
                naive_dt = dt.replace(tzinfo=None)
                due_date = naive_dt.replace(tzinfo=tz)
            else:
                due_date = dt

        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=due_date,
        )
