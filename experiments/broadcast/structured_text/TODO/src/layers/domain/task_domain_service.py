"""Domain service for task-related operations.

This service encapsulates task-specific business logic independent of storage.
"""

from datetime import datetime, timezone
from typing import Optional

from ..models.task import Task
from ..models.task_status import TaskStatus
from .task_repository import TaskRepository


class TaskDomainService:
    """Service encapsulating task domain logic."""

    def __init__(self, task_repository: TaskRepository) -> None:
        self._repo = task_repository

    def create_task(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        """Create a new task."""
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._repo.add(title.strip(), description, due_date)

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID."""
        return self._repo.get(task_id)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        """Update a task."""
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._repo.update(task_id, title=title, description=description, due_date=due_date)

    def set_task_status(self, task_id: str, status: TaskStatus) -> Task:
        """Set task status."""
        return self._repo.set_status(task_id, status)

    def delete_task(self, task_id: str) -> None:
        """Delete a task."""
        self._repo.delete(task_id)

    def list_all_tasks(self) -> list[Task]:
        """List all tasks."""
        return self._repo.list_all()

    def list_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        """List tasks by status."""
        return self._repo.list_by_status(status)

    def list_tasks_by_project(self, project_id: str) -> list[Task]:
        """List tasks in a project."""
        return self._repo.list_by_project(project_id)

    def list_overdue_tasks(self) -> list[Task]:
        """List all overdue tasks."""
        return self._repo.list_overdue()
