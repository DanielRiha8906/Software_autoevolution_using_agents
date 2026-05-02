from datetime import datetime, timezone
from typing import Optional

from src.services.task_manager import TaskManager, TaskNotFoundError
from src.models.task_comment import TaskComment


class CommentNotFoundError(Exception):
    """Raised when a comment is not found."""
    pass


class CommentsService:
    """Service for managing task comments."""

    def __init__(self, manager: TaskManager) -> None:
        """
        Initialize CommentsService with a TaskManager.

        Args:
            manager: TaskManager instance for task operations.
        """
        self._manager = manager

    def add_comment(
        self,
        task_id: str,
        content: str,
        author: Optional[str] = None
    ) -> TaskComment:
        """
        Add a comment to a task.

        Args:
            task_id: ID of the task to add comment to.
            content: The comment content.
            author: Optional author name; defaults to None.

        Returns:
            The created TaskComment.

        Raises:
            TaskNotFoundError: If task doesn't exist.
            ValueError: If content is empty or whitespace-only.
        """
        task = self._manager.get(task_id)
        content = content.strip()
        if not content:
            raise ValueError("Comment content cannot be empty")
        comment = TaskComment(task_id=task.id, content=content, author=author)
        task.comments.append(comment)
        self._manager._persist()
        return comment

    def list_comments(self, task_id: str) -> list[TaskComment]:
        """
        List all comments for a task, sorted by creation time.

        Args:
            task_id: ID of the task.

        Returns:
            List of TaskComments sorted by created_at.

        Raises:
            TaskNotFoundError: If task doesn't exist.
        """
        task = self._manager.get(task_id)
        return sorted(task.comments, key=lambda c: c.created_at)

    def delete_comment(self, task_id: str, comment_id: str) -> None:
        """
        Delete a comment from a task.

        Args:
            task_id: ID of the task.
            comment_id: ID of the comment to delete.

        Raises:
            TaskNotFoundError: If task doesn't exist.
            CommentNotFoundError: If comment doesn't exist.
        """
        task = self._manager.get(task_id)
        comment_to_delete = None
        for comment in task.comments:
            if comment.id == comment_id:
                comment_to_delete = comment
                break
        if comment_to_delete is None:
            raise CommentNotFoundError(f"Comment {comment_id} not found")
        task.comments.remove(comment_to_delete)
        self._manager._persist()

    def edit_comment(
        self,
        task_id: str,
        comment_id: str,
        new_content: str
    ) -> TaskComment:
        """
        Edit an existing comment.

        Args:
            task_id: ID of the task.
            comment_id: ID of the comment to edit.
            new_content: The new comment content.

        Returns:
            The updated TaskComment.

        Raises:
            TaskNotFoundError: If task doesn't exist.
            CommentNotFoundError: If comment doesn't exist.
            ValueError: If new_content is empty or whitespace-only.
        """
        task = self._manager.get(task_id)
        comment_to_edit = None
        for comment in task.comments:
            if comment.id == comment_id:
                comment_to_edit = comment
                break
        if comment_to_edit is None:
            raise CommentNotFoundError(f"Comment {comment_id} not found")
        new_content = new_content.strip()
        if not new_content:
            raise ValueError("Comment content cannot be empty")
        comment_to_edit.content = new_content
        comment_to_edit.updated_at = datetime.now(timezone.utc)
        self._manager._persist()
        return comment_to_edit
