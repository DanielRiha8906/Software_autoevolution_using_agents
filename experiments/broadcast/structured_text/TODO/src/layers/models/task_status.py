"""Task status enumeration."""

from enum import Enum


class TaskStatus(Enum):
    """Status states for tasks."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
