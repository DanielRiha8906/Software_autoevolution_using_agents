from datetime import datetime
from typing import Optional, Union

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)

    def add_task(self, title: str, description: Optional[str] = None, due_date: Optional[Union[datetime, str]] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.add(title.strip(), description, due_date)

    def get_task(self, task_id: str) -> Task:
        return self._manager.get(task_id)

    def list_tasks(self, status: Optional[TaskStatus] = None) -> list[Task]:
        if status is not None:
            return self._manager.list_by_status(status)
        return self._manager.list_all()

    def start_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.DONE)

    def reopen_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.PENDING)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[Union[datetime, str]] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.update(task_id, title=title, description=description, due_date=due_date)

    def delete_task(self, task_id: str) -> None:
        self._manager.delete(task_id)

    def mark_in_progress(self, task_id: str) -> Task:
        """Mark task as in-progress and persist."""
        task = self._manager.get(task_id)
        task.mark_in_progress()
        self._manager._persist()
        return task

    def mark_done(self, task_id: str) -> Task:
        """Mark task as done and persist."""
        task = self._manager.get(task_id)
        task.mark_done()
        self._manager._persist()
        return task

    def reopen(self, task_id: str) -> Task:
        """Reopen task (transition to PENDING) and persist."""
        task = self._manager.get(task_id)
        task.reopen()
        self._manager._persist()
        return task

    def is_pending(self, task_id: str) -> bool:
        """Check if task is pending."""
        return self._manager.get(task_id).is_pending()

    def is_in_progress(self, task_id: str) -> bool:
        """Check if task is in progress."""
        return self._manager.get(task_id).is_in_progress()

    def is_completed(self, task_id: str) -> bool:
        """Check if task is completed."""
        return self._manager.get(task_id).is_completed()

    def is_overdue(self, task_id: str) -> bool:
        """Check if task is overdue."""
        return self._manager.get(task_id).is_overdue()
