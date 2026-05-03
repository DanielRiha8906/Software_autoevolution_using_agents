from datetime import datetime
from typing import Optional

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)

    def add_task(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        if due_date is not None and due_date.tzinfo is None:
            raise ValueError("due_date must be timezone-aware")
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
        return self._manager.set_status(task_id, TaskStatus.IN_PROGRESS)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        if due_date is not None and due_date.tzinfo is None:
            raise ValueError("due_date must be timezone-aware")
        return self._manager.update(task_id, title=title, description=description, due_date=due_date)

    def set_due_date(self, task_id: str, due_date: Optional[datetime]) -> Task:
        if due_date is not None and due_date.tzinfo is None:
            raise ValueError("due_date must be timezone-aware")
        return self._manager.set_due_date(task_id, due_date)

    def delete_task(self, task_id: str) -> None:
        self._manager.delete(task_id)

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task.

        Args:
            task_id: The ID of the task to comment on.
            content: The comment content (non-empty string).
            author: Optional author name for the comment.

        Returns:
            TaskComment: The created comment.

        Raises:
            ValueError: If content is empty.
            TaskNotFoundError: If task is not found.
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        return self._manager.add_comment(task_id, content.strip(), author)

    def get_comments(self, task_id: str) -> list[TaskComment]:
        """Get all comments for a task.

        Args:
            task_id: The ID of the task.

        Returns:
            list[TaskComment]: All comments for the task.

        Raises:
            TaskNotFoundError: If task is not found.
        """
        return self._manager.get_comments(task_id)

    def delete_comment(self, task_id: str, comment_id: str) -> None:
        """Delete a comment from a task.

        Args:
            task_id: The ID of the task.
            comment_id: The ID of the comment to delete.

        Raises:
            TaskNotFoundError: If task is not found.
            ValueError: If comment is not found on the task.
        """
        self._manager.delete_comment(task_id, comment_id)

    def edit_comment(self, task_id: str, comment_id: str, content: str) -> TaskComment:
        """Edit a comment on a task.

        Args:
            task_id: The ID of the task.
            comment_id: The ID of the comment to edit.
            content: The new comment content (non-empty string).

        Returns:
            TaskComment: The updated comment.

        Raises:
            ValueError: If content is empty.
            TaskNotFoundError: If task is not found.
            ValueError: If comment is not found on the task.
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        return self._manager.edit_comment(task_id, comment_id, content.strip())
