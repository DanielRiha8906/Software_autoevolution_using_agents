"""Abstract protocols for repository interfaces."""

from typing import Protocol, Optional
from ..models import Task, TaskComment, Project, TaskStatus


class TaskRepository(Protocol):
    """Protocol for task persistence operations."""

    def add(self, title: str, description: Optional[str] = None, due_date: Optional[object] = None) -> Task:
        """Add a new task."""
        ...

    def get(self, task_id: str) -> Task:
        """Get a task by ID or prefix."""
        ...

    def list_all(self) -> list[Task]:
        """List all tasks."""
        ...

    def list_by_status(self, status: TaskStatus) -> list[Task]:
        """List tasks filtered by status."""
        ...

    def list_by_project(self, project_id: str) -> list[Task]:
        """List tasks filtered by project."""
        ...

    def list_overdue(self) -> list[Task]:
        """List all overdue tasks."""
        ...

    def list_by_due_date_range(
        self, before: Optional[object] = None, after: Optional[object] = None
    ) -> list[Task]:
        """List tasks with due dates in the specified range."""
        ...

    def update(
        self, task_id: str, title: Optional[str] = None, description: Optional[str] = None,
        due_date: Optional[object] = None
    ) -> Task:
        """Update a task."""
        ...

    def set_status(self, task_id: str, status: TaskStatus) -> Task:
        """Set the status of a task."""
        ...

    def delete(self, task_id: str) -> None:
        """Delete a task."""
        ...


class CommentRepository(Protocol):
    """Protocol for comment persistence operations."""

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task."""
        ...

    def get_comment(self, comment_id: str) -> TaskComment:
        """Get a comment by ID or prefix."""
        ...

    def list_comments_by_task(self, task_id: str) -> list[TaskComment]:
        """List comments for a task."""
        ...

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment."""
        ...

    def update_comment(self, comment_id: str, content: str) -> TaskComment:
        """Update a comment."""
        ...

    def delete_comments_by_task(self, task_id: str) -> None:
        """Delete all comments for a task."""
        ...


class ProjectRepository(Protocol):
    """Protocol for project persistence operations."""

    def add(self, name: str) -> Project:
        """Add a new project."""
        ...

    def get(self, project_id: str) -> Project:
        """Get a project by ID or prefix."""
        ...

    def list_all(self) -> list[Project]:
        """List all projects."""
        ...

    def update(self, project_id: str, name: str) -> Project:
        """Update a project."""
        ...

    def delete(self, project_id: str) -> None:
        """Delete a project."""
        ...
