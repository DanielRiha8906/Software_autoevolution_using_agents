from typing import Optional

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager
from .comments_service import CommentsService


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)
        self._comments_service = CommentsService(self._manager, storage)

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

    def is_task_pending(self, task_id: str) -> bool:
        task = self._manager.get(task_id)
        return task.is_pending()

    def is_task_in_progress(self, task_id: str) -> bool:
        task = self._manager.get(task_id)
        return task.is_in_progress()

    def is_task_completed(self, task_id: str) -> bool:
        task = self._manager.get(task_id)
        return task.is_completed()

    def is_task_overdue(self, task_id: str) -> bool:
        task = self._manager.get(task_id)
        return task.is_overdue()

    # Comment management methods
    def add_comment(
        self, task_id: str, content: str, author: Optional[str] = None
    ) -> TaskComment:
        """Add a comment to a task."""
        return self._comments_service.add_comment(task_id, content, author)

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """List all comments for a task (ordered by created_at)."""
        return self._comments_service.list_comments_for_task(task_id)

    def get_comment(self, comment_id: str) -> TaskComment:
        """Get a specific comment by id."""
        return self._comments_service.get_comment(comment_id)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment by id."""
        self._comments_service.delete_comment(comment_id)

    def edit_comment(self, comment_id: str, content: str) -> TaskComment:
        """Edit a comment's content."""
        return self._comments_service.edit_comment(comment_id, content)
