"""Domain contracts - protocols defining responsibilities for task, comment, and project management."""

from typing import Protocol, Optional
from datetime import datetime

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.task_status import TaskStatus
from ..models.project import Project


class TaskDomain(Protocol):
    """Protocol for task domain operations.

    Any implementation handling task operations should conform to this contract.
    """

    def add_task(
        self,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        project_id: Optional[str] = None,
    ) -> Task:
        """Add a new task."""
        ...

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID."""
        ...

    def list_all_tasks(self) -> list[Task]:
        """List all tasks."""
        ...

    def list_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        """List tasks filtered by status."""
        ...

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Task:
        """Update a task."""
        ...

    def set_task_status(self, task_id: str, status: TaskStatus) -> Task:
        """Change task status."""
        ...

    def delete_task(self, task_id: str) -> None:
        """Delete a task."""
        ...


class CommentDomain(Protocol):
    """Protocol for comment domain operations.

    Any implementation handling comment operations should conform to this contract.
    """

    def add_comment(
        self, task_id: str, content: str, author: Optional[str] = None
    ) -> TaskComment:
        """Add a comment to a task."""
        ...

    def list_comments_for_task(self, task_id: str) -> list[TaskComment]:
        """List comments for a specific task."""
        ...

    def get_all_comments(self) -> list[TaskComment]:
        """Get all comments across all tasks."""
        ...


class ProjectDomain(Protocol):
    """Protocol for project domain operations.

    Any implementation handling project operations should conform to this contract.
    """

    def create_project(self, name: str) -> Project:
        """Create a new project."""
        ...

    def list_all_projects(self) -> list[Project]:
        """List all projects."""
        ...
