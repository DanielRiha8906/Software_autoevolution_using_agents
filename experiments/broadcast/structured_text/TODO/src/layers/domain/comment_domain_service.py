"""Domain service for comment-related operations.

This service encapsulates comment-specific business logic independent of storage.
"""

from typing import Optional

from ..models.task_comment import TaskComment
from .comment_repository import CommentRepository
from .task_repository import TaskRepository


class CommentDomainService:
    """Service encapsulating comment domain logic."""

    def __init__(self, comment_repository: CommentRepository, task_repository: TaskRepository) -> None:
        self._comment_repo = comment_repository
        self._task_repo = task_repository

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task.

        Validates that the task exists before adding the comment.
        """
        # Validate that task exists and get the full ID (in case a prefix was provided)
        task = self._task_repo.get(task_id)
        return self._comment_repo.add_comment(task.id, content, author)

    def get_comment(self, comment_id: str) -> TaskComment:
        """Get a comment by ID."""
        return self._comment_repo.get_comment(comment_id)

    def list_comments_for_task(self, task_id: str) -> list[TaskComment]:
        """List all comments for a task, ordered by created_at.

        Validates that the task exists.
        """
        # Validate that task exists and get the full ID (in case a prefix was provided)
        task = self._task_repo.get(task_id)
        return self._comment_repo.list_comments_by_task(task.id)

    def update_comment(self, comment_id: str, content: str) -> TaskComment:
        """Update a comment's content."""
        return self._comment_repo.update_comment(comment_id, content)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment."""
        self._comment_repo.delete_comment(comment_id)

    def delete_comments_for_task(self, task_id: str) -> None:
        """Delete all comments for a task (cascade delete)."""
        self._comment_repo.delete_comments_by_task(task_id)
