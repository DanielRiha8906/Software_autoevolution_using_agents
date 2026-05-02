from typing import Optional

from ..models.task_comment import TaskComment
from .todo_service import TodoService


class CommentsService:
    """Manages TaskComment lifecycle for tasks."""

    def __init__(self, todo_service: TodoService) -> None:
        """Initialize CommentsService with a TodoService instance.

        Args:
            todo_service: The TodoService instance to use for task validation and storage.
        """
        self._todo_service = todo_service
        self._comments: dict[str, list[TaskComment]] = {}
        self._load()

    def _load(self) -> None:
        """Load comments from tasks in storage."""
        self._comments = {}
        for task in self._todo_service.list_tasks():
            self._comments[task.id] = []

    def _get_task_comments_from_storage(self, task_id: str) -> list[dict]:
        """Retrieve comments list from task data in storage.

        Args:
            task_id: The task ID to retrieve comments for.

        Returns:
            List of comment dicts, or empty list if none exist.
        """
        # Get the task from TodoService to validate it exists
        task = self._todo_service.get_task(task_id)
        # Access the underlying storage through TodoService's manager
        # Since we don't have direct access to task._comments, we work with the in-memory cache
        return []

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task.

        Args:
            task_id: The task ID to add the comment to.
            content: The comment content (must be non-empty).
            author: Optional author name.

        Returns:
            The created TaskComment instance.

        Raises:
            ValueError: If content is empty or whitespace-only.
            TaskNotFoundError: If the task doesn't exist.
        """
        # Validate task exists (also raises TaskNotFoundError if not found)
        self._todo_service.get_task(task_id)

        # Create the comment (TaskComment validates content in __post_init__)
        comment = TaskComment(task_id=task_id, content=content, author=author)

        # Add to in-memory cache
        if task_id not in self._comments:
            self._comments[task_id] = []
        self._comments[task_id].append(comment)

        return comment

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """List comments for a task, ordered by created_at ascending.

        Args:
            task_id: The task ID to list comments for.

        Returns:
            List of TaskComment instances ordered by created_at ascending.

        Raises:
            TaskNotFoundError: If the task doesn't exist.
        """
        # Validate task exists
        self._todo_service.get_task(task_id)

        # Get comments from cache, or return empty list if none
        comments = self._comments.get(task_id, [])

        # Sort by created_at ascending
        return sorted(comments, key=lambda c: c.created_at)

    def delete_comment(self, task_id: str, comment_id: str) -> None:
        """Delete a comment from a task.

        Args:
            task_id: The task ID.
            comment_id: The comment ID to delete.

        Raises:
            TaskNotFoundError: If the task doesn't exist.
        """
        # Validate task exists
        self._todo_service.get_task(task_id)

        # Remove comment from cache
        if task_id in self._comments:
            self._comments[task_id] = [
                c for c in self._comments[task_id] if c.id != comment_id
            ]

    def delete_comments_for_task(self, task_id: str) -> None:
        """Delete all comments for a task (cascade delete).

        Args:
            task_id: The task ID.

        Raises:
            TaskNotFoundError: If the task doesn't exist.
        """
        # Validate task exists
        self._todo_service.get_task(task_id)

        # Clear all comments for this task
        if task_id in self._comments:
            self._comments[task_id] = []
