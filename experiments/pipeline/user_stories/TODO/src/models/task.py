from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .task_status import TaskStatus
from .task_comment import TaskComment


@dataclass
class Task:
    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[datetime] = None
    comments: list[TaskComment] = field(default_factory=list)
    project_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate timezone awareness of datetime fields."""
        if self.due_date is not None:
            if self.due_date.tzinfo is None:
                raise ValueError("due_date must be timezone-aware")

    # Query Methods

    def is_pending(self) -> bool:
        """Check if task is in PENDING status.

        Returns:
            bool: True if status is PENDING, False otherwise.
        """
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """Check if task is in IN_PROGRESS status.

        Returns:
            bool: True if status is IN_PROGRESS, False otherwise.
        """
        return self.status == TaskStatus.IN_PROGRESS

    def is_completed(self) -> bool:
        """Check if task is in DONE status.

        Returns:
            bool: True if status is DONE, False otherwise.
        """
        return self.status == TaskStatus.DONE

    def is_overdue(self) -> bool:
        """Check if task is overdue.

        A task is considered overdue if it has a due_date in the past and
        has not been completed (status is not DONE). Tasks without a due_date
        or completed tasks are never considered overdue.

        Returns:
            bool: True if task is overdue, False otherwise.
        """
        if self.due_date is None:
            return False
        if self.status == TaskStatus.DONE:
            return False
        return self.due_date < datetime.now(timezone.utc)

    # Mutation Methods

    def mark_in_progress(self) -> Task:
        """Transition task from PENDING to IN_PROGRESS status.

        Updates the task status to IN_PROGRESS and sets updated_at to current UTC time.

        Returns:
            Task: self for method chaining.

        Raises:
            ValueError: If task is not in PENDING status.
        """
        if self.status != TaskStatus.PENDING:
            raise ValueError(f"Cannot mark in_progress: task is already in {self.status.value}")
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(timezone.utc)
        return self

    def mark_done(self) -> Task:
        """Transition task from IN_PROGRESS to DONE status.

        Updates the task status to DONE and sets updated_at to current UTC time.

        Returns:
            Task: self for method chaining.

        Raises:
            ValueError: If task is not in IN_PROGRESS status.
        """
        if self.status != TaskStatus.IN_PROGRESS:
            raise ValueError(f"Cannot mark done: task is {self.status.value}")
        self.status = TaskStatus.DONE
        self.updated_at = datetime.now(timezone.utc)
        return self

    def reopen(self) -> Task:
        """Transition task from DONE back to IN_PROGRESS status.

        Updates the task status to IN_PROGRESS and sets updated_at to current UTC time.
        This allows a completed task to be resumed.

        Returns:
            Task: self for method chaining.

        Raises:
            ValueError: If task is not in DONE status.
        """
        if self.status != TaskStatus.DONE:
            raise ValueError(f"Cannot reopen: task is {self.status.value}")
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(timezone.utc)
        return self

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "comments": [c.to_dict() for c in self.comments],
            "project_id": self.project_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        due_date_str = data.get("due_date")
        due_date = datetime.fromisoformat(due_date_str) if due_date_str else None
        comments_data = data.get("comments") or []
        comments = [TaskComment.from_dict(c) for c in comments_data]
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=due_date,
            comments=comments,
            project_id=data.get("project_id"),
        )
