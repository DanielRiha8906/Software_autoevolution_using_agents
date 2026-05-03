from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .task_status import TaskStatus


@dataclass
class FilterOptions:
    """Encapsulates filtering criteria for tasks."""

    status: Optional[TaskStatus] = None
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    overdue_only: bool = False

    def __post_init__(self) -> None:
        """Validate filter options after initialization."""
        if self.due_before is not None and not isinstance(self.due_before, datetime):
            raise ValueError(f"due_before must be a datetime object, got {type(self.due_before)}")
        if self.due_after is not None and not isinstance(self.due_after, datetime):
            raise ValueError(f"due_after must be a datetime object, got {type(self.due_after)}")

        if self.due_before is not None and self.due_before.tzinfo is None:
            raise ValueError("due_before must be timezone-aware")
        if self.due_after is not None and self.due_after.tzinfo is None:
            raise ValueError("due_after must be timezone-aware")
