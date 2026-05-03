from typing import Optional

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from .comment_manager import CommentManager
from .task_manager import TaskManager


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)
        self._comment_manager = CommentManager(storage)

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
        task = self._manager.get(task_id)  # resolves prefix; raises if missing
        self._comment_manager.delete_all_by_task(task.id)  # cascade delete comments
        self._manager.delete(task.id)

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task.

        Args:
            task_id: ID of the task (full or prefix)
            content: Comment text (required, non-empty)
            author: Optional author name

        Returns:
            The created TaskComment instance

        Raises:
            ValueError: If content is empty or whitespace-only
            TaskNotFoundError: If task does not exist
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        # Verify task exists
        task = self._manager.get(task_id)
        return self._comment_manager.add(task.id, content.strip(), author)

    def get_comments(self, task_id: str) -> list[TaskComment]:
        """Get all comments for a task in chronological order.

        Args:
            task_id: ID of the task (full or prefix)

        Returns:
            List of TaskComment instances sorted by created_at (oldest first)

        Raises:
            TaskNotFoundError: If task does not exist
        """
        # Verify task exists
        task = self._manager.get(task_id)
        return self._comment_manager.list_by_task(task.id)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment.

        Args:
            comment_id: ID of the comment (full or prefix)

        Raises:
            CommentNotFoundError: If comment not found or prefix is ambiguous
        """
        self._comment_manager.delete(comment_id)
