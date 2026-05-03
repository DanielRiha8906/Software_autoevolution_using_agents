from datetime import datetime
from typing import Optional

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from .comments_service import CommentsService
from .task_manager import TaskManager


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        storage = storage or JsonStorage()
        self._manager = TaskManager(storage)
        self._comments_service = CommentsService(storage, self._manager)
        # Now set the comments_service on the manager for cascade deletes
        self._manager._comments_service = self._comments_service

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
        self._manager.delete(task_id)

    def set_due_date(self, task_id: str, due_date: Optional[datetime] = None) -> Task:
        return self._manager.set_due_date(task_id, due_date)

    def add_comment(self, task_id: str, content: str) -> TaskComment:
        return self._comments_service.add_comment(task_id, content)

    def list_comments(self, task_id: str) -> list[TaskComment]:
        return self._comments_service.list_comments(task_id)

    def delete_comment(self, comment_id: str) -> None:
        self._comments_service.delete_comment(comment_id)
