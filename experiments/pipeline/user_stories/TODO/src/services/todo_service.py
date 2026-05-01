from datetime import datetime
from typing import Optional

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)

    def _validate_due_date(self, due_date_str: Optional[str]) -> Optional[datetime]:
        """Validate and parse ISO 8601 due date string. Returns datetime or None."""
        if due_date_str is None:
            return None
        if not isinstance(due_date_str, str):
            raise ValueError("Due date must be a string")
        try:
            return datetime.fromisoformat(due_date_str)
        except ValueError as e:
            raise ValueError(f"Invalid due date format. Expected ISO 8601 string: {e}")

    def add_task(self, title: str, description: Optional[str] = None, due_date: Optional[str] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        validated_due_date = self._validate_due_date(due_date)
        return self._manager.add(title.strip(), description, validated_due_date)

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

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[str] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        validated_due_date = self._validate_due_date(due_date)
        return self._manager.update(task_id, title=title, description=description, due_date=validated_due_date)

    def delete_task(self, task_id: str) -> None:
        self._manager.delete(task_id)
