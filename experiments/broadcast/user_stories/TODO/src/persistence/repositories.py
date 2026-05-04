from abc import ABC, abstractmethod
from typing import Optional

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.project import Project


class TaskRepository(ABC):
    """Abstract repository for Task persistence."""

    @abstractmethod
    def add(self, task: Task) -> Task:
        """Add a new task."""
        pass

    @abstractmethod
    def get(self, task_id: str) -> Task:
        """Get a task by ID (supports prefix lookup)."""
        pass

    @abstractmethod
    def list_all(self) -> list[Task]:
        """List all tasks."""
        pass

    @abstractmethod
    def list_by_status(self, status) -> list[Task]:
        """List tasks by status."""
        pass

    @abstractmethod
    def list_by_project(self, project_id: str) -> list[Task]:
        """List tasks by project ID."""
        pass

    @abstractmethod
    def list_unassigned(self) -> list[Task]:
        """List tasks not assigned to any project."""
        pass

    @abstractmethod
    def update(self, task: Task) -> Task:
        """Update an existing task."""
        pass

    @abstractmethod
    def delete(self, task_id: str) -> None:
        """Delete a task by ID."""
        pass


class CommentRepository(ABC):
    """Abstract repository for TaskComment persistence."""

    @abstractmethod
    def add(self, comment: TaskComment) -> TaskComment:
        """Add a new comment."""
        pass

    @abstractmethod
    def get(self, comment_id: str) -> TaskComment:
        """Get a comment by ID (supports prefix lookup)."""
        pass

    @abstractmethod
    def list_for_task(self, task_id: str) -> list[TaskComment]:
        """List comments for a specific task, ordered by created_at."""
        pass

    @abstractmethod
    def list_all(self) -> list[TaskComment]:
        """List all comments."""
        pass

    @abstractmethod
    def update(self, comment: TaskComment) -> TaskComment:
        """Update an existing comment."""
        pass

    @abstractmethod
    def delete(self, comment_id: str) -> None:
        """Delete a comment by ID."""
        pass

    @abstractmethod
    def delete_by_task_id(self, task_id: str) -> None:
        """Delete all comments for a specific task."""
        pass


class ProjectRepository(ABC):
    """Abstract repository for Project persistence."""

    @abstractmethod
    def add(self, project: Project) -> Project:
        """Add a new project."""
        pass

    @abstractmethod
    def get(self, project_id: str) -> Project:
        """Get a project by ID (supports prefix lookup)."""
        pass

    @abstractmethod
    def list_all(self) -> list[Project]:
        """List all projects."""
        pass

    @abstractmethod
    def update(self, project: Project) -> Project:
        """Update an existing project."""
        pass

    @abstractmethod
    def delete(self, project_id: str) -> None:
        """Delete a project by ID."""
        pass


__all__ = ["TaskRepository", "CommentRepository", "ProjectRepository"]
