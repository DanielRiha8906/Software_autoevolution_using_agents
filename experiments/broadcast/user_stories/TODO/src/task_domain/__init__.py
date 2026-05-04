"""Task domain layer.

This module contains task-specific business logic, separated from storage and interface concerns.
"""

from .task_repository import TaskRepository as TaskRepositoryImpl
from .task_repository import TaskNotFoundError

__all__ = [
    "TaskRepositoryImpl",
    "TaskNotFoundError",
]
