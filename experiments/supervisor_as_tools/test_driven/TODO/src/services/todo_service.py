from typing import Optional, TYPE_CHECKING

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager

if TYPE_CHECKING:
    from .comments_service import CommentsService


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)
        self._comments_service: Optional["CommentsService"] = None

    def add_task(self, title: str, description: Optional[str] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.add(title.strip(), description)

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

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.update(task_id, title=title, description=description)

    def delete_task(self, task_id: str) -> None:
        if self._comments_service:
            self._comments_service.delete_comments_for_task(task_id)
        self._manager.delete(task_id)
