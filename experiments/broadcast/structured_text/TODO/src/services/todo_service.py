from datetime import datetime, timezone
from typing import Optional

from ..models.task import Task, CEST
from ..models.task_comment import TaskComment
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage
from .task_manager import TaskManager
from .comments_service import CommentsService


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._manager = TaskManager(self._storage)
        self._comments = CommentsService(self._storage)

    def add_task(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.add(title.strip(), description, due_date)

    def get_task(self, task_id: str) -> Task:
        return self._manager.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        overdue: bool = False,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
    ) -> list[Task]:
        """List tasks with optional filters for status, overdue, and due date range.

        Args:
            status: Filter by task status
            overdue: If True, return only overdue tasks
            due_before: Filter tasks with due_date <= this datetime
            due_after: Filter tasks with due_date >= this datetime

        Returns:
            Filtered list of tasks
        """
        # Normalize timezone-naive datetimes to UTC for consistent comparison
        if due_before is not None and due_before.tzinfo is None:
            due_before = due_before.replace(tzinfo=timezone.utc)
        if due_after is not None and due_after.tzinfo is None:
            due_after = due_after.replace(tzinfo=timezone.utc)

        # Start with base query
        if status is not None:
            tasks = self._manager.list_by_status(status)
        else:
            tasks = self._manager.list_all()

        # Apply overdue filter
        if overdue:
            tasks = [t for t in tasks if t.is_overdue()]

        # Apply due date range filters
        if due_before is not None or due_after is not None:
            filtered = []
            for t in tasks:
                if t.due_date is None:
                    continue
                # Normalize task's due_date to UTC if naive
                task_due_date = t.due_date
                if task_due_date.tzinfo is None:
                    task_due_date = task_due_date.replace(tzinfo=timezone.utc)
                # Now compare
                if due_before is not None and task_due_date > due_before:
                    continue
                if due_after is not None and task_due_date < due_after:
                    continue
                filtered.append(t)
            tasks = filtered

        return tasks

    def start_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.DONE)

    def reopen_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.PENDING)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.update(task_id, title=title, description=description, due_date=due_date)

    def delete_task(self, task_id: str) -> None:
        # Get the full task ID (in case a prefix was provided)
        task = self.get_task(task_id)
        # Cascade delete: remove comments for this task
        self._comments.delete_comments_by_task(task.id)
        # Delete the task
        self._manager.delete(task.id)

    # Comment management methods
    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task.

        Args:
            task_id: The ID of the task
            content: The comment content
            author: Optional author name

        Returns:
            The created TaskComment

        Raises:
            ValueError: If the task doesn't exist or content is empty
        """
        # Validate that task exists and get the full ID (in case a prefix was provided)
        task = self.get_task(task_id)
        return self._comments.add_comment(task.id, content, author)

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """List all comments for a task, ordered by created_at ascending.

        Args:
            task_id: The ID of the task

        Returns:
            List of TaskComment objects ordered by created_at
        """
        # Validate that task exists and get the full ID (in case a prefix was provided)
        task = self.get_task(task_id)
        return self._comments.list_comments_by_task(task.id)

    def get_comment(self, comment_id: str) -> TaskComment:
        """Get a comment by ID.

        Args:
            comment_id: The ID of the comment

        Returns:
            The TaskComment object

        Raises:
            CommentNotFoundError: If the comment is not found
        """
        return self._comments.get_comment(comment_id)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment by ID.

        Args:
            comment_id: The ID of the comment to delete

        Raises:
            CommentNotFoundError: If the comment is not found
        """
        self._comments.delete_comment(comment_id)

    def update_comment(self, comment_id: str, content: str) -> TaskComment:
        """Update a comment's content.

        Args:
            comment_id: The ID of the comment
            content: The new comment content

        Returns:
            The updated TaskComment

        Raises:
            CommentNotFoundError: If the comment is not found
            ValueError: If content is empty
        """
        return self._comments.update_comment(comment_id, content)
