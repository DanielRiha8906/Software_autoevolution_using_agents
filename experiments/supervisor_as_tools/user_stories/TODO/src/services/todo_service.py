from datetime import datetime
from typing import Optional

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)

    def add_task(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        if due_date is not None:
            if not isinstance(due_date, datetime):
                raise ValueError("due_date must be a datetime instance or None")
            if due_date.tzinfo is None:
                raise ValueError("due_date must be timezone-aware")
        task = self._manager.add(title.strip(), description)
        if due_date is not None:
            task.due_date = due_date
            self._manager._persist()
        return task

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

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        if due_date is not None:
            if not isinstance(due_date, datetime):
                raise ValueError("due_date must be a datetime instance or None")
            if due_date.tzinfo is None:
                raise ValueError("due_date must be timezone-aware")
        return self._manager.update(task_id, title=title, description=description, due_date=due_date)

    def delete_task(self, task_id: str) -> None:
        self._manager.delete(task_id)

    def add_comment_to_task(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        return self._manager.add_comment(task_id, content.strip(), author)

    def list_task_comments(self, task_id: str) -> list[TaskComment]:
        return self._manager.list_comments(task_id)

    def delete_task_comment(self, task_id: str, comment_id: str) -> None:
        self._manager.delete_comment(task_id, comment_id)
