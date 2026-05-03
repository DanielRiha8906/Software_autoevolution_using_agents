from typing import Optional, TYPE_CHECKING
from datetime import datetime

from ..models.task import Task, CEST
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager

if TYPE_CHECKING:
    from .comments_service import CommentsService


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)
        self._comments_service: Optional["CommentsService"] = None

    def _validate_datetime_cest(self, dt: datetime, name: str) -> None:
        """Validate that a datetime is timezone-aware and uses CEST timezone."""
        if dt.tzinfo is None:
            raise ValueError(f"{name} must be timezone-aware (cannot be naive)")
        if dt.tzinfo != CEST:
            raise ValueError(f"{name} must be in CEST timezone, got {dt.tzinfo}")

    def add_task(self, title: str, description: Optional[str] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.add(title.strip(), description)

    def get_task(self, task_id: str) -> Task:
        return self._manager.get(task_id)

    def list_tasks(self,
                   status: Optional[TaskStatus] = None,
                   overdue: Optional[bool] = None,
                   due_before: Optional[datetime] = None,
                   due_after: Optional[datetime] = None) -> list[Task]:
        # Validate datetime parameters
        if due_before is not None:
            self._validate_datetime_cest(due_before, "due_before")
        if due_after is not None:
            self._validate_datetime_cest(due_after, "due_after")

        # Get base list
        if status is not None:
            tasks = self._manager.list_by_status(status)
        else:
            tasks = self._manager.list_all()

        # Apply date filters with AND semantics
        if overdue is not None:
            tasks = [t for t in tasks if t.is_overdue() == overdue]

        if due_before is not None:
            tasks = [t for t in tasks if t.due_date is not None and t.due_date < due_before]

        if due_after is not None:
            tasks = [t for t in tasks if t.due_date is not None and t.due_date > due_after]

        return tasks

    def start_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.DONE)

    def reopen_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.PENDING)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.update(task_id, title=title, description=description)

    def delete_task(self, task_id: str) -> None:
        if self._comments_service:
            self._comments_service.delete_comments_for_task(task_id)
        self._manager.delete(task_id)
