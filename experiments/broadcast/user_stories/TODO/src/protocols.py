"""
Protocol definitions for repository and storage abstraction.

This module defines typing protocols that establish contracts between layers,
enabling dependency injection and decoupling of services from their storage implementations.
"""

from __future__ import annotations

from typing import Protocol

from .models.task import Task
from .models.task_comment import TaskComment
from .models.project import Project


class TaskRepository(Protocol):
    """Protocol for task persistence operations."""

    def load_tasks(self) -> list[Task]:
        """Load all tasks from storage."""
        ...

    def save_tasks(self, tasks: list[Task]) -> None:
        """Save all tasks to storage."""
        ...


class CommentRepository(Protocol):
    """Protocol for comment persistence operations."""

    def load_comments(self) -> list[TaskComment]:
        """Load all comments from storage."""
        ...

    def save_comments(self, comments: list[TaskComment]) -> None:
        """Save all comments to storage."""
        ...


class ProjectRepository(Protocol):
    """Protocol for project persistence operations."""

    def load_projects(self) -> list[Project]:
        """Load all projects from storage."""
        ...

    def save_projects(self, projects: list[Project]) -> None:
        """Save all projects to storage."""
        ...


class StorageBackend(Protocol):
    """Protocol for unified storage backend."""

    def load_tasks(self) -> list[Task]:
        """Load all tasks from storage."""
        ...

    def save_tasks(self, tasks: list[Task]) -> None:
        """Save all tasks to storage."""
        ...

    def load_comments(self) -> list[TaskComment]:
        """Load all comments from storage."""
        ...

    def save_comments(self, comments: list[TaskComment]) -> None:
        """Save all comments to storage."""
        ...

    def load_projects(self) -> list[Project]:
        """Load all projects from storage."""
        ...

    def save_projects(self, projects: list[Project]) -> None:
        """Save all projects to storage."""
        ...


__all__ = [
    "TaskRepository",
    "CommentRepository",
    "ProjectRepository",
    "StorageBackend",
]
