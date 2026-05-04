from typing import Optional
from datetime import datetime, timezone, timedelta

from ..models.task import Task, CEST
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)

    def get_storage(self):
        """Get storage backend for dependent services (e.g., ProjectService).

        Returns:
            The JsonStorage instance.
        """
        return self._manager._storage

    def get_all_tasks_as_dicts(self) -> list[dict]:
        """Get all persisted tasks as dictionaries.

        Used by ProjectService for coordinated storage operations.

        Returns:
            List of task dictionaries.
        """
        return [t.to_dict() for t in self._manager.list_all()]

    def _reload_tasks(self) -> None:
        """Reload tasks from storage.

        Used by import/export operations that modify storage externally.
        """
        self._manager._load()

    def add_task(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None, project_id: Optional[str] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.add(title.strip(), description, due_date, project_id)

    def get_task(self, task_id: str) -> Task:
        return self._manager.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        overdue: bool = False,
        project_id: Optional[str] = None,
    ) -> list[Task]:
        # Validate timezone for due_before and due_after
        if due_before is not None:
            if due_before.tzinfo is None or due_before.tzinfo != CEST:
                raise ValueError("due_before must be a timezone-aware CEST datetime")
        if due_after is not None:
            if due_after.tzinfo is None or due_after.tzinfo != CEST:
                raise ValueError("due_after must be a timezone-aware CEST datetime")

        # Start with all tasks or filtered by status
        if status is not None:
            tasks = self._manager.list_by_status(status)
        else:
            tasks = self._manager.list_all()

        # Apply due_before filter
        if due_before is not None:
            tasks = [t for t in tasks if t.due_date is not None and t.due_date < due_before]

        # Apply due_after filter
        if due_after is not None:
            tasks = [t for t in tasks if t.due_date is not None and t.due_date > due_after]

        # Apply overdue filter
        if overdue:
            tasks = [t for t in tasks if t.is_overdue()]

        # Apply project_id filter
        if project_id is not None:
            tasks = [t for t in tasks if t.project_id == project_id]

        return tasks

    def start_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.DONE)

    def reopen_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.PENDING)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, project_id: Optional[str] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.update(task_id, title=title, description=description, project_id=project_id)

    def delete_task(self, task_id: str) -> None:
        self._manager.delete(task_id)
