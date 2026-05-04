"""Abstract base classes for repository and service interfaces.

This module defines the contracts for storage-related services, decoupling
domain logic from persistence concerns.
"""

from abc import ABC, abstractmethod
from typing import Optional, Union

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.project import Project
from ..models.task_status import TaskStatus


class TaskRepository(ABC):
    """Abstract interface for task persistence and querying."""

    @abstractmethod
    def load(self) -> dict[str, Task]:
        """Load all tasks from storage.

        Returns:
            Dictionary mapping task IDs to Task objects
        """
        ...

    @abstractmethod
    def save(self, tasks: dict[str, Task]) -> None:
        """Persist tasks to storage.

        Args:
            tasks: Dictionary mapping task IDs to Task objects
        """
        ...

    @abstractmethod
    def get(self, task_id: str) -> Optional[Task]:
        """Retrieve a single task by ID.

        Args:
            task_id: The task ID

        Returns:
            Task object if found, None otherwise
        """
        ...

    @abstractmethod
    def find_by_prefix(self, prefix: str) -> list[Task]:
        """Find tasks by ID prefix.

        Args:
            prefix: ID prefix to search for

        Returns:
            List of matching tasks
        """
        ...


class CommentRepository(ABC):
    """Abstract interface for comment persistence and querying."""

    @abstractmethod
    def load(self) -> dict[str, TaskComment]:
        """Load all comments from storage.

        Returns:
            Dictionary mapping comment IDs to TaskComment objects
        """
        ...

    @abstractmethod
    def save(self, comments: dict[str, TaskComment]) -> None:
        """Persist comments to storage.

        Args:
            comments: Dictionary mapping comment IDs to TaskComment objects
        """
        ...

    @abstractmethod
    def get(self, comment_id: str) -> Optional[TaskComment]:
        """Retrieve a single comment by ID.

        Args:
            comment_id: The comment ID

        Returns:
            TaskComment object if found, None otherwise
        """
        ...

    @abstractmethod
    def find_by_prefix(self, prefix: str) -> list[TaskComment]:
        """Find comments by ID prefix.

        Args:
            prefix: ID prefix to search for

        Returns:
            List of matching comments
        """
        ...

    @abstractmethod
    def find_by_task(self, task_id: str) -> list[TaskComment]:
        """Find all comments for a specific task.

        Args:
            task_id: The task ID

        Returns:
            List of comments for that task, ordered by creation time
        """
        ...


class ProjectRepository(ABC):
    """Abstract interface for project persistence and querying."""

    @abstractmethod
    def load(self) -> dict[str, Project]:
        """Load all projects from storage.

        Returns:
            Dictionary mapping project IDs to Project objects
        """
        ...

    @abstractmethod
    def save(self, projects: dict[str, Project]) -> None:
        """Persist projects to storage.

        Args:
            projects: Dictionary mapping project IDs to Project objects
        """
        ...

    @abstractmethod
    def get(self, project_id: str) -> Optional[Project]:
        """Retrieve a single project by ID.

        Args:
            project_id: The project ID

        Returns:
            Project object if found, None otherwise
        """
        ...

    @abstractmethod
    def find_by_prefix(self, prefix: str) -> list[Project]:
        """Find projects by ID prefix.

        Args:
            prefix: ID prefix to search for

        Returns:
            List of matching projects
        """
        ...
