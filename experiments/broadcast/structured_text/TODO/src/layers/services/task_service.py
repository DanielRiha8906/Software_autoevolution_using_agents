"""Task domain service for task-related use cases."""

from datetime import datetime, timezone
from typing import Optional

from ..models import Task, TaskStatus
from ..repositories import JsonTaskRepository, TaskNotFoundError
from ..storage import JsonStorage


class TaskService:
    """Domain service for managing tasks."""

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._repository = JsonTaskRepository(storage or JsonStorage())

    def add_task(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        """Add a new task."""
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._repository.add(title.strip(), description, due_date)

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID."""
        return self._repository.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        overdue: bool = False,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        project_id: Optional[str] = None,
    ) -> list[Task]:
        """List tasks with optional filters."""
        # Normalize timezone-naive datetimes to UTC for consistent comparison
        if due_before is not None and due_before.tzinfo is None:
            due_before = due_before.replace(tzinfo=timezone.utc)
        if due_after is not None and due_after.tzinfo is None:
            due_after = due_after.replace(tzinfo=timezone.utc)

        # Start with base query
        if project_id is not None:
            tasks = self._repository.list_by_project(project_id)
        elif status is not None:
            tasks = self._repository.list_by_status(status)
        else:
            tasks = self._repository.list_all()

        # Apply overdue filter
        if overdue:
            tasks = [t for t in tasks if t.is_overdue()]

        # Apply due date range filters
        if due_before is not None or due_after is not None:
            filtered = []
            for t in tasks:
                if t.due_date is None:
                    continue
                # Normalize task's due_date to UTC if naive
                task_due_date = t.due_date
                if task_due_date.tzinfo is None:
                    task_due_date = task_due_date.replace(tzinfo=timezone.utc)
                # Now compare
                if due_before is not None and task_due_date > due_before:
                    continue
                if due_after is not None and task_due_date < due_after:
                    continue
                filtered.append(t)
            tasks = filtered

        return tasks

    def start_task(self, task_id: str) -> Task:
        """Mark a task as in-progress."""
        return self._repository.set_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: str) -> Task:
        """Mark a task as done."""
        return self._repository.set_status(task_id, TaskStatus.DONE)

    def reopen_task(self, task_id: str) -> Task:
        """Mark a task as pending."""
        return self._repository.set_status(task_id, TaskStatus.PENDING)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        """Update a task's properties."""
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._repository.update(task_id, title=title, description=description, due_date=due_date)

    def delete_task(self, task_id: str) -> None:
        """Delete a task."""
        # Get the full task ID (in case a prefix was provided)
        task = self.get_task(task_id)
        self._repository.delete(task.id)
