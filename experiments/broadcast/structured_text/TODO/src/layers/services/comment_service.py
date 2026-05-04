"""Comment domain service for comment-related use cases."""

from typing import Optional

from ..models import TaskComment
from ..repositories import JsonCommentRepository, CommentNotFoundError
from ..storage import JsonStorage


class CommentService:
    """Domain service for managing task comments."""

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._repository = JsonCommentRepository(storage or JsonStorage())

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task."""
        return self._repository.add_comment(task_id, content, author)

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """List comments for a task."""
        return self._repository.list_comments_by_task(task_id)

    def get_comment(self, comment_id: str) -> TaskComment:
        """Get a comment by ID."""
        return self._repository.get_comment(comment_id)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment."""
        self._repository.delete_comment(comment_id)

    def update_comment(self, comment_id: str, content: str) -> TaskComment:
        """Update a comment."""
        return self._repository.update_comment(comment_id, content)

    def delete_comments_by_task(self, task_id: str) -> None:
        """Delete all comments for a task."""
        self._repository.delete_comments_by_task(task_id)
